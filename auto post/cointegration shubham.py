import eikon as ek
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
import matplotlib.pyplot as plt
import time   # <--- added


# CONFIG

POINT_VALUE = 1000
START_DATE = "2025-10-01"
END_DATE = "2025-11-08"
INTERVAL = "minute"

RIC_1 = "ESc1"
RIC_2 = "YMc1"

ek.set_app_key("92e0a59a8e994142bab0f82d8294e1df404da224")


# Download Data

def download_data(ric1, ric2):
    print(f"\n[INFO] Downloading data for {ric1} and {ric2}...")
    print(f"       Date range: {START_DATE} → {END_DATE}")
    print(f"       Interval  : {INTERVAL}")
    time.sleep(1.5)

    try:
        df = ek.get_timeseries(
            [ric1, ric2],
            start_date=START_DATE,
            end_date=END_DATE,
            interval=INTERVAL
        )

        # ---- Improved Error Handling ----
        if df is None:
            raise ValueError("Eikon returned None. Wrong RIC or expired contract.")

        if not isinstance(df, pd.DataFrame):
            raise ValueError("Unexpected data type returned from Eikon API.")

        if df.empty:
            raise ValueError("Eikon returned an empty DataFrame — no data in this date range.")

        print("[INFO] Raw data downloaded:", len(df), "rows")
        time.sleep(1.0)
        return df.dropna()

    except Exception as e:
        print("[ERROR] Download failed:", e)
        time.sleep(1.5)
        return None


# Clean MultiIndex Columns into Flat DF

def clean_columns(raw_df, ric1, ric2):
    print("\n[INFO] Cleaning columns...")
    time.sleep(1.5)

    if not isinstance(raw_df.columns, pd.MultiIndex):
        print("[ERROR] Data is not MultiIndex OHLCV format.")
        raise ValueError("Expected MultiIndex OHLCV data from Eikon.")

    df = pd.concat([
        raw_df[(ric1, 'OPEN')].rename('open_1'),
        raw_df[(ric1, 'HIGH')].rename('high_1'),
        raw_df[(ric1, 'LOW')].rename('low_1'),
        raw_df[(ric1, 'CLOSE')].rename('close_1'),
        raw_df[(ric1, 'VOLUME')].rename('volume_1'),

        raw_df[(ric2, 'OPEN')].rename('open_2'),
        raw_df[(ric2, 'HIGH')].rename('high_2'),
        raw_df[(ric2, 'LOW')].rename('low_2'),
        raw_df[(ric2, 'CLOSE')].rename('close_2'),
        raw_df[(ric2, 'VOLUME')].rename('volume_2'),
    ], axis=1)

    print("[INFO] Cleaned data rows:", len(df))
    time.sleep(1.5)
    return df.astype(float)


# Resample to 15-minute bars

def resample_bars(df):
    print("\n[INFO] Resampling to 15-minute bars...")
    time.sleep(1.5)

    rules = {
        'open_1': 'first', 'high_1': 'max', 'low_1': 'min', 'close_1': 'last', 'volume_1': 'sum',
        'open_2': 'first', 'high_2': 'max', 'low_2': 'min', 'close_2': 'last', 'volume_2': 'sum',
    }
    out = df.resample("15T").agg(rules).dropna()

    print("[INFO] Resampled rows:", len(out))
    time.sleep(1.5)
    return out


# Cointegration & Hedge Ratio

def compute_hedge_ratio(series1, series2):
    print("\n-----> Running cointegration test...")
    time.sleep(1.5)

    score, pvalue, _ = coint(series1, series2)
    print(f"-----> Cointegration p-value = {pvalue:.4f}")
    time.sleep(1.5)

    if pvalue >= 0.1:
        print("-----> Series NOT cointegrated. Exiting.\n")
        time.sleep(1.5)
        return None

    print("-----> Running OLS to compute hedge ratio...")
    time.sleep(1.5)

    X = sm.add_constant(series2)
    model = sm.OLS(series1, X).fit()
    hedge_ratio = model.params[series2.name]

    print(f"-----> Hedge Ratio = {hedge_ratio:.5f}")
    time.sleep(1.5)
    return hedge_ratio


# Backtest

def run_backtest(df, hedge_ratio,
                 z_window=30,
                 entry_thr=2,
                 stop_thr=4,
                 exit_thr=0):

    print("\n-----> Starting backtest...")
    print(f"       Hedge Ratio : {hedge_ratio:.5f}")
    print(f"       Z-window    : {z_window}")
    print(f"       Entry thr   : ±{entry_thr}")
    print(f"       Stop thr    : ±{stop_thr}")
    time.sleep(1.5)

    s1 = df["close_1"]
    s2 = df["close_2"]

    spread = s1 - hedge_ratio * s2
    spread_mean = spread.rolling(z_window).mean()
    spread_std = spread.rolling(z_window).std()
    zscore = (spread - spread_mean) / spread_std

    backtest_df = pd.DataFrame({"s1": s1, "s2": s2, "spread": spread, "z": zscore})
    backtest_df["pos"] = 0

    position = 0
    trades = []
    active_trade = None

    for i in range(1, len(backtest_df)):
        z = backtest_df["z"].iloc[i]
        idx = backtest_df.index[i]

        # ENTRY
        if position == 0:
            if z < -entry_thr: 
                print(f"[LONG ENTRY] {idx} | Z={z:.2f}")
                time.sleep(1.5)
                position = 1
                active_trade = {
                    "entry_time": idx,
                    "type": "long",
                    "entry_z": z,
                    "s1_e": backtest_df["s1"].iloc[i],
                    "s2_e": backtest_df["s2"].iloc[i]
                }

            elif z > entry_thr:
                print(f"[SHORT ENTRY] {idx} | Z={z:.2f}")
                time.sleep(1.5)
                position = -1
                active_trade = {
                    "entry_time": idx,
                    "type": "short",
                    "entry_z": z,
                    "s1_e": backtest_df["s1"].iloc[i],
                    "s2_e": backtest_df["s2"].iloc[i]
                }

        # EXIT LONG
        elif position == 1:
            if z >= exit_thr or z <= -stop_thr:
                pnl = ((backtest_df["s1"].iloc[i] - active_trade["s1_e"])
                       - hedge_ratio * (backtest_df["s2"].iloc[i] - active_trade["s2_e"])) * POINT_VALUE

                print(f"[LONG EXIT] {idx} | Z={z:.2f} | PnL={pnl:.2f}")
                time.sleep(1.5)

                active_trade.update({"exit_time": idx, "exit_z": z, "pnl": pnl})
                trades.append(active_trade)
                active_trade = None
                position = 0

        # EXIT SHORT
        elif position == -1:
            if z <= exit_thr or z >= stop_thr:
                pnl = (-(backtest_df["s1"].iloc[i] - active_trade["s1_e"])
                       + hedge_ratio * (backtest_df["s2"].iloc[i] - active_trade["s2_e"])) * POINT_VALUE

                print(f"[SHORT EXIT] {idx} | Z={z:.2f} | PnL={pnl:.2f}")
                time.sleep(1.5)

                active_trade.update({"exit_time": idx, "exit_z": z, "pnl": pnl})
                trades.append(active_trade)
                active_trade = None
                position = 0

        backtest_df.at[idx, "pos"] = position

    backtest_df["pnl"] = (
        backtest_df["pos"].shift(1) *
        (backtest_df["s1"].diff() - hedge_ratio * backtest_df["s2"].diff())
    ) * POINT_VALUE

    backtest_df["cum_pnl"] = backtest_df["pnl"].cumsum()

    print("[INFO] Backtest complete.....:)")
    time.sleep(1.5)
    return backtest_df, pd.DataFrame(trades)

# ---------------------------------------------------
# Z-score Rolling Window and Entry/Exit Thresholds
# ---------------------------------------------------
def parameter_sweep(df, hedge_ratio,
                    entry_list =[1.5, 2.0, 2.5],
                    z_windows  =[15, 20, 40, 60],
                    stop_list  =[3.0, 3.5, 4.0]):

    print("\n========== PARAMETER TEST START ==========\n")
    results = []

    for zw in z_windows:
        for ent in entry_list:
            for st in stop_list:
                print(f"\n[RUN] ZW={zw} | ENTRY={ent} | STOP={st}")

                backtest_df, trades_df = run_backtest(
                    df,
                    hedge_ratio,
                    z_window=zw,
                    entry_thr=ent,
                    stop_thr=st,
                    exit_thr=0
                )

                final_pnl = backtest_df["cum_pnl"].iloc[-1]
                trades = len(trades_df)
                winrate = (trades_df["pnl"] > 0).mean() if trades > 0 else 0

                results.append({
                    "Z-Window": zw,
                    "Entry": ent,
                    "Stop": st,
                    "PnL": final_pnl,
                    "Trades": trades,
                    "WinRate": winrate
                })

    print("\n========== PARAMETER SWEEP DONE ==========\n")
    return pd.DataFrame(results)


#===========================
# MAIN
#===========================
def main():
    print("\n========== PAIRS TRADING SYSTEM ==========\n")
    time.sleep(1.5)

    raw = download_data(RIC_1, RIC_2)
    if raw is None:
        print("[EXIT] No raw data.")
        return

    clean = clean_columns(raw, RIC_1, RIC_2)
    bars_15m = resample_bars(clean)

    hedge = compute_hedge_ratio(bars_15m["close_1"], bars_15m["close_2"])
    if hedge is None:
        print("[EXIT] No hedge ratio.")
        return
    
    # ---------------- test with muti thresholds to get best results  ----------------
    print("\nRun parameter optimization? (y/n): ", end="") # y = it will test in different thresholds to get best results 
    choice = input().strip().lower()                       # n = normal backtest with default thresholds

    if choice == "y":
        sweep_df = parameter_sweep(bars_15m, hedge)

        print("\n===== OPTIMIZATION RESULTS =====")
        print(sweep_df.sort_values(by="PnL", ascending=False))

        sweep_output = r"C:\Users\admin\Documents\vs code\pairs_parameter_sweep.xlsx"
        sweep_df.to_excel(sweep_output, index=False)
        print(f"\nSaved sweep results: {sweep_output}")

        print("\nContinuing with normal backtest...\n")

    backtest_df, trades_df = run_backtest(bars_15m, hedge)

    print("\n========== BACKTEST SUMMARY ==========")
    print("Total PnL:", backtest_df["cum_pnl"].iloc[-1])
    print("Trades    :", len(trades_df))
    print("Win Rate  :", (trades_df["pnl"] > 0).mean())
    time.sleep(1.5)

    print("\nTrade Log:")
    print(trades_df)
    time.sleep(1.5)

    try:
        output_file = r"C:\Users\admin\Documents\vs code\pairs_backtest_output.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            raw.to_excel(writer, sheet_name="Raw_Data")
            clean.to_excel(writer, sheet_name="Clean_Data")
            bars_15m.to_excel(writer, sheet_name="Bars_15min")
            backtest_df.to_excel(writer, sheet_name="Backtest")
            trades_df.to_excel(writer, sheet_name="Trades")

        print(f"\n<------- Excel saved:--------> {output_file}")
        time.sleep(1.5)
    except Exception as e:
        print("<------- Failed to save Excel:------->", e)
        time.sleep(1.5)

    plt.figure(figsize=(12, 6))
    plt.plot(backtest_df["cum_pnl"])
    plt.title("Cumulative PnL")
    plt.show()


if __name__ == "__main__":
    main()
