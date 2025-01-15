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
			std::cout << "Trading Status Turn On For : " << GetSymbol() << std::endl;
			settlementFlag = true;
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
		if(myPosition > 0 && settle)
		{
			numSell++;
			SendNewOrder(m_BidAskData.bid - 10*tickSizeNew,exchange::rom::Sell, myPosition);
		}
		if(myPosition < 0 && settle)
		{
			numBuy++;
			SendNewOrder(m_BidAskData.ask + 10*tickSizeNew,exchange::rom::Buy, (-1*myPosition));
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

	if((Symbol == "MESZ4") || (Symbol == "MNQZ4") || (Symbol == "MYMZ4") || (Symbol == "MGCG5") || (Symbol == "MBTZ4"))       //  || (Symbol == "YMZ3")
	{
		start_hour = 12;   //5:30pm
		start_min = 00;
		end_hour = 20;    //1:30am
		end_min = 00;
	}

	if((Symbol == "MCLF5"))
	{
		start_hour = 12;   // 5:30pm
		start_min = 00;
		end_hour = 19;    // 12:30am
		end_min = 00;
	}

	if(Symbol == "GCJ4")
	{
		start_hour = 8; //01:30pm
		start_min = 00;
		end_hour = 16; // 09:30am
		end_min = 00;
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

void CalcManager::CancelExistingLiveOrders()
{

	try
	{
		auto itr = m_OrderDetailMap.find(prevOrder);
		if(itr != m_OrderDetailMap.end()) 
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
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::CancelExistingLiveOrders(): " << e.what() << std::endl;
	}

}

void CalcManager::SendNewOrder(ctrSpec::Price shootPrice, exchange::rom::Side buySell, int quantity)
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
			m_OrderDetailMap.insert(std::make_pair(newTkt->GetClOrderID(),std::make_pair((int)0,newTkt)));
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
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::SendNewOrder: " << e.what() << std::endl;
	}
	
}

int CalcManager::calRisk1()
{
	try
	{
		if(local_high1 == INT_MAX || local_low1 == INT_MIN) return 1;
		
		double diff = 0;
		diff = m_BidAskData.ask - curr_low1;

		double LotPrice = (diff)*(priceVal) ;   // 50 = 12.5%0.25
        int maxLoss = static_cast<int>(std::ceil(LotPrice));

		if(maxLoss > 225) return 1;
		if(maxLoss == 0) return 0;

        int riskQuant = static_cast<int>(round(225/LotPrice));
		
        if(riskQuant > 20)
		{
			riskQuant = 20;
		} 
		if(riskQuant > 12 && GetSymbol() == "MGCG5")
		{
			riskQuant = 12;
		}
		if(riskQuant > 15 && GetSymbol() == "MBTZ4")
		{
			riskQuant = 15;
		}
		
		if(riskQuant < 1) riskQuant = 1;

		return riskQuant;


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
		if(local_high1 == INT_MAX || local_low1 == INT_MIN) return 1;

		double diff = 0;
		diff = curr_high1 - m_BidAskData.bid;

		double LotPrice = (diff)*(priceVal) ;   // 50 = 12.5%0.25
        int maxLoss = static_cast<int>(std::ceil(LotPrice));

		if(maxLoss > 225) return 1;
		if(maxLoss == 0) return 0;

        int riskQuant = static_cast<int>(round(225/LotPrice));

        if(riskQuant > 20)
		{
			riskQuant = 20;
		} 
		if(riskQuant > 12 && GetSymbol() == "MGCG5")
		{
			riskQuant = 12;
		}
		if(riskQuant > 15 && GetSymbol() == "MBTZ4")
		{
			riskQuant = 15;
		}
		
		if(riskQuant < 1) riskQuant = 1;


		return riskQuant;


	}
	catch(const std::exception& e)
	{
		std::cerr <<  "Exception caught in CalcManager::SendNewOrder: " << e.what() << '\n';
		return 1;
	}
	
}


int CalcManager::calRisk12()
{
	try
	{
		if(local_high1 == INT_MAX || local_low1 == INT_MIN) return 1;
		
		double diff = 0;
		diff = prevBuyOrderPrice - curr_low1;

		double LotPrice = (diff)*(priceVal) ;   // 50 = 12.5%0.25
        int maxLoss = static_cast<int>(std::ceil(LotPrice));

		if(maxLoss > 225) return 1;
		if(maxLoss == 0) return 0;

        int riskQuant = static_cast<int>(round(225/LotPrice));
		
        if(riskQuant > 20)
		{
			riskQuant = 20;
		} 
		if(riskQuant > 12 && GetSymbol() == "MGCG5")
		{
			riskQuant = 12;
		}
		if(riskQuant > 15 && GetSymbol() == "MBTZ4")
		{
			riskQuant = 15;
		}
		
		if(riskQuant < 1) riskQuant = 1;

		return riskQuant;


	}
	catch(const std::exception& e)
	{
		std::cerr <<  "Exception caught in CalcManager::SendNewOrder: " << e.what() << '\n';
		return 1;
	}
	
}

int CalcManager::calRisk22()
{
	try
	{
		if(local_high1 == INT_MAX || local_low1 == INT_MIN) return 1;

		double diff = 0;
		diff = curr_high1 - prevSellOrderPrice;

		double LotPrice = (diff)*(priceVal) ;   // 50 = 12.5%0.25
        int maxLoss = static_cast<int>(std::ceil(LotPrice));

		if(maxLoss > 225) return 1;
		if(maxLoss == 0) return 0;

        int riskQuant = static_cast<int>(round(225/LotPrice));

        if(riskQuant > 20)
		{
			riskQuant = 20;
		} 
		if(riskQuant > 12 && GetSymbol() == "MGCG5")
		{
			riskQuant = 12;
		}
		if(riskQuant > 15 && GetSymbol() == "MBTZ4")
		{
			riskQuant = 15;
		}
		
		if(riskQuant < 1) riskQuant = 1;


		return riskQuant;


	}
	catch(const std::exception& e)
	{
		std::cerr <<  "Exception caught in CalcManager::SendNewOrder: " << e.what() << '\n';
		return 1;
	}
	
}

void CalcManager::exitExtraLots()
{
	if((myPosition > 0) && (LongOrderExitPrice > curr_low1))
	{
		// Long -> exit Extra Lots
		int newriskQuantity = calRisk12();
		int remlots = myPosition - newriskQuantity;
		if(myPosition > newriskQuantity && (myPosition > remlots))
		{
			LongOrderExitPrice = curr_low1;
			std::cout << "Exit Extra Lots = " << remlots << std::endl;
			SendNewOrder(m_BidAskData.bid - (10*tickSizeNew),exchange::rom::Sell, remlots);
		}
		
	}
	if((myPosition < 0) && (ShortOrderExitPrice < curr_high1))
	{
		// Short -> exit Extra Lots
        int newriskQuantity = calRisk22();
		int remlots = abs(myPosition) - newriskQuantity;
		if(abs(myPosition) > newriskQuantity && (abs(myPosition) > remlots))
		{
			ShortOrderExitPrice = curr_high1;
			std::cout << "Exit Extra Lots = " << remlots << std::endl;
			SendNewOrder(m_BidAskData.ask + (10*tickSizeNew),exchange::rom::Buy, remlots); 
		}
	}
}

bool CalcManager::bullish()
{
    // Long
	try
	{
		if((myPosition == 0) && (!bullFirstTrigg) && (!bearFirstTrigg)) riskQuantity = calRisk1();

        std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
		std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
		std::tm* tm_struct = std::gmtime(&current_time_t);   
		std::string current_Time = std::asctime(tm_struct);

		bool condition1 = false;
		if((lastTradedPrice > local_high1)) condition1 = true;

		bool condition2 = false;
		if(lastTradedPrice > curr_high1) condition2 = true;

		bool condition3 = false; 
		if((local_low1 >= local_low2) && ((local_high1 > local_high2) || (local_high1 > curr_high2) || (local_high1 < local_low2))) condition3 = true;

		bool condition4 = false;
		if((myPosition < riskQuantity) && (myPosition >= 0)) condition4 = true;


		if( condition1 && condition2 && condition3 && condition4 && (bearFirstTrigg == false))
		{

			if(bullFirstTrigg == false)
			{
				std::cout <<current_Time << GetSymbol() << " Long Entry " << "riskQuantity : " << riskQuantity << std::endl;
				std::cout << "Curr High1 " << curr_high1 << "  Curr Low1 " << curr_low1 << " Prev high1 " << prev_high1 << " Prev Low1 " << prev_low1 << " Temp High1 " << temp_high1 << " temp_low1 " << temp_low1  << " Local High1 " << local_high1 << " Local low1 " << local_low1 << " Prev Local High1 " << prev_local_high1 << " Prev Local low1 " << prev_local_low1 << std::endl;
	     		std::cout << "Curr High2 " << curr_high2 << "  Curr Low2 " << curr_low2 << " Prev high2 " << prev_high2 << " Prev Low2 " << prev_low2 << " Temp High2 " << temp_high2 << " temp_low2 " << temp_low2  << " Local High2 " << local_high2 << " Local low2 " << local_low2 << " Prev Local High2 " << prev_local_high2 << " Prev Local low2 " << prev_local_low2 << std::endl;

	
                numBuy++;
				bullFirstTrigg = true;
				LongOrderExitPrice = curr_low1;
				SendNewOrder(m_BidAskData.ask,exchange::rom::Buy, riskQuantity);
				prevChaseBuyOrder = false;
				prevBuyOrderPrice = m_BidAskData.ask;
			}
			else if(bullFirstTrigg==true && curr_BestBid >= prev_BestBid)
			{
				CancelExistingLiveOrders();
				if(prevChaseBuyOrder)
				{
					riskQuantity = calRisk1();
					int leftQuantity = riskQuantity - myPosition;
					SendNewOrder(m_BidAskData.ask,exchange::rom::Buy, leftQuantity);
					prevChaseBuyOrder = false;
				    prevBuyOrderPrice = m_BidAskData.ask;
				}
			}
			return true;
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
		
		bool condition1 = false;
		if(lastTradedPrice < curr_low1) condition1 = true;

		bool condition2 = false;
		if(myPosition > 0) condition2 = true; 

		if(condition1 && condition2 && bullFirstTrigg)
		{
			std::cout << GetSymbol() << " Long Exit Algo1" << " myPosition= " << myPosition << std::endl;
			numSell++;
			longExitPrice = m_BidAskData.bid - (10*tickSizeNew);
			prevBuyExitOrder = false;
			SendNewOrder(m_BidAskData.bid - (10*tickSizeNew),exchange::rom::Sell, myPosition);
			bullFirstTrigg = false;
		}
		else if(condition2 && (bullFirstTrigg == false) && (longExitPrice > lastTradedPrice))
		{
			CancelExistingLiveOrders();
			if(prevBuyExitOrder)
			{
				longExitPrice = m_BidAskData.bid - (10*tickSizeNew);
				prevBuyExitOrder = false;
			    SendNewOrder(m_BidAskData.bid - (10*tickSizeNew),exchange::rom::Sell, myPosition);
			}
		}

		return false;
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::exitbullishposition(): " << e.what() << std::endl;
		return false;
	}
	
}

bool CalcManager::bearish()
{
	// Short
	try
	{
        if((myPosition == 0) && (!bearFirstTrigg) && (!bullFirstTrigg)) riskQuantity = calRisk2();

		std::chrono::system_clock::time_point current_time_utc = std::chrono::system_clock::now(); 
		std::time_t current_time_t = std::chrono::system_clock::to_time_t(current_time_utc);            
		std::tm* tm_struct = std::gmtime(&current_time_t);   
		std::string current_Time = std::asctime(tm_struct);

		bool condition1 = false;
		if((lastTradedPrice < local_low1)) condition1 = true;

        bool condition2 = false;
		if(lastTradedPrice < curr_low1) condition2 = true;

		bool condition3 = false;
		if((local_high1 <= local_high2)  && ((local_low1 < local_low2) || (local_low1 < curr_low2) || (local_low1 > local_high2))) condition3 = true;

		bool condition4 = false;
		if((myPosition > (-1*riskQuantity)) && (myPosition <= 0)) condition4 = true;


		if(condition1 && condition2 && condition3 && condition4 && (bullFirstTrigg == false))            
		{

			if(bearFirstTrigg == false)
			{
				std::cout << current_Time << GetSymbol() << " Short Entry "  << "riskQuantity : " << riskQuantity << std::endl;
				std::cout << "Curr High1 " << curr_high1 << "  Curr Low1 " << curr_low1 << " Prev high1 " << prev_high1 << " Prev Low1 " << prev_low1 << " Temp High1 " << temp_high1 << " temp_low1 " << temp_low1  << " Local High1 " << local_high1 << " Local low1 " << local_low1 << " Prev Local High1 " << prev_local_high1 << " Prev Local low1 " << prev_local_low1 << std::endl;
	     		std::cout << "Curr High2 " << curr_high2 << "  Curr Low2 " << curr_low2 << " Prev high2 " << prev_high2 << " Prev Low2 " << prev_low2 << " Temp High2 " << temp_high2 << " temp_low2 " << temp_low2  << " Local High2 " << local_high2 << " Local low2 " << local_low2 << " Prev Local High2 " << prev_local_high2 << " Prev Local low2 " << prev_local_low2 << std::endl << std::endl;

                numSell++;
				bearFirstTrigg = true;
				ShortOrderExitPrice = curr_high1;
				SendNewOrder(m_BidAskData.bid,exchange::rom::Sell, riskQuantity);
				prevChaseSellOrder = false;
				prevSellOrderPrice = m_BidAskData.bid;
			}
			else if(bearFirstTrigg == true && curr_BestAsk <= prev_BestAsk)
			{
				CancelExistingLiveOrders();
				if(prevChaseSellOrder)
				{
					riskQuantity = calRisk2();
					int leftQuantity = riskQuantity - (-1*myPosition);
					SendNewOrder(m_BidAskData.bid,exchange::rom::Sell, leftQuantity);
					prevChaseSellOrder = false;
				    prevSellOrderPrice = m_BidAskData.bid;
				}
			}
			return true;
		}
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
		
		bool condition1 = false;
		if(lastTradedPrice > curr_high1) condition1 = true;

		bool condition2 = false;
		if(myPosition < 0) condition2 = true;

		if(condition1 && condition2 && bearFirstTrigg)
		{
			numBuy++;
			std::cout << GetSymbol() << " Short Exit Algo1" << " myPosition= " << myPosition << std::endl;
			shortExitPrice = m_BidAskData.ask + (10*tickSizeNew);
			prevSellExitOrder = false;
			SendNewOrder(m_BidAskData.ask + (10*tickSizeNew),exchange::rom::Buy, (-1*myPosition));                       
			bearFirstTrigg = false;
		}
		else if(condition2 && (bearFirstTrigg == false) && (shortExitPrice < lastTradedPrice))
		{
			CancelExistingLiveOrders();
			if(prevSellExitOrder)
			{
				shortExitPrice = m_BidAskData.ask + (10*tickSizeNew);
				prevSellExitOrder = false;
				SendNewOrder(m_BidAskData.ask + (10*tickSizeNew),exchange::rom::Buy, (-1*myPosition)); 
			}
		}

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
			settlementFlag = false;
			if(myPosition > 0)
			{
				numSell++;
				SendNewOrder(m_BidAskData.bid - 10*tickSizeNew,exchange::rom::Sell, myPosition);
	
			}
			if(myPosition < 0)
			{
				numBuy++;
				SendNewOrder(m_BidAskData.ask + 10*tickSizeNew,exchange::rom::Buy, (-1*myPosition));
			}
		}

		if((settlementFlag == true) && (GetSymbol() == "MCLF5") && (myPosition!=0) && (current_hour == 19 && current_minute >= 00))
		{
			settlementFlag = false;
			if(myPosition > 0)
			{
				numSell++;
				SendNewOrder(m_BidAskData.bid - 10*tickSizeNew,exchange::rom::Sell, myPosition);
	
			}
			if(myPosition < 0)
			{
				numBuy++;
				SendNewOrder(m_BidAskData.ask + 10*tickSizeNew,exchange::rom::Buy, (-1*myPosition));
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

		prev_BestAsk = curr_BestAsk;
		prev_BestBid = curr_BestBid;
		curr_BestAsk = m_BidAskData.ask;
		curr_BestBid = m_BidAskData.bid;

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
		FormCandle();
		CalcManager::TradingTimings(GetSymbol());

		if((CalcManager::connectVar == 1) && (tradingStatusOnOffInd == true))
		{
			// Algorithm For Buy and Sell
			if(CalcManager::TradingTimings(GetSymbol()) && (numTrade <= 50))                                                      // We are using flagTimer2 (Algo start after formation 2nd candle && between 2:30pm-2:30am)
			{
				bullish();
				bearish();
			}
			exitbullishposition();
			exitbearishposition();
		}
		else
		{
			//std::cout << "Not Connected : CalcManager::connectVar == 0" << std::endl;
		}

		// Trade Settlement (20:00(1:30) (MCL : 19:00(12:30)))
		TradeSettlement();





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
		else if(GetSymbol() == "MCLF5") 
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

		prevChaseBuyOrder = true;
		prevChaseSellOrder = true;
		prevBuyExitOrder = true;
		prevSellExitOrder = true;

		prevBuyOrderPrice = 0;
		prevSellOrderPrice = INT_MAX;

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
		prevBuyExitOrder = true;
		prevSellExitOrder = true;

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

		string BuySell;
		ctrSpec::Price currPrice = 0;
		if(msg.getSide() == 1)
		{
			BuySell = "Buy";
			currPrice = (-1*(msg.getExecPrice()));
			myPosition = myPosition + std::stoi(msg.getLastShares());    
		}
		else
		{
			BuySell = "Sell";
			currPrice = msg.getExecPrice();
			myPosition = myPosition - std::stoi(msg.getLastShares());
		}

		std::cout << msg.getSymbol() << " Order Filled : " << BuySell << " Prize " << msg.getExecPrice() << "  QuantityFilled : " << msg.getLastShares() << "  " << current_Time << std::endl;
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
		if(myPosition == 0)
		{
			bullFirstTrigg = false;
	        bearFirstTrigg = false;
			exitExtraLotsFlag = true;
		}


		if(myPosition == 0)
		{
			numTrade++;
			int currQuantity = std::stoi(msg.getQty());
			ctrSpec::Price profit = (currPrice + prevPrice)*(riskQuantity);
			int factorPNL= priceVal;
            
			profit = profit*factorPNL;

			if(profit > maxProf) maxProf = profit;
			if(profit < maxLoss) maxLoss = profit;

			PNL += profit;
		}

		prevPrice = currPrice;

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
			high1 = lastTradedPrice;
			low1 = lastTradedPrice;

			firstFeed = false;

			//SendNewOrder(m_BidAskData.ask + 20*tickSizeNew,exchange::rom::Sell, 1);
		}

		if(high1 == 0) high1 = lastTradedPrice;
		if(low1 == 0) low1 = lastTradedPrice;
		
		// Logic for calculate high, low.
		if(lastTradedPrice > high1) high1 = lastTradedPrice;
		if(lastTradedPrice < low1) low1 = lastTradedPrice;
 
        if(high1 > curr_high1)
		{
			if(flagFlyChange1) prev_local_low1 = pos_local_low1;
			flagFlyChange1 = false;
			local_low1 = temp_low1;
		}
		if(low1 < curr_low1)
		{
			if(flagFlyChange2) prev_local_high1 = pos_local_high1;
			flagFlyChange2 = false;
			local_high1 = temp_high1;
		}


		if(curr_high1 == 0 || curr_low1 == 0)
		{
			curr_high1 = high1;
			curr_low1 = low1;
			temp_high1 = high1;
			temp_low1 = low1;
		}

		if((((tm_struct->tm_min)%15 == 0)) && flag == true)         //(tm_struct_chicago->tm_hour - 1 + 4)
		{
			//Implementation of Inside Candle
			if((high1>curr_high1) || (low1<curr_low1))
			{
				prev_high1 = curr_high1;
				prev_low1 = curr_low1;
				curr_high1 = high1;
				curr_low1 = low1;
				newFlag = true;
			}
			if((curr_high1 > prev_high1) && (curr_low1 < prev_low1))
			{
				temp_high1 = curr_high1;
				temp_low1 = curr_low1;
				if(newFlag)
				{
					pos_prev_local_low1 = pos_local_low1;
				    pos_prev_local_high1 = pos_local_high1;
					newFlag = false;
				}

				if(CalcManager::TradingTimings(GetSymbol())) exitExtraLots();
			}
			if( curr_high1 > prev_high1)
			{
				if((curr_high1 > prev_high1) && (curr_low1 < prev_low1))
				{
					posflag1 = false;
				    posflag2 = false;
				}

				temp_high1 = curr_high1;
				if(posflag1)
				{
					pos_prev_local_low1 = pos_local_low1;
				}
				flagFlyChange2 = true;
				posflag1 = false;
				posflag2 = true;

				pos_local_low1 = temp_low1;
			}
			if(curr_low1< prev_low1)
			{
				if((curr_high1 > prev_high1) && (curr_low1 < prev_low1))
				{
					posflag1 = false;
				    posflag2 = false;
				}

				temp_low1 = curr_low1; 
				if(posflag2)
				{
					pos_prev_local_high1 = pos_local_high1;
				}
				flagFlyChange1 = true;
				posflag2 = false;
				posflag1 = true;

				pos_local_high1 = temp_high1;
			}
			
			if((curr_high1 > prev_high1) && (curr_low1 < prev_low1))
			{
				flagFlyChange1 = false;
				flagFlyChange2 = false;
				posflag1 = false;
				posflag2 = false;
			}

		
		    local_high1 = pos_local_high1;
			prev_local_high1 = pos_prev_local_high1;
			local_low1 = pos_local_low1;
			prev_local_low1 = pos_prev_local_low1;

		    

			std::cout << GetSymbol() << "  " << current_Time << "  Myposition " << myPosition  << " Trade " << numTrade <<  std::endl;
			std::cout << "Curr High1 " << curr_high1 << "  Curr Low1 " << curr_low1 << " Prev high1 " << prev_high1 << " Prev Low1 " << prev_low1 << " Temp High1 " << temp_high1 << " temp_low1 " << temp_low1  << " Local High1 " << local_high1 << " Local low1 " << local_low1 << " Prev Local High1 " << prev_local_high1 << " Prev Local low1 " << prev_local_low1 << std::endl;
			std::cout << "Curr High2 " << curr_high2 << "  Curr Low2 " << curr_low2 << " Prev high2 " << prev_high2 << " Prev Low2 " << prev_low2 << " Temp High2 " << temp_high2 << " temp_low2 " << temp_low2  << " Local High2 " << local_high2 << " Local low2 " << local_low2 << " Prev Local High2 " << prev_local_high2 << " Prev Local low2 " << prev_local_low2 << std::endl;

	
			//std::cout << pos_local_high1 << " " << pos_local_low1 << " " << pos_prev_local_high1 << " " << pos_prev_local_low1 << std::endl;
			//std::cout << endl;
			high1 = lastTradedPrice;
			low1 = lastTradedPrice;
			flag = false;
			cntCandle++;


		}
		if(((tm_struct->tm_min)%15  == 1))
		{
			flag = true;
		}





    // ######################## For 2nd CANDLE (Daily)

	// update high2, low2 for first feed.
	    
		if(firstFeed2 == true)
		{
			high2 = lastTradedPrice;
			low2 = lastTradedPrice;
			firstFeed2 = false;
		}

		if(high2 == 0) high2 = lastTradedPrice;
		if(low2 == 0) low2 = lastTradedPrice;
		
		// Logic for calculate high2 , low2.
		if(lastTradedPrice > high2) high2 = lastTradedPrice;
		if(lastTradedPrice < low2) low2 = lastTradedPrice;

		if(high2 > curr_high2)
		{
			if(flagFlyChange12) prev_local_low2 = pos_local_low2;
			flagFlyChange12 = false;
			local_low2 = temp_low2;
		}
		if(low2 < curr_low2)
		{
			if(flagFlyChange22) prev_local_high2 = pos_local_high2;
			flagFlyChange22 = false;
			local_high2 = temp_high2;
		}

		if(curr_high2 == 0 || curr_low2 == 0)
		{
			curr_high2 = high2;
			curr_low2 = low2;
			temp_high2 = high2;
			temp_low2 = low2;
		}
        


		if(((tm_struct->tm_min)%60 == 0) && flag2 == true)
		{
			//Implementation of Inside Candle
			if((high2>curr_high2) || (low2<curr_low2))
			{
				prev_high2 = curr_high2;
				prev_low2 = curr_low2;
				curr_high2 = high2;
				curr_low2 = low2;
				newFlag2 = true;
			}
			if((curr_high2 > prev_high2) && (curr_low2 < prev_low2))
			{
				temp_high2 = curr_high2;
				temp_low2 = curr_low2;
				if(newFlag2)
				{
					pos_prev_local_low2 = pos_local_low2;
				    pos_prev_local_high2 = pos_local_high2;
					newFlag2 = false;
				}
			}

			if( curr_high2 > prev_high2)
			{
				if((curr_high2 > prev_high2) && (curr_low2 < prev_low2))
				{
					posflag12 = false;
				    posflag22 = false;
				}

				temp_high2 = curr_high2;
				if(posflag12)
				{
					pos_prev_local_low2 = pos_local_low2;
				}
				flagFlyChange22 = true;
				posflag12 = false;
				posflag22 = true;

				pos_local_low2 = temp_low2;
			}
			if(curr_low2< prev_low2)
			{
				if((curr_high2 > prev_high2) && (curr_low2 < prev_low2))
				{
					posflag12 = false;
				    posflag22 = false;
				}

				temp_low2 = curr_low2; 
				if(posflag22)
				{
					pos_prev_local_high2 = pos_local_high2;
				}
				flagFlyChange12 = true;
				posflag22 = false;
				posflag12 = true;

				pos_local_high2 = temp_high2;
			}

			if((curr_high2 > prev_high2) && (curr_low2 < prev_low2))
			{
				flagFlyChange12 = false;
				flagFlyChange22 = false;
				posflag12 = false;
				posflag22 = false;
			}


			local_high2 = pos_local_high2;
			prev_local_high2 = pos_prev_local_high2;
			local_low2 = pos_local_low2;
			prev_local_low2 = pos_prev_local_low2;
		
			std::cout << GetSymbol() << " Candle2: Big Candle " << current_Time  << "  Local High2 : " << local_high2 << "  Local low2 : " << local_low2 << "Current High2 : " << curr_high2 << "  Current Low2 : " << curr_low2 << std::endl;
			//std::cout << endl;
			high2 = lastTradedPrice;
			low2 = lastTradedPrice;
			flag2 = false;
			// tradingStatusOnOffInd = false;
			// closePosition = 1;
			// std::cout << "TradingStatus : " << tradingStatusOnOffInd << " OpenPositions" << std::endl << std::endl;

		}
		if(((tm_struct->tm_min)%60 == 55))
		{ 
			flag2 = true;
		}
	}
	catch(const std::exception &e)
	{
		std::cerr << "Exception caught in CalcManager::FormCandle(): " << e.what() << std::endl;
	}
 
}

void CalcManager::ResetHighLowValues()
{ 
	std::string input = CalcManager::HighLow;
	std::stringstream ss(input);
    std::string token;
    size_t count = 0;

    // Tokenize the input string by comma and extract values
    while (std::getline(ss, token, ',')) 
	{
        try 
		{
            count++;
        } 
		catch (const std::invalid_argument& e) 
		{
            std::cerr << "Error: Invalid value detected in input: " << e.what() << std::endl;
            return ;
        } 
		catch (const std::out_of_range& e) 
		{
            std::cerr << "Error: Value out of range in input: " << e.what() << std::endl;
            return ;
        }
	}

	if(count != 12)
	{
		std::cout << "Invalid input" << std::endl;
		return ;
	}


	//std::cout << "CalcManager::ResetHighLowValues()1" << std::endl;

	// Find the position of the first comma
    size_t firstCommaPos = input.find(',');

    // Find the position of the second comma
    size_t secondCommaPos = input.find(',', firstCommaPos + 1);

    // Extract the substring between the first and second comma
    std::string resultSymbol = input.substr(firstCommaPos + 1, secondCommaPos - firstCommaPos - 1);
	if(resultSymbol == GetSymbol())
	{	
		//std::cout << "CalcManager::ResetHighLowValues()2" << std::endl;
		if( CalcManager::HighLow[0] == 'd')
		{
			//std::cout << "CalcManager::ResetHighLowValues()3" << std::endl;
			// Find the position of the second comma
			size_t secondCommaPos = input.find(',', input.find(',') + 1);
			
			// Extract the substring after the second comma
			std::string substr = input.substr(secondCommaPos + 1);
			
			// Create a string stream from the substring
			std::stringstream ss(substr);
			std::string token;
			
			std::getline(ss, token, ','); curr_high1 = std::stod(token);
			std::getline(ss, token, ','); curr_low1 = std::stod(token);
			std::getline(ss, token, ','); prev_high1 = std::stod(token);
			std::getline(ss, token, ','); prev_low1 = std::stod(token);
			std::getline(ss, token, ','); temp_high1 = std::stod(token);
			std::getline(ss, token, ','); temp_low1 = std::stod(token);
			std::getline(ss, token, ','); local_high1 = std::stod(token);
			std::getline(ss, token, ','); local_low1 = std::stod(token);
			std::getline(ss, token, ','); prev_local_high1 = std::stod(token);
			std::getline(ss, token, ','); prev_local_low1 = std::stod(token);

			pos_local_high1 = local_high1;
			pos_local_low1 = local_low1;
			pos_prev_local_high1 = prev_local_high1;
			pos_prev_local_low1 = prev_local_low1;

			if((curr_high1 > prev_high1) && (curr_low1 < prev_low1))
			{
				flagFlyChange1 = false;
				flagFlyChange2 = false;
				posflag1 = false;
				posflag2 = false;
			}
			else if(curr_high1 > prev_high1)
			{
				flagFlyChange2 = true;
				posflag2 = true;
			}
			else if(curr_low1 < prev_low1)
			{
				flagFlyChange1 = true;
				posflag1 = true;
			}
			
            std::cout << "ResetHighLowValues for Candle1" << std::endl;
			std::cout << GetSymbol() << "  " << "Current High1 : " << curr_high1 << "  Current Low1 : " << curr_low1 << " Prev_high1: " << prev_high1 << " Prev_low1: " << prev_low1 << " Temp_high1: " << temp_high1 << " Temp_low1: " << temp_low1  << std::endl;
			std::cout <<  "  Local High1 : " << local_high1 << "  Local low1 : " << local_low1 << "   Prev Local High1 : " << prev_local_high1 << " Prev Local low1 : " << prev_local_low1 << " pos_local_high1 " << pos_local_high1  << " pos_local_low1 " << pos_local_low1 << " pos_prev_local_high1 " << pos_prev_local_high1 << " pos_prev_local_low1 " << pos_prev_local_low1  << std::endl << std::endl;
			
		}
		if( CalcManager::HighLow[0] == 'D')
		{
			//std::cout << "CalcManager::ResetHighLowValues()3" << std::endl;
			// Find the position of the second comma
			size_t secondCommaPos = input.find(',', input.find(',') + 1);
			
			// Extract the substring after the second comma
			std::string substr = input.substr(secondCommaPos + 1);
			
			// Create a string stream from the substring
			std::stringstream ss(substr);
			std::string token;
			
			std::getline(ss, token, ','); curr_high2 = std::stod(token);
			std::getline(ss, token, ','); curr_low2 = std::stod(token);
			std::getline(ss, token, ','); prev_high2 = std::stod(token);
			std::getline(ss, token, ','); prev_low2 = std::stod(token);
			std::getline(ss, token, ','); temp_high2 = std::stod(token);
			std::getline(ss, token, ','); temp_low2 = std::stod(token);
			std::getline(ss, token, ','); local_high2 = std::stod(token);
			std::getline(ss, token, ','); local_low2 = std::stod(token);
			std::getline(ss, token, ','); prev_local_high2 = std::stod(token);
			std::getline(ss, token, ','); prev_local_low2 = std::stod(token);
			
			pos_local_high2 = local_high2;
			pos_local_low2 = local_low2;
			pos_prev_local_high2 = prev_local_high2;
			pos_prev_local_low2 = prev_local_low2;

			if((curr_high2 > prev_high2) && (curr_low2 < prev_low2))
			{
				flagFlyChange12 = false;
				flagFlyChange22 = false;
				posflag12 = false;
				posflag22 = false;
			}
			else if(curr_high2 > prev_high2)
			{
				flagFlyChange22 = true;
				posflag22 = true;
			}
			else if(curr_low2 < prev_low2)
			{
				flagFlyChange12 = true;
				posflag12 = true;
			}
			
            std::cout << "ResetHighLowValues for Candle2" << std::endl;
            std::cout << GetSymbol() << "  " << "Current High2 : " << curr_high2 << "  Current Low2 : " << curr_low2 << " prev_high2: " << prev_high2 << " prev_low2: " << prev_low2 << " temp_high2: " << temp_high2 << " temp_low2: " << temp_low2  << std::endl;
		    std::cout <<  "  Local High2 : " << local_high2 << "  Local low2 : " << local_low2 << "   Prev Local High2 : " << prev_local_high2 << " Prev Local low2 : " << prev_local_low2 << " pos_local_high2 " << pos_local_high2  << " pos_local_low2 " << pos_local_low2 << " pos_prev_local_high2 " << pos_prev_local_high2 << " pos_prev_local_low2 " << pos_prev_local_low2  << std::endl << std::endl;

		}
		if( CalcManager::HighLow[0] == 'F')
		{
			//std::cout << "CalcManager::ResetHighLowValues()3" << std::endl;
			// Find the position of the second comma
			size_t secondCommaPos = input.find(',', input.find(',') + 1);
			
			// Extract the substring after the second comma
			std::string substr = input.substr(secondCommaPos + 1);
			
			// Create a string stream from the substring
			std::stringstream ss(substr);
			std::string token;
			
			std::getline(ss, token, ','); curr_high3 = std::stod(token);
			std::getline(ss, token, ','); curr_low3 = std::stod(token);
			std::getline(ss, token, ','); prev_high3 = std::stod(token);
			std::getline(ss, token, ','); prev_low3 = std::stod(token);
			std::getline(ss, token, ','); temp_high3 = std::stod(token);
			std::getline(ss, token, ','); temp_low3 = std::stod(token);
			std::getline(ss, token, ','); local_high3 = std::stod(token);
			std::getline(ss, token, ','); local_low3 = std::stod(token);
			std::getline(ss, token, ','); prev_local_high3 = std::stod(token);
			std::getline(ss, token, ','); prev_local_low3 = std::stod(token);
			
			pos_local_high3 = local_high3;
			pos_local_low3 = local_low3;
			pos_prev_local_high3 = prev_local_high3;
			pos_prev_local_low3 = prev_local_low3;
			
            std::cout << "ResetHighLowValues for Candle3" << std::endl;
            std::cout << GetSymbol() << "  " << "Current High3 : " << curr_high3 << "  Current Low3 : " << curr_low3 << " prev_high3: " << prev_high3 << " prev_low3: " << prev_low3 << " temp_high3: " << temp_high2 << " temp_low3: " << temp_low3  << std::endl;
		    std::cout <<  "  Local High3 : " << local_high3 << "  Local low3 : " << local_low3 << "   Prev Local High3 : " << prev_local_high3 << " Prev Local low3 : " << prev_local_low3 << " pos_local_high3 " << pos_local_high3  << " pos_local_low3 " << pos_local_low3 << " pos_prev_local_high3 " << pos_prev_local_high3 << " pos_prev_local_low3 " << pos_prev_local_low3  << std::endl << std::endl;

		}
	}
}


