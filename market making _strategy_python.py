import pandas as pd
import time

# =============================
# SIMPLE ADL QUOTING LOGIC
# =============================

MAIN_INSTRUMENT = "ES"
HEDGE_INSTRUMENT = "NQ"

ORDER_QTY = 1

position = 0
entry_price = None
trade_number = 0

data = pd.read_csv("market_data.csv")

print("\n===== STRATEGY STARTED =====\n")

for i, row in data.iterrows():

    es_bid = row["ES_Bid"]
    es_ask = row["ES_Ask"]

    nq_bid = row["NQ_Bid"]
    nq_ask = row["NQ_Ask"]

    print("\n--------------------------------")
    print("Market Update:", i+1)
    print("ES Bid:", es_bid, "| ES Ask:", es_ask)
    print("NQ Bid:", nq_bid, "| NQ Ask:", nq_ask)

    # =============================
    # ENTRY
    # =============================
    if position == 0:

        entry_price = es_bid
        trade_number += 1

        print("\n>>> ENTRY TRADE", trade_number)
        print("BUY", MAIN_INSTRUMENT, "at", entry_price)

        position = 1
        continue

    # =============================
    # EXIT
    # =============================
    if position == 1:

        exit_price = es_ask

        pnl = (exit_price - entry_price) * ORDER_QTY

        print("\n>>> EXIT TRADE", trade_number)
        print("SELL", MAIN_INSTRUMENT, "at", exit_price)

        print("Entry Price :", entry_price)
        print("Exit Price  :", exit_price)
        print("PnL :", pnl)

        # Hedge order
        hedge_price = nq_bid

        print("\n>>> HEDGE ORDER")
        print("SELL", HEDGE_INSTRUMENT, "at", hedge_price)

        print("\n===== TRADE COMPLETED =====")

        position = 0

        time.sleep(3)

print("\n===== STRATEGY FINISHED =====")