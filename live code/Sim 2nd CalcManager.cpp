#include "CalcManager.h"
#include "PilotSvrManager.h"
#include <fasteyelib/Compare.h>
#include <fasteyelib/ConfigParams.h>
#include <fasteyelib/TradingControl.h>
#include <commonsvr/OrderTicket.h>
#include <commonsvr/Exchange.h>
#include <commonsvr/ETradeManager.h>
#include <commonsvr/ExchangeSpecs.h>
#include <chrono>
#include <thread>

using namespace pilotsvr;
using namespace exchange;
    
CalcManager::CalcManager(const FastEye::tpos::SecurityInfo * sec,
						 const FastEye::tpos::Account * acct, const ctrSpec::TickSize tickSz,
						 const ctrSpec::Quantity TicksChange, exchange::ETradeManager * OrderManager,
						 FastEye::thread::EventQueue & calcThread)
: commonsvr::CalcManager(sec, acct, tickSz)
, commonsvr::SmartTrader(OrderManager->GetExchange(*sec))
, m_TicksChange(TicksChange*tickSz)
, m_LastOrderPx(0)
, m_EtMgr(OrderManager)
, m_CalcEventQueue(calcThread)
, m_advOrderPriceNotifier(new commonsvr::SubjectImplT(this))
{
    auto fn = [&]()
    {
        auto &si = GetSecInfo(); 
        auto pExch = m_EtMgr->GetExchange(si);
        if (!pExch)
        {
            std::cerr << "Exchange still not found for " << GetSymbol() << "\n";
            return;
        }
        SetExchange(pExch);
        FastEye::tpos::SecurityInfo::ExchangeConversions conv;
        pExch->GetProductConversionFactorAndCode(si, conv);
        m_InstrGroupCode = conv.instrumentGroupCode;
        m_ConversionFactor = conv.conversionFactor;
        static_cast<PilotSvrManager &>(m_EtMgr->GetServerManager()).AddIntrumentCodeToExchangeEntry(m_InstrGroupCode,
                                                                                                    si.GetBaseSecInfo()->GetFullSymbol(),
                                                                                                    pExch);

        // This allows additional data within the smart trader to be set based on
        // exchange and instrument.
        SetExchangeAdditionalData(m_EtMgr->GetServerManager(), GetSecInfo());
    };

    if (m_EtMgr->GetConfigParams().svrOperation.ShouldConnectToExch)
    {
    	if (GetExchange())
    	{
    		fn();
    	}
    	else
    	{
    		m_EtMgr->ExchangePending(&GetSecInfo(), fn);
    		std::ostringstream oss;
    		oss << "Error: This CalcMgr does not have an exchange associated with it "
    				"YET.  Symbol=" << GetSymbol() << " ProductCode=" << GetSecInfo().GetProductCode() << std::endl;
    		m_EtMgr->OnNotify(oss.str(), false, false);
    	}
    }
	else
	{
		m_RivalGatewaySimPtr = &(static_cast<PilotSvrManager &>(m_EtMgr->GetServerManager()).GetRivalHandler());
	}
	m_RivalGatewaySimPtr->positionPandL();
	//m_RivalGatewaySimPtr->Heartbeat();
}

CalcManager::~CalcManager()
{
	delete m_advOrderPriceNotifier;
}

commonsvr::CalcMgrSubjectPtr CalcManager::GetSubject()
{
	return m_advOrderPriceNotifier;
}

std::string MyUserData(const exchange::ExchRecvData & exchData)
{
    UNUSED(exchData);
	return "USER;DATA";
}


/*
 * You would typically handle handle all of your
 * strategy logic inside this place. This strategy
 * here serves as an example only. It computes the
 * mid market price, and shoots an order for the same.
 */

///////////////////////////
bool CalcManager::tradingStatusOnOff = false;
std::string CalcManager::tradingStatusMsg = "nullstring";
std::string CalcManager::HighLow = "nullstring";
int CalcManager::connectVar = 0;

void CalcManager::SetHighLowIndividually(std::string HighLowNew)
{
	HighLow = HighLowNew;
}


void CalcManager::ChangeTradingStatus(bool tradingStatusNew)
{
    tradingStatusOnOff = tradingStatusNew;
}


void CalcManager::ChangeTradingStatusIndividually(std::string tradingStatusmsg)
{
	tradingStatusMsg = tradingStatusmsg;
}

void CalcManager::TradingStatusVariables()
{
	std::string input = CalcManager::tradingStatusMsg;
	std::stringstream ss(input);
    std::string token;
	

    // Fetch value after the first comma
    std::getline(ss, token, ','); // Skip the first value
    std::getline(ss, token, ',');
	if(token == GetSymbol())
	{
		std::getline(ss, token, ',');
		if(token == "on")
		{
			tradingStatusOnOffInd = true;
			settlementFlag = true;
			std::cout << "Trading Status Turn On For : " << GetSymbol() << std::endl;
		}
		else if(token == "off")
		{
			std::getline(ss, token, ',');
			tradingStatusOnOffInd = false;
			if(token == "1")
			{
				closePosition = 1;
				std::cout << "Trading Status Turn Off (Holding Positions) For : " << GetSymbol() << std::endl;
			}
			else if(token == "0")
			{
				closePosition = 0;
				std::cout << "Trading Status Turn Off (Not Holding Positions) For : " << GetSymbol() << std::endl;
				bullFirstTrigg = false;
	            bearFirstTrigg = false;
			}
		}
		else
		{
			std::cout << "Invalid String" << std::endl;
		}
		CalcManager::tradingStatusMsg[0] = 't';
	}
}

bool CalcManager::TradingTimings( std::string Symbol ) 
{
    if(CalcManager::tradingStatusMsg[0] == 'T')
	{
		TradingStatusVariables();
	}

	if(tradingStatusOnOffInd == false) 
	{
		if(closePosition == 1)
		{
			return false;
		}
		longEntry1 = true;
		CancelExistingLiveOrders(5);
		if(myPosition > 0 && settle)
		{
			numSell++;
			SendNewOrder(m_BidAskData.bid - 10*tickSizeNew,exchange::rom::Sell, myPosition, 5, 2);
		}
		if(myPosition < 0 && settle)
		{
			numBuy++;
			SendNewOrder(m_BidAskData.ask + 10*tickSizeNew,exchange::rom::Buy, (-1*myPosition), 5,2);
		}
		settle = false;
		return false;
	}
	if(tradingStatusOnOffInd == true)
	{
		settle = true;
	}
	
	using namespace exchange;

    int start_hour = 8;
	int start_min = 00;
	int end_hour = 20;
	int end_min = 00;

	if((Symbol == "MESZ4") || (Symbol == "MNQZ4") || (Symbol == "MYMZ4") || (Symbol == "MBTZ4"))       //  || (Symbol == "YMZ3")
	{
		start_hour = 8;   //1:30pm
		start_min = 00;
		end_hour = 19;    //1:15am
		end_min = 45;
	}

	if((Symbol == "MCLX4"))
	{
		start_hour = 00;   // 5:30am
		start_min = 00;
		end_hour = 19;    // 12:30am
		end_min = 00;
	}

	if(Symbol == "MGCG5")
	{
		start_hour = 8;  // 1:30PM
		start_min = 00;
		end_hour = 17;  // 11:00PM
		end_min = 30;
	}



	std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now();         // Get the current time point in UTC
	std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);               // Convert the time point to a time_t object
	std::tm* tm_struct = std::gmtime(&current_time_t);    // Convert the time to the local time in London
	std::string current_Time = std::asctime(tm_struct);   // Convert the tm struct to a string representation



    int current_hour = tm_struct->tm_hour;
    int current_minute = tm_struct->tm_min;

    if(( (current_hour > start_hour) || (current_hour == start_hour && current_minute >= start_min)) && ( (current_hour < end_hour) || (current_hour == end_hour && current_minute < end_min)) )
	{
		return true;
    } 
	else 
    {
        return false;
    }
}


void CalcManager::OnPandLvaluesFromSim(double & CurPosition)
{
	position = CurPosition;
	//std::cout << " OnPandLvalues      Position " << position << "   MyPosition " << myPosition << current_Time;
}

void CalcManager::CancelExistingLiveOrders(int slot)
{

	try
	{
		if(slot == 5)
		{
			for(auto itr = m_OrderDetailMap.begin(); itr != m_OrderDetailMap.end(); ++itr) 
			{
				if((m_OrderDetailMap.find(itr->first) != m_OrderDetailMap.end())) 
				{
					if(itr->second.first == 1) 
					{
						m_RivalGatewaySimPtr->ConstructAndSendCancelToSim(itr->second.second);
						itr->second.first = 11;
					}
				}
			}
		}
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::CancelExistingLiveOrders(): " << e.what() << std::endl;
	}

}

void CalcManager::SendNewOrder(ctrSpec::Price shootPrice, exchange::rom::Side buySell, int quantity, int slot, int orderTypeLimitMarket)
{
	try
	{
        if(numTrade > 50)
		{
			std::cout << "Number of Trades is greater then 50" << std::endl;
			return ;
		}

		if(quantity < 1) return ;
		if(quantity > 100) return ;
		
        if(orderTypeLimitMarket == 1)
		{
			if(OrderTicketPtr newTkt = OrderTicket::CreateOrderTicket(m_EtMgr->GetConfigParams(), GetExchange()))
			{
				newTkt->SetSeqNum(m_BidAskData.seqnoTimestamps.seqno);

				newTkt->SetOrderNew( this,
										GetSecInfo(),   // TPOS Security info
										GetAccount(),   // TPOS account info
										m_BidAskData,   // Mkt data
										0,              // Theo
										shootPrice,     // Price to shoot at
										quantity,
										buySell,
										rom::LIMIT,
										rom::Day,
										rom::ElectronicEye,
										m_InstrGroupCode,
										m_ConversionFactor );

				m_RivalGatewaySimPtr->ConstructAndSendNewOrderToSim(newTkt);
				if(slot == 5) m_OrderDetailMap.insert(std::make_pair(newTkt->GetClOrderID(),std::make_pair((int)0,newTkt)));
				
				prevOrder = std::to_string(newTkt->GetTicketOrdID());

				string BuySell;
				if(buySell == exchange::rom::Buy)
				{
					BuySell = "Buy";
				}
				else 
				{
					BuySell = "Sell";
				}


				std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
				std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
				std::tm* tm_struct = std::gmtime(&current_time_t);   
				std::string current_Time = std::asctime(tm_struct);

				std::cout << GetSymbol() << " " << newTkt->GetTicketOrdID() << " shootPrice: " << shootPrice << " LastTradedPrice: " << lastTradedPrice << "  Best Ask: "<< m_BidAskData.ask << "  Best Bid: " << m_BidAskData.bid << " " << "Current time: " << current_Time << std::endl;	
			}
		}
		else
		{
			if(OrderTicketPtr newTkt = OrderTicket::CreateOrderTicket(m_EtMgr->GetConfigParams(), GetExchange()))
			{
				newTkt->SetSeqNum(m_BidAskData.seqnoTimestamps.seqno);

				newTkt->SetOrderNew( this,
										GetSecInfo(),   // TPOS Security info
										GetAccount(),   // TPOS account info
										m_BidAskData,   // Mkt data
										0,              // Theo
										shootPrice,     // Price to shoot at
										quantity,
										buySell,
										rom::MARKET,
										rom::Day,
										rom::ElectronicEye,
										m_InstrGroupCode,
										m_ConversionFactor );

				m_RivalGatewaySimPtr->ConstructAndSendNewOrderToSim(newTkt);
				if(slot == 5) m_OrderDetailMap.insert(std::make_pair(newTkt->GetClOrderID(),std::make_pair((int)0,newTkt)));
				
				prevOrder = std::to_string(newTkt->GetTicketOrdID());

				string BuySell;
				if(buySell == exchange::rom::Buy)
				{
					BuySell = "Buy";
				}
				else 
				{
					BuySell = "Sell";
				}


				std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
				std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
				std::tm* tm_struct = std::gmtime(&current_time_t);   
				std::string current_Time = std::asctime(tm_struct);

				std::cout << GetSymbol() << " " << newTkt->GetTicketOrdID() << " shootPrice: " << shootPrice << " LastTradedPrice: " << lastTradedPrice << "  Best Ask: "<< m_BidAskData.ask << "  Best Bid: " << m_BidAskData.bid << " " << "Current time: " << current_Time << std::endl;	
			}
		}


	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::SendNewOrder: " << e.what() << std::endl;
	}
	
}

int CalcManager::calRisk1()
{
	try
	{
		
	}
	catch(const std::exception& e)
	{
		std::cerr <<  "Exception caught in CalcManager::SendNewOrder: " << e.what() << '\n';
		return 1;
	}
	
}

int CalcManager::calRisk2()
{
	try
	{

	}
	catch(const std::exception& e)
	{
		std::cerr <<  "Exception caught in CalcManager::SendNewOrder: " << e.what() << '\n';
		return 1;
	}
	
}



bool CalcManager::bullish(int slot)
{
    // Long
	try
	{
		std::chrono::system_clock::time_point current_time = std::chrono::system_clock::now();
		std::time_t current_tm = std::chrono::system_clock::to_time_t(current_time);
		auto tm_struct = std::localtime(&current_tm);
		std::string current_Time = std::ctime(&current_tm);

		if(slot == 5)
		{
			bool condition1 = false;
            if((close1 > open1) && (close12 > open12) && (close13 < open13) && (close14 > open14) && (close15 < open15)) condition1 = true;

			bool condition2 = false;
			if(max(high12, max(high13, max(high14, high15))) < high1) condition2 = true;

			if(condition1 && condition2 && longEntry1)
			{
			    numLot = 1;
				
				entryPrice = close1;
				stop1 = min(low1, min(low12, min(low13, min(low14, low15))));
				targetRange = high1-stop1;
				targetRange1 = high1-stop1;
				profPrice = close1 + targetRange;
				std::cout << "5min Long Entry   EntryPrice:" << entryPrice << "  TargetRange:" << targetRange << " profPrice:" << profPrice << std::endl;
				SendNewOrder(entryPrice + 10*tickSizeNew,exchange::rom::Buy, numLot, 5, 2);
				longEntry1 = false;
			}
		}
		return false;
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::bullish(): " << e.what() << std::endl;
		return false;
	}
	
}

bool CalcManager::exitbullishposition()
{
	try
	{
		
		if(myPosition != 0 && lastTradedPrice < stop1 && longExit1)
		{
			longExit1 = false;
			CancelExistingLiveOrders(5);
			SendNewOrder(stop1 - 10*tickSizeNew,exchange::rom::Sell, abs(myPosition), 5, 2);
			stop1 = INT16_MIN;
		}

		return false;
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::exitbullishposition(): " << e.what() << std::endl;
		return false;
	}
	
}

bool CalcManager::bearish(int slot)
{
	// Short
	try
	{
		return false;
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::bearish(): " << e.what() << std::endl;
		return false;
	}
		
}

bool CalcManager::exitbearishposition()
{
	try
	{
		return false;
		
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::exitbearishposition(): " << e.what() << std::endl;
		return false;
	}
}


void CalcManager::TradeSettlement()
{
	try
	{
		//Current Time
		std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
		std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
		std::tm* tm_struct = std::gmtime(&current_time_t);   

		// Trade Settlement (1:30AM)
		int current_hour = tm_struct->tm_hour;
		int current_minute = tm_struct->tm_min;

		if((settlementFlag == true) && (myPosition!=0) && (current_hour == 20 && current_minute >= 00))
		{
			CancelExistingLiveOrders(5);
			settlementFlag = false;
			if(myPosition > 0)
			{
				numSell++;
				SendNewOrder(m_BidAskData.bid - 10*tickSizeNew,exchange::rom::Sell, myPosition, 5, 2);
	
			}
			if(myPosition < 0)
			{
				numBuy++;
				SendNewOrder(m_BidAskData.ask + 10*tickSizeNew,exchange::rom::Buy, (-1*myPosition), 5, 2);
			}
		}

		if((settlementFlag == true) && (GetSymbol() == "MGCG5") && (myPosition!=0) && (current_hour == 18 && current_minute >= 00))
		{
			CancelExistingLiveOrders(5);
			settlementFlag = false;
			if(myPosition > 0)
			{
				numSell++;
				SendNewOrder(m_BidAskData.bid - 10*tickSizeNew,exchange::rom::Sell, myPosition, 5, 2);
	
			}
			if(myPosition < 0)
			{
				numBuy++;
				SendNewOrder(m_BidAskData.ask + 10*tickSizeNew,exchange::rom::Buy, (-1*myPosition), 5, 2);
			}
		}
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::TradeSettlement(): " << e.what() << std::endl;
	}
}

void CalcManager::OnBestPriceUpdate()
{
	try
	{
		GetSubject()->NotifyAllObservers(commonsvr::CalcManagerChanged(commonsvr::PRICE_UPDATE, 0, GetTopOfBook().seqnoTimestamps.seqno));
		using namespace exchange;

		// Count Garbage Value (When bid or ask is equal to zero).
		if((m_BidAskData.ask == 0) || (m_BidAskData.bid == 0))
		{
			// std::cout <<" Symbol=" << GetSymbol() << " Garbage Value  " << std::endl; //std::cout << "Current time: " << current_Time; // std::cout << " current_high1 : " << curr_high1 << "  current_low1 : " << curr_low1 << "  previous_high1 : " << prev_high1 << "  previous_low1 : " << prev_low1 << std::endl; // std::cout << " high1 : " << high1 << "  low1 : " << low1 << std::endl; 
			return ;
		}

	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::OnBestPriceUpdate(): " << e.what() << std::endl;
	}
	
}

void CalcManager::OnLastPriceUpdate()
{
	//std::cout << "OnLastPriceUpdate" << std::endl;
	// Handle your onTrade arrival logic here..

	try
	{
		lastTradedPrice =  m_LastPxQty.m_Price;	

		// Count Garbage Value (When bid or ask is equal to zero).
		if((m_BidAskData.ask == 0) || (m_BidAskData.bid == 0)  || (lastTradedPrice == 0))
		{
			// std::cout <<" Symbol=" << GetSymbol() << " Garbage Value  " << std::endl; //std::cout << "Current time: " << current_Time; // std::cout << " current_high1 : " << curr_high1 << "  current_low1 : " << curr_low1 << "  previous_high1 : " << prev_high1 << "  previous_low1 : " << prev_low1 << std::endl; // std::cout << " high1 : " << high1 << "  low1 : " << low1 << std::endl; 
			return ;
		}

		//Logic for formation of Candles
		CalcManager::TradingTimings(GetSymbol());
		FormCandle();
		if((CalcManager::connectVar == 1))
		{
			// Algorithm For Buy Exit
			exitbullishposition();
		}
        TradeSettlement();
	}
	catch(const std::exception& e)
	{
		std::cerr << "Exception caught in CalcManager::OnLastPriceUpdate(): " << e.what() << '\n';
	}
	
}

void CalcManager::OnTradingStatus(const std::string &source,const long tradingStatus)
{
	std::cout << "OnTradingStatus" << std::endl;
}


void CalcManager::OnOrderSubmittedFromSim(exchange::rom::ROMStatusMsg& msg)
{
	std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
	std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
	std::tm* tm_struct = std::gmtime(&current_time_t);   
	std::string current_Time = std::asctime(tm_struct);

	std::cout << msg.getTag()  <<"  OnOrderSubmitted  " << current_Time << std::endl;
	std::string msgTag = msg.getTag(); 
    std::string subTag = msgTag.substr(17);

	try
	{
		auto itr  =  m_OrderDetailMap.find(subTag);
		if( itr != m_OrderDetailMap.end())
		{
			itr->second.first = 1;
		}
		else
		{
			std::cout << "Order from OnOrderSubmitted " << msg.getTag() << " not found" << std::endl;
		}
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::OnOrderSubmitted: " << e.what() << std::endl;
	}
	

}


void CalcManager::OnOrderCanceledFromSim(exchange::rom::ROMStatusMsg& msg)
{
	try
	{
		std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
		std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
		std::tm* tm_struct = std::gmtime(&current_time_t);   
		std::string current_Time = std::asctime(tm_struct);

		std::cout << msg.getTag() << "  OnOrderCanceled" << current_Time << std::endl;


        std::string msgTag = msg.getTag(); 
        std::string subTag = msgTag.substr(17);
		auto itr  =  m_OrderDetailMap.find(subTag);
		if( itr != m_OrderDetailMap.end())
		{
			itr->second.first = 3;
		}
		else
		{
			std::cout << "Order from OnOrderCanceled " << msg.getTag() << " not found" << std::endl; 
		}
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::OnOrderCanceled: " << e.what() << std::endl;
	}
	
}


void CalcManager::OnOrderRejectedFromSim(exchange::rom::ROMStatusMsg& msg)
{
	std::cout << msg.getTag() << "  OnOrderRejected        " << msg.GetRomMsg() << std::endl ;

    try
	{
		std::string msgTag = msg.getTag(); 
        std::string subTag = msgTag.substr(17);
		
		auto itr  =  m_OrderDetailMap.find(subTag);
		if( itr != m_OrderDetailMap.end())
		{
			itr->second.first = 4;
		}
		else
		{
			std::cout << "Order from OnOrderRejected " << msg.getTag() << " not found" << std::endl; 
		}
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::OnOrderRejected: " << e.what() << std::endl;
	}
	
	
}

void CalcManager::OnOrderFilledFromSim(exchange::rom::ROMStatusMsg& msg)
{
	try
	{
		std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
		std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
		std::tm* tm_struct = std::gmtime(&current_time_t);   
		std::string current_Time = std::asctime(tm_struct);

		if(msg.getSide() == 1)   myPosition = myPosition + std::stoi(msg.getLastShares());  
		else myPosition = myPosition - std::stoi(msg.getLastShares());

		std::cout << msg.getSymbol()  << " Order Filled: 5min : " << " Prize " << msg.getExecPrice() << "  QuantityFilled : " << msg.getLastShares() << "  " << current_Time << std::endl;
		
		if(myPosition == 0)
		{
			longEntry1 = true;
			longExit1 = true;
			CancelExistingLiveOrders(5);
		}
		if(myPosition == numLot)
		{
			SendNewOrder(profPrice,exchange::rom::Sell, abs(myPosition), 5, 1);
		}

		std::string msgTag = msg.getTag(); 
        std::string subTag = msgTag.substr(17);
		auto itr  =  m_OrderDetailMap.find(subTag);
		if( itr != m_OrderDetailMap.end())
		{
			int status = msg.getStatus();
			if(status == 2)
			{
				itr->second.first = 2;
			}
		}
		else
		{
			std::cout << "Order from OnOrderFilled " << msg.getTag() << " not found" << std::endl; 
		}

	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::OnOrderFilled: " << e.what() << std::endl;
	}
	

}

void CalcManager::OnOrderReplaceRejectFromSim(exchange::rom::ROMStatusMsg& msg)
{
	std::string msgTag = msg.getTag(); 
    std::string subTag = msgTag.substr(17);
    auto itr  =  m_OrderDetailMap.find(subTag);
	if( itr != m_OrderDetailMap.end())
	{
		itr->second.first = 4;
	}
	else
	{
		std::cout << "Order from OnOrderReplaceReject " << msg.getTag() << " not found" << std::endl; 
	}
}

void CalcManager::OnOrderCancelRejectFromSim(exchange::rom::ROMStatusMsg& msg)
{
	std::string msgTag = msg.getTag(); 
    std::string subTag = msgTag.substr(17);
    auto itr  =  m_OrderDetailMap.find(subTag);
	if( itr != m_OrderDetailMap.end())
	{
		itr->second.first = 4;
	}
	else
	{
		std::cout << "Order from OnOrderCancelReject " << msg.getTag() << " not found" << std::endl; 
	}
}

void CalcManager::OnOrderReplacedFromSim(exchange::rom::ROMStatusMsg& msg)
{
	std::string msgTag = msg.getTag(); 
    std::string subTag = msgTag.substr(17);
	auto itr  =  m_OrderDetailMap.find(subTag);
	if( itr != m_OrderDetailMap.end())
	{
		itr->second.first = 4;
	}
	else
	{
		std::cout << "Order from OnOrderReplaced " << msg.getTag() << " not found" << std::endl; 
	}
}






void CalcManager::FormCandle()
{
	try
	{
		std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
		std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
		std::tm* tm_struct = std::gmtime(&current_time_t);   
		std::string current_Time = std::asctime(tm_struct);


		// Count Garbage Value (When bid or ask is equal to zero).
		if((m_BidAskData.ask == 0) || (m_BidAskData.bid == 0)  || (lastTradedPrice == 0))
		{
			// std::cout <<" Symbol=" << GetSymbol() << " Garbage Value  " << std::endl; //std::cout << "Current time: " << current_Time; // std::cout << " current_high1 : " << curr_high1 << "  current_low1 : " << curr_low1 << "  previous_high1 : " << prev_high1 << "  previous_low1 : " << prev_low1 << std::endl; // std::cout << " high1 : " << high1 << "  low1 : " << low1 << std::endl; 
			return ;
		}

		// Calculate Curr High and Low, Local High Low from FQE Port;
		std::string input = CalcManager::HighLow;

		// Find the position of the first comma
		size_t firstCommaPos = input.find(',');

		// Find the position of the second comma
		size_t secondCommaPos = input.find(',', firstCommaPos + 1);

         // Extract the substring between the first and second comma
		std::string resultSymbol = input.substr(firstCommaPos + 1, secondCommaPos - firstCommaPos - 1);

        if((CalcManager::HighLow[0] == 'c' || CalcManager::HighLow[0] == 'C' || CalcManager::HighLow[0] == 'E') && (resultSymbol == GetSymbol()))
		{
			if(HighLow[0] == 'c')  CalcManager::HighLow[0] = 'd';
		    if(HighLow[0] == 'C')  CalcManager::HighLow[0] = 'D';
			if(HighLow[0] == 'E')  CalcManager::HighLow[0] = 'F';
		
			ResetHighLowValues(); 
		}

		// update high, low1 for first feed.
		if(firstFeed == true)
		{
			firstFeed = false;
			if(high1 == 0) high1 = lastTradedPrice;
		    if(low1 == 0) low1 = lastTradedPrice;
			if(open1 == 0) high1 = lastTradedPrice;
		    if(close1 == 0) low1 = lastTradedPrice;

			if(GetSymbol() == "MESZ4")
			{
				priceVal = 5;
				tickSizeNew = 0.25;
			}
			else if(GetSymbol() == "MYMZ4")
			{
				priceVal = 0.5;
				tickSizeNew = 1;
			}
			else if(GetSymbol() == "MNQZ4") 
			{
				priceVal = 2;
				tickSizeNew = 0.25;
			}
			else if(GetSymbol() == "MCLX4") 
			{
				priceVal = 100;
				tickSizeNew = 0.01;
			}
			else if(GetSymbol() == "MBTZ4") 
			{
				priceVal = 0.1;
				tickSizeNew = 5;
			}
			else if(GetSymbol() == "MGCG5") 
			{
				priceVal = 10;
				tickSizeNew = 0.1;
			}
			if(GetSymbol() == "ESZ4")
			{
				priceVal = 50;
				tickSizeNew = 0.25;
			}
			else if(GetSymbol() == "YMZ4")
			{
				priceVal = 5;
				tickSizeNew = 1;
			}
			else if(GetSymbol() == "NQZ4") 
			{
				priceVal = 20;
				tickSizeNew = 0.25;
			}
			else if(GetSymbol() == "CLV4") 
			{
				priceVal = 1000;
				tickSizeNew = 0.01;
			}
			else if(GetSymbol() == "GCG5") 
			{
				priceVal = 1000;
				tickSizeNew = 0.1;
			}
			else if(GetSymbol() == "SIH5") 
			{
				priceVal = 100;
				tickSizeNew = 0.005;
			}
			else if(GetSymbol() == "HGH5") 
			{
				priceVal = 100;
				tickSizeNew = 0.0005;
			}


			//SendNewOrder(m_BidAskData.ask + 20*tickSizeNew,exchange::rom::Sell, 1, 2);
		}

		// 5min Logic for calculate high, low.
		if((tm_struct->tm_min%5 == 0) && flag1 == true)
		{
			ATP13 = ATP12;
			ATP12 = ATP11;
			ATP11 = (avgSumPrice)/(tradeVol);
			tradeVol = 0;
		    avgSumPrice = 0;
			std::cout << GetSymbol() << " " << current_Time << " 5min Open:" << open1 << " Low" << low1 << " close " << close1 << " High" << high1 << " ATP1 " << ATP11 << " ATP2 " << ATP12 << " ATP3 " << ATP13 << std::endl << std::endl;
			if((CalcManager::connectVar == 1) && (tradingStatusOnOffInd == true))
			{
				// Algorithm For Buy and Sell
				if(CalcManager::TradingTimings(GetSymbol()) && (numTrade <= 50))                                                      // We are using flagTimer2 (Algo start after formation 2nd candle && between 2:30pm-2:30am)
				{
					bullish(5);
				}
			}
			open15 = open14;
			open14 = open13;
			open13 = open12;
			open12 = open1;
			open1 = lastTradedPrice;
            
			high15 = high14;
			high14 = high13;
			high13 = high12;
			high12 = high1;
			high1 = lastTradedPrice;
            
			low15 = low14;
			low14 = low13;
			low13 = low12;
            low12 = low1;
			low1 = lastTradedPrice;
			flag1 = false;

            close15 = close14;
			close14 = close13;
		    close13 = close12;
		    close12 = close1;
		
		}
		if(tm_struct->tm_min%5 == 1)
		{ 
			flag1 = true;
		}
		if(lastTradedPrice > high1) high1 = lastTradedPrice;
		if(lastTradedPrice < low1) low1 = lastTradedPrice;
		
		close1 = lastTradedPrice;

		tradeVol += m_LastPxQty.m_Qty;
        avgSumPrice += (m_LastPxQty.m_Price)*(m_LastPxQty.m_Qty);



		
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::FormCandle(): " << e.what() << std::endl;
	}
 
}

void CalcManager::ResetHighLowValues()
{ 
	
}


