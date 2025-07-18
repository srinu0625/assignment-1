import backtrader as bt

class ATRBreakoutStrategy(bt.Strategy):
    params = dict(
        atr_period=3,
        stop_loss_atr=1.0,
        take_profit_atr=2.0,
        contract_size=5,
        trade_cost=1.30,
    )
    
    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(self.data, period=self.params.atr_period)
        self.two_dh = bt.ind.Highest(self.data.high, period=2)
        self.two_dl = bt.ind.Lowest(self.data.low, period=2)
        
        self.entry_price = 0
        self.trade_pnls = []
    
    def next(self):
        close = self.data.close[0]
        atr = self.atr[0]
        two_dh = self.two_dh[0]
        two_dl = self.two_dl[0]

        buy_rate = two_dh + 1.5 * atr
        sell_rate = two_dh - 1.5 * atr
        
        if not self.position:
            if close > buy_rate:
                self.buy(size=self.params.contract_size)
                self.entry_price = close
                print(f"LONG ENTRY at {self.data.datetime.date(0)}, price {close:.2f}")
            elif close < sell_rate:
                self.sell(size=self.params.contract_size)
                self.entry_price = close
                print(f"SHORT ENTRY at {self.data.datetime.date(0)}, price {close:.2f}")
        else:
            if self.position.size > 0:
                stop_loss = self.entry_price - self.params.stop_loss_atr * atr
                take_profit = self.entry_price + self.params.take_profit_atr * atr
                if close <= stop_loss or close < sell_rate or close >= take_profit:
                    pnl = (close - self.entry_price) * self.params.contract_size - self.params.trade_cost
                    self.trade_pnls.append(pnl)
                    self.close()
                    print(f"LONG EXIT at {self.data.datetime.date(0)}, price {close:.2f}, PnL: {pnl:.2f}")
            else:
                stop_loss = self.entry_price + self.params.stop_loss_atr * atr
                take_profit = self.entry_price - self.params.take_profit_atr * atr
                if close >= stop_loss or close > buy_rate or close <= take_profit:
                    pnl = (self.entry_price - close) * self.params.contract_size - self.params.trade_cost
                    self.trade_pnls.append(pnl)
                    self.close()
                    print(f"SHORT EXIT at {self.data.datetime.date(0)}, price {close:.2f}, PnL: {pnl:.2f}")

    def stop(self):
        total_trades = len(self.trade_pnls)
        positive_trades = len([p for p in self.trade_pnls if p > 0])
        negative_trades = len([p for p in self.trade_pnls if p <= 0])
        total_pnl = sum(self.trade_pnls)
        print("\n=== Summary ===")
        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {positive_trades}")
        print(f"Losing Trades: {negative_trades}")
        print(f"Total PnL: {total_pnl:.2f}")

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    
    data_path = r"D:\Data\BR Jun25_10min.csv"  # Change to your file path
    
    data = bt.feeds.GenericCSVData(
    dataname=data_path,
    dtformat=('%d-%m-%Y %H.%M'),  # Match your datetime format here
    datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=5,
    openinterest=-1,
    timeframe=bt.TimeFrame.Minutes,
    compression=30,
    headers=True
)

    
    cerebro.adddata(data)
    cerebro.addstrategy(ATRBreakoutStrategy)
    
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.0)
    
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")
