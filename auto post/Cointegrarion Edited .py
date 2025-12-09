# Cointegration with parameter sweep for pairs trading strategy and backtest code

import eikon as ek
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
import matplotlib.pyplot as plt
import time

# Constants 
POINT_VALUE = 1000        # POINT VALUE EXPLANATION:  Point Value = how many dollars you gain or lose when the futures price moves by 1.00 point use correct value for each futures contract.
START_DATE = "2025-10-01"
END_DATE = "2025-11-08"
INTERVAL = "minute"

RIC_1 = "ESc1"
RIC_2 = "YMc1"

ek.set_app_key("92e0a59a8e994142bab0f82d8294e1df404da224")

# ---  parameters (defaults) ---
COMMISSION_PER_LEG = 2.5    # USD per leg per side (entry or exit). Round-trip per leg = 5. Two legs => 10.
SLIPPAGE_TICKS = 1.0        # ticks of slippage applied per side
TICK_ES = 0.25
TICK_YM = 1.0


# Download Data
def download_data(ric1, ric2):
    print(f"\n[INFO] Downloading data for {ric1} and {ric2}...")
    print(f"       Date range: {START_DATE} → {END_DATE}")
    print(f"       Interval  : {INTERVAL}")
    time.sleep(0.5)

    try:
        df = ek.get_timeseries(
            [ric1, ric2],
            start_date=START_DATE,
            end_date=END_DATE,
            interval=INTERVAL
        )

        if df is None:
            raise ValueError("Eikon returned None. Wrong RIC or expired contract.")

        if not isinstance(df, pd.DataFrame):
            raise ValueError("Unexpected data type returned from Eikon API.")

        if df.empty:
            raise ValueError("Eikon returned an empty DataFrame — no data in this date range.")

        print("[INFO] Raw data downloaded:", len(df), "rows")
        time.sleep(0.2)
        return df.dropna()

    except Exception as e:
        print("[ERROR] Download failed:", e)
        time.sleep(0.2)
        return None


# Clean MultiIndex Columns into Flat DF
def clean_columns(raw_df, ric1, ric2):
    print("\n[INFO] Cleaning columns...")
    time.sleep(0.2)

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
    time.sleep(0.2)
    return df.astype(float)


# Resample to 15-minute bars
def resample_bars(df):
    print("[INFO] Resampling to 15-minute bars...")
    time.sleep(0.2)

    rules = {
        'open_1': 'first', 'high_1': 'max', 'low_1': 'min', 'close_1': 'last', 'volume_1': 'sum',
        'open_2': 'first', 'high_2': 'max', 'low_2': 'min', 'close_2': 'last', 'volume_2': 'sum',
    }
    out = df.resample("15T").agg(rules).dropna()

    print("[INFO] Resampled rows:", len(out))
    time.sleep(0.2)
    return out


# Cointegration & Hedge Ratio
def compute_hedge_ratio(series1, series2):
    print("-----> Running cointegration test...")
    time.sleep(0.2)

    score, pvalue, _ = coint(series1, series2)
    print(f"-----> Cointegration p-value = {pvalue:.4f}")
    time.sleep(0.2)

    if pvalue >= 0.1:
        print("-----> Series NOT cointegrated. Exiting.\n")
        time.sleep(0.2)
        return None

    print("-----> Running OLS to compute hedge ratio...")
    time.sleep(0.2)

    X = sm.add_constant(series2)
    model = sm.OLS(series1, X).fit()
    hedge_ratio = model.params[series2.name]

    print(f"-----> Hedge Ratio = {hedge_ratio:.5f}")
    time.sleep(0.2)
    return hedge_ratio


# Helper: tick value selector
def tick_value_for_ric(ric):
    if ric.lower().startswith('esc') or 'es' in ric.lower():
        return TICK_ES
    if ric.lower().startswith('ym') or 'ym' in ric.lower():
        return TICK_YM
    return TICK_ES


# Backtest
def run_backtest(df, hedge_ratio,
                 z_window=30,
                 entry_thr=2,
                 stop_thr=4,
                 exit_thr=0):

    print("-----> Starting backtest...")
    print(f"       Hedge Ratio : {hedge_ratio:.5f}")
    print(f"       Z-window    : {z_window}")
    print(f"       Entry thr   : ±{entry_thr}")
    print(f"       Stop thr    : ±{stop_thr}")
    time.sleep(0.2)

    s1 = df["close_1"]
    s2 = df["close_2"]

    # LOOK-AHEAD FIX: use shifted rolling mean/std so only past bars are used for signal
    spread = s1 - hedge_ratio * s2
    spread_mean = spread.rolling(z_window).mean().shift(1)
    spread_std = spread.rolling(z_window).std().shift(1)
    zscore = (spread - spread_mean) / spread_std

    backtest_df = pd.DataFrame({"s1": s1, "s2": s2, "spread": spread, "z": zscore})
    backtest_df["pos"] = 0

    position = 0
    trades = []
    active_trade = None

    # Pre-calc slippage dollar values per side using tick values
    tick1 = tick_value_for_ric(RIC_1) * SLIPPAGE_TICKS
    tick2 = tick_value_for_ric(RIC_2) * SLIPPAGE_TICKS
    slippage_cost_per_side = (tick1 + tick2) * POINT_VALUE  # both legs slippage per side
    roundtrip_commission = COMMISSION_PER_LEG * 2 * 2  # two legs, entry+exit

    for i in range(1, len(backtest_df)):
        z = backtest_df["z"].iloc[i]
        idx = backtest_df.index[i]

        # ENTRY for LONG or SHORT
        if position == 0:
            if z < -entry_thr and not np.isnan(z):
                print(f"[LONG ENTRY] {idx} | Z={z:.2f}")
                time.sleep(0.01)
                position = 1
                # apply slippage to entry prices: buyer gets slightly worse price
                s1_e = backtest_df["s1"].iloc[i] + tick1
                s2_e = backtest_df["s2"].iloc[i] - tick2
                active_trade = {
                    "entry_time": idx,
                    "type": "long",
                    "entry_z": z,
                    "s1_e": s1_e,
                    "s2_e": s2_e
                }

            elif z > entry_thr and not np.isnan(z):
                print(f"[SHORT ENTRY] {idx} | Z={z:.2f}")
                time.sleep(0.01)
                position = -1
                s1_e = backtest_df["s1"].iloc[i] - tick1
                s2_e = backtest_df["s2"].iloc[i] + tick2
                active_trade = {
                    "entry_time": idx,
                    "type": "short",
                    "entry_z": z,
                    "s1_e": s1_e,
                    "s2_e": s2_e
                }

        # EXIT LONG
        elif position == 1:
            if (z >= exit_thr or z <= -stop_thr) and not np.isnan(z):
                # apply slippage at exit
                s1_x = backtest_df["s1"].iloc[i] - tick1
                s2_x = backtest_df["s2"].iloc[i] + tick2
                pnl = ((s1_x - active_trade["s1_e"]) - hedge_ratio * (s2_x - active_trade["s2_e"])) * POINT_VALUE

                # subtract realistic costs: slippage (both sides entry+exit) + commission
                total_slip_cost = slippage_cost_per_side * 2  # entry+exit
                pnl -= (total_slip_cost + roundtrip_commission)

                print(f"[LONG EXIT] {idx} | Z={z:.2f} | PnL={pnl:.2f}")
                time.sleep(0.01)

                active_trade.update({"exit_time": idx, "exit_z": z, "pnl": pnl})
                trades.append(active_trade)
                active_trade = None
                position = 0

        # EXIT SHORT
        elif position == -1:
            if (z <= exit_thr or z >= stop_thr) and not np.isnan(z):
                s1_x = backtest_df["s1"].iloc[i] + tick1
                s2_x = backtest_df["s2"].iloc[i] - tick2
                pnl = (-(s1_x - active_trade["s1_e"]) + hedge_ratio * (s2_x - active_trade["s2_e"])) * POINT_VALUE

                total_slip_cost = slippage_cost_per_side * 2
                pnl -= (total_slip_cost + roundtrip_commission)

                print(f"[SHORT EXIT] {idx} | Z={z:.2f} | PnL={pnl:.2f}")
                time.sleep(0.01)

                active_trade.update({"exit_time": idx, "exit_z": z, "pnl": pnl})
                trades.append(active_trade)
                active_trade = None
                position = 0

        backtest_df.at[idx, "pos"] = position

    # PnL stream using filled prices and positions from trades
    backtest_df["pnl"] = 0.0
    for t in trades:
        exit_idx = t["exit_time"]
        backtest_df.at[exit_idx, "pnl"] = t["pnl"]

    backtest_df["cum_pnl"] = backtest_df["pnl"].cumsum()

    print("[INFO] Backtest complete.....:)")
    time.sleep(0.2)
    return backtest_df, pd.DataFrame(trades)


# Z-score Rolling Window and Entry/Exit Thresholds
def parameter_sweep(df, hedge_ratio,
                    entry_list =[1.5, 2.0, 2.5],
                    z_windows  =[15, 20, 40, 60],
                    stop_list  =[3.0, 3.5, 4.0]):

    print("\n========== PARAMETER TEST START ==========")
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

    print("\n========== PARAMETER SWEEP DONE ==========")
    return pd.DataFrame(results)


#===========================
# MAIN
#===========================
def main():
    print("\n========== PAIRS TRADING SYSTEM ==========")
    time.sleep(0.2)

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
    print("\nRun parameter optimization? (y/n): ", end="") # y = it will test in defined thresholds to get best results 
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
    time.sleep(0.2)

    print("\nTrade Log:")
    print(trades_df)
    time.sleep(0.2)

    try:
        output_file = r"C:\Users\admin\Documents\vs code\pairs_backtest_output.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            raw.to_excel(writer, sheet_name="Raw_Data")
            clean.to_excel(writer, sheet_name="Clean_Data")
            bars_15m.to_excel(writer, sheet_name="Bars_15min")
            backtest_df.to_excel(writer, sheet_name="Backtest")
            trades_df.to_excel(writer, sheet_name="Trades")

        print(f"\n<------- Excel saved:--------> {output_file}")
        time.sleep(0.2)
    except Exception as e:
        print("<------- Failed to save Excel:------->", e)
        time.sleep(0.2)

    plt.figure(figsize=(12, 6))
    plt.plot(backtest_df["cum_pnl"])
    plt.title("Cumulative PnL")
    plt.show()


if __name__ == "__main__":
    main()
