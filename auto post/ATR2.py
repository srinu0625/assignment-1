for i in range(1, len(df)):
    row, prev = df.loc[i], df.loc[i-1]
    dt = row['DATETIME']

    # ============================
    #           EXITS
    # ============================
    if position:

        side = position["side"]
        stop = position["stop"]
        tps  = position["tp_prices"]

        # -------- LONG EXIT --------
        if side == "long":

            # Stop Loss
            if row["LOW"] <= stop:
                for _ in range(position["units_remaining"]):
                    lot = position["remaining_lots"].pop(0)
                    record_fill(trades, dt, "SELL", "STOP LOSS",
                                f"LOW {row['LOW']} <= STOP {stop}",
                                stop, 1, position,
                                lot_id=lot, atr=row["ATR"], ma24=row["MA24"])
                position = None
                continue

            # Take Profits
            for idx, tp in enumerate(tps):
                if not position["tp_hit_flags"][idx] and row["HIGH"] >= tp:
                    lot = position["remaining_lots"].pop(0)
                    record_fill(trades, dt, "SELL", f"TP{idx+1} HIT",
                                f"HIGH {row['HIGH']} >= TP {tp}",
                                tp, 1, position,
                                lot_id=lot, atr=row["ATR"], ma24=row["MA24"])

                    position["units_remaining"] -= 1
                    position["tp_hit_flags"][idx] = True

                    # Move Stop
                    if idx == 0: position["stop"] = position["entry_price"]
                    elif idx == 1: position["stop"] = tps[0]

            if position["units_remaining"] <= 0:
                position = None
                continue

        # -------- SHORT EXIT --------
        else:

            # Stop Loss
            if row["HIGH"] >= stop:
                for _ in range(position["units_remaining"]):
                    lot = position["remaining_lots"].pop(0)
                    record_fill(trades, dt, "BUY", "STOP LOSS",
                                f"HIGH {row['HIGH']} >= STOP {stop}",
                                stop, 1, position,
                                lot_id=lot, atr=row["ATR"], ma24=row["MA24"])
                position = None
                continue

            # Take Profits
            for idx, tp in enumerate(tps):
                if not position["tp_hit_flags"][idx] and row["LOW"] <= tp:
                    lot = position["remaining_lots"].pop(0)
                    record_fill(trades, dt, "BUY", f"TP{idx+1} HIT",
                                f"LOW {row['LOW']} <= TP {tp}",
                                tp, 1, position,
                                lot_id=lot, atr=row["ATR"], ma24=row["MA24"])

                    position["units_remaining"] -= 1
                    position["tp_hit_flags"][idx] = True

                    if idx == 0: position["stop"] = position["entry_price"]
                    elif idx == 1: position["stop"] = tps[0]

            if position["units_remaining"] <= 0:
                position = None
                continue


    # ============================
    #           ENTRIES
    # ============================
    if position is None:

        atr_up = row["ATR"] > prev["ATR"]

        long_cond = (
            prev["CLOSE"] <= prev["HH50"] and
            row["CLOSE"]  > prev["HH50"]  and
            row["CLOSE"]  > row["MA24"]   and atr_up
        )

        short_cond = (
            prev["CLOSE"] >= prev["LL50"] and
            row["CLOSE"]  < prev["LL50"]  and
            row["CLOSE"]  < row["MA24"]   and atr_up
        )

        # ----- LONG ENTRY -----
        if long_cond:
            entry = row["CLOSE"]
            atr   = row["ATR"]
            tps   = [entry + m * atr for m in TP_MULTS]

            position = {
                "side": "long",
                "entry_price": entry,
                "units_remaining": UNITS_PER_ENTRY,
                "stop": entry - SL_MULT * atr,
                "tp_prices": tps,
                "tp_hit_flags": [False]*3,
                "remaining_lots": [1,2,3]
            }

            record_fill(trades, dt, "BUY", "ENTRY",
                        f"Long | SL={position['stop']} | TPs={tps}",
                        entry, UNITS_PER_ENTRY, position,
                        atr=atr, ma24=row["MA24"])

            print("\n===== LONG ENTRY =====")
            print(row[["OPEN","HIGH","LOW","CLOSE","HH50","LL50"]])
            print("ENTRY AT CLOSE:", entry)
            print("======================\n")
            time.sleep(150)

        # ----- SHORT ENTRY -----
        elif short_cond:
            entry = row["CLOSE"]
            atr   = row["ATR"]
            tps   = [entry - m * atr for m in TP_MULTS]

            position = {
                "side": "short",
                "entry_price": entry,
                "units_remaining": UNITS_PER_ENTRY,
                "stop": entry + SL_MULT * atr,
                "tp_prices": tps,
                "tp_hit_flags": [False]*3,
                "remaining_lots": [1,2,3]
            }

            record_fill(trades, dt, "SELL", "ENTRY",
                        f"Short | SL={position['stop']} | TPs={tps}",
                        entry, UNITS_PER_ENTRY, position,
                        atr=atr, ma24=row["MA24"])

            print("\n===== SHORT ENTRY =====")
            print(row[["OPEN","HIGH","LOW","CLOSE","HH50","LL50"]])
            print("ENTRY AT CLOSE:", entry)
            print("=======================\n")
            time.sleep(150)

return trades
