class profit_loss:
    def a(self):
        symbol = "esh4"
        qty = 1
        tick = 50
        sell_price = 5095.75
        buy_price = 5082
        print("esh4:", (sell_price - buy_price) * qty * tick)

    def b(self):
        symbol = "nqh4"
        qty = 1
        tick = 20
        sell_price = 18028.25
        buy_price = 18043.5
        print("nqh4:", (sell_price - buy_price) * qty * tick)

    def c(self):
        symbol = "ymh4"
        qty = 1
        tick = 5
        sell_price = 39024
        buy_price = 39016
        print("ymh4:", (sell_price - buy_price) * qty * tick)


# Instantiate the class and call the methods
pl = profit_loss()
pl.a()
pl.b()
pl.c()

