import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
import io
import time 

# ==========================
# CONFIG
# ==========================
CSV_FILE    = r"D:\data 3\CL_BR 15.csv"
OUTPUT_PATH = r"D:\ARB_PROJECT1\CL_BR_UPDATED___15min___.xlsx"

ROLLING_WINDOW = 200

#  Z OPTIMIZATION LIST
Z_LIST = [0.5, 1, 1.5, 2, 2.5, 3]
RESULT_MATRIX  = []
SUMMARY_MATRIX = []

MAX_HOLD           = 20
MAX_LOSS_PER_TRADE = -2000   # CL/BR are $1000/pt each — wider loss buffer vs ES/NQ

# CL  = WTI Crude Oil  → $1,000 per $1.00 move  (1000 barrels/contract)
# BR  = Brent Crude    → $1,000 per $1.00 move  (1000 barrels/contract)
CL_MULT = 1000
BR_MULT = 1000

TCOST             = 25.0    # CL + BR round-turn realistic commission ($12-13/side)
ADF_PVALUE_THRESH = 0.05

# ── FILTERS ───────────────────────────────────────────────────
MIN_HALF_LIFE  = 3      # bars
MAX_HALF_LIFE  = 35     # bars
MIN_CORR       = 0.85   # CL/BR are near-twins — raise bar vs ES/NQ (was 0.75)
CORR_WINDOW    = 60     # bars for rolling correlation
CONFIRM_BARS   = 2      # z must hold above threshold this many bars before entry
PEAK_PULLBACK  = 0.15   # z must retrace this much from peak before entering
# ──────────────────────────────────────────────────────────────

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

for sym in ["CL", "BR"]:
    if f"{sym} Close" in df.columns:
        df[sym] = df[f"{sym} Close"]
    else:
        df[sym] = (df[f"{sym} High"] + df[f"{sym} Low"]) / 2
        print(f"[WARN] {sym}: using mid-price — prefer Close")

df = df[["CL", "BR"]].dropna()
log_df = np.log(df)

# ── PRE-COMPUTE rolling correlation ───────────────────────────
log_df["rolling_corr"] = log_df["CL"].rolling(CORR_WINDOW).corr(log_df["BR"])
# ──────────────────────────────────────────────────────────────

print("\n\033[1m=== CL/BR PCA STAT ARB v3 (HIGH WIN RATE) ===\033[0m\n")

# ==========================
#  OPEN EXCEL WRITER
# ==========================
writer = pd.ExcelWriter(OUTPUT_PATH.replace(".xlsx", "_FIXED.xlsx"), engine="openpyxl")

# ==========================
#  MAIN OPTIMIZATION LOOP
# ==========================

for ENTRY_Z in Z_LIST:

    EXIT_Z = ENTRY_Z * 0.5
    STOP_Z = ENTRY_Z * 1.5

    print(f"\n\n\033[96m===== RUNNING FOR Z = {ENTRY_Z} =====\033[0m\n")

    # RESET VARIABLES
    position     = 0
    entry        = None
    trade_log    = []
    equity       = 0
    equity_curve = []
    skipped_adf  = 0
    skipped_hl   = 0
    skipped_corr = 0
    bar_count    = 0
    z_prev       = 0

    # Confirmation state for reversal entry
    confirm_dir   = 0
    confirm_count = 0
    z_peak        = 0.0

    exit_counts = {
        "Hard Stop Loss": 0,
        "Mean Reversion": 0,
        "Z Stop":         0,
        "Time Exit":      0,
    }

    # ===== MAIN LOOP =====
    for i in range(ROLLING_WINDOW, len(df)):

        # Get log prices for window
        window_log = log_df.iloc[i - ROLLING_WINDOW:i]
        window_cl  = window_log["CL"].values
        window_br  = window_log["BR"].values

        # Regress CL on BR
        X     = sm.add_constant(window_br)
        model = OLS(window_cl, X).fit()
        beta  = model.params[1]
        alpha = model.params[0]

        # Spread calculation
        spread = window_cl - beta * window_br

        # ADF test on spread
        try:
            adf_p = adfuller(spread, autolag="AIC")[1]
        except Exception:
            adf_p = 1.0

        if adf_p > ADF_PVALUE_THRESH:
            skipped_adf  += 1
            z_prev        = 0
            confirm_dir   = 0
            confirm_count = 0
            continue

        # Half-life check
        spread_lag = spread[:-1]
        delta      = np.diff(spread)
        if len(delta) > 10 and np.std(spread_lag) > 0:
            try:
                hl_model  = OLS(delta, sm.add_constant(spread_lag)).fit()
                theta     = hl_model.params[1]
                half_life = -np.log(2) / theta if theta < 0 else np.inf
            except Exception:
                half_life = np.inf
        else:
            half_life = np.inf

        if half_life < MIN_HALF_LIFE or half_life > MAX_HALF_LIFE:
            skipped_hl   += 1
            z_prev        = 0
            confirm_dir   = 0
            confirm_count = 0
            continue

        # Correlation filter — CL/BR must be tightly linked
        corr = log_df["rolling_corr"].iloc[i]
        if np.isnan(corr) or corr < MIN_CORR:
            skipped_corr += 1
            z_prev        = 0
            confirm_dir   = 0
            confirm_count = 0
            continue

        bar_count += 1

        # No look-ahead bias — use past spread only
        past_spread = spread[:-1]
        mean = past_spread.mean()
        std  = past_spread.std()

        if std == 0 or np.isnan(std):
            continue

        z = (spread[-1] - mean) / std

        # Current prices
        date     = df.index[i]
        cl_price = df.iloc[i]["CL"]
        br_price = df.iloc[i]["BR"]

        # Dollar hedge ratio
        # Both multipliers are $1000, so ratio = abs(beta) * (CL_MULT / BR_MULT) = abs(beta)
        dollar_hedge_ratio = abs(beta) * (CL_MULT / BR_MULT)

        if position == 0:

            # ── REVERSAL CONFIRMATION ENTRY ───────────────────
            # 1) z crosses threshold  → start counting
            # 2) z holds CONFIRM_BARS → not a spike
            # 3) z retraces PEAK_PULLBACK from peak → reversal confirmed
            # ──────────────────────────────────────────────────

            if z >= ENTRY_Z:
                if confirm_dir == -1:
                    confirm_count += 1
                    z_peak = max(z_peak, z)
                else:
                    confirm_dir   = -1
                    confirm_count = 1
                    z_peak        = z

            elif z <= -ENTRY_Z:
                if confirm_dir == 1:
                    confirm_count += 1
                    z_peak = min(z_peak, z)
                else:
                    confirm_dir   = 1
                    confirm_count = 1
                    z_peak        = z

            else:
                confirm_dir   = 0
                confirm_count = 0
                z_peak        = 0.0

            if confirm_count >= CONFIRM_BARS:

                if confirm_dir == -1 and z < z_peak - PEAK_PULLBACK:
                    # Spread too high, peaked, turning down → SHORT CL / LONG BR
                    position = -1
                    entry    = (date, cl_price, br_price, bar_count, "SHORT", dollar_hedge_ratio, beta)
                    print(f"{date} | \033[91mSHORT CL LONG BR\033[0m | Z={z:.2f} | Peak={z_peak:.2f} | Beta={beta:.3f} | HL={half_life:.1f} | Corr={corr:.2f}")
                    confirm_dir = 0; confirm_count = 0; z_peak = 0.
                    time.sleep(5)  # slight pause to differentiate entry printouts

                elif confirm_dir == 1 and z > z_peak + PEAK_PULLBACK:
                    # Spread too low, troughed, turning up → LONG CL / SHORT BR
                    position = 1
                    entry    = (date, cl_price, br_price, bar_count, "LONG", dollar_hedge_ratio, beta)
                    print(f"{date} | \033[92mLONG CL SHORT BR\033[0m | Z={z:.2f} | Peak={z_peak:.2f} | Beta={beta:.3f} | HL={half_life:.1f} | Corr={corr:.2f}")
                    confirm_dir = 0; confirm_count = 0; z_peak = 0.0
                    time.sleep(5)  # slight pause to differentiate entry printouts

        else:
            holding    = bar_count - entry[3]
            hr         = entry[5]
            entry_beta = entry[6]

            if entry[4] == "LONG":
                # Long CL, Short BR
                cl_pnl = (cl_price - entry[1]) * CL_MULT
                br_pnl = (entry[2] - br_price) * BR_MULT * hr
            else:
                # Short CL, Long BR
                cl_pnl = (entry[1] - cl_price) * CL_MULT
                br_pnl = (br_price - entry[2]) * BR_MULT * hr

            pnl = cl_pnl + br_pnl - TCOST

            exit_flag = False

            if pnl <= MAX_LOSS_PER_TRADE:
                pnl       = MAX_LOSS_PER_TRADE
                reason    = "Hard Stop Loss"
                exit_flag = True

            elif abs(z) < EXIT_Z:
                reason    = "Mean Reversion"
                exit_flag = True

            elif abs(z) > STOP_Z:
                reason    = "Z Stop"
                exit_flag = True

            elif holding > MAX_HOLD:
                reason    = "Time Exit"
                exit_flag = True

            if exit_flag:
                exit_counts[reason] += 1
                equity += pnl
                equity_curve.append(equity)

                color = "\033[92m" if pnl > 0 else "\033[91m"
                print(f"{date} | \033[93mEXIT\033[0m | {reason} | {color}PnL=${pnl:.2f}\033[0m | Equity=${equity:.2f}")

                trade_log.append({
                    "Entry Date":   entry[0],
                    "Exit Date":    date,
                    "Direction":    entry[4],
                    "Entry CL":     entry[1],
                    "Exit CL":      cl_price,
                    "Entry BR":     entry[2],
                    "Exit BR":      br_price,
                    "Hedge Ratio":  round(hr, 4),
                    "Beta":         round(entry_beta, 4),
                    "Half Life":    round(half_life, 1),
                    "Corr":         round(corr, 3),
                    "Holding Bars": holding,
                    "Exit Reason":  reason,
                    "CL PnL":       round(cl_pnl, 2),
                    "BR PnL":       round(br_pnl, 2),
                    "PnL":          round(pnl, 2),
                    "Equity":       round(equity, 2),
                })
                position = 0

        # Store z for next bar
        z_prev = z

    # ===== SUMMARY =====
    trades_df = pd.DataFrame(trade_log)

    if trades_df.empty:
        print(f"\nNo trades executed for Z={ENTRY_Z}.")
        continue

    pnl           = trades_df["PnL"]
    equity_series = pnl.cumsum()
    drawdown      = equity_series - equity_series.cummax()
    z_name        = str(ENTRY_Z).replace('.', '_')

    trades_df.to_excel(writer, sheet_name=f"Z_{z_name}_Trades", index=False)

    total_pnl    = pnl.sum()
    max_profit   = pnl.max()
    max_loss     = pnl.min()
    max_drawdown = drawdown.min()
    max_runup    = equity_series.max()
    num_trades   = len(pnl)
    wins         = (pnl > 0).sum()
    losses       = (pnl < 0).sum()
    win_rate     = wins / num_trades * 100 if num_trades > 0 else 0
    avg_win      = pnl[pnl > 0].mean() if wins > 0 else 0
    avg_loss     = pnl[pnl < 0].mean() if losses > 0 else 0
    profit_factor = abs(pnl[pnl > 0].sum() / pnl[pnl < 0].sum()) if losses > 0 and pnl[pnl < 0].sum() != 0 else float("inf")
    sharpe        = (pnl.mean() / pnl.std()) * np.sqrt(26 * 252) if pnl.std() > 0 else 0

    # Sortino ratio
    downside_std = pnl[pnl < 0].std()
    sortino      = (pnl.mean() / downside_std) * np.sqrt(26 * 252) if downside_std > 0 else 0

    # Expected value per trade
    ev = (win_rate / 100) * avg_win + (1 - win_rate / 100) * avg_loss

    print(f"\n\033[1m{'='*55}\033[0m")
    print(f"  {'Total PnL':<25}: ${total_pnl:>10,.2f}")
    print(f"  {'Sharpe Ratio':<25}: {sharpe:>10.3f}")
    print(f"  {'Sortino Ratio':<25}: {sortino:>10.3f}")
    print(f"  {'Profit Factor':<25}: {profit_factor:>10.3f}")
    print(f"  {'Max Drawdown':<25}: ${max_drawdown:>10,.2f}")
    print(f"  {'Max Run-up':<25}: ${max_runup:>10,.2f}")
    print(f"  {'Total Trades':<25}: {num_trades:>10}")
    print(f"  {'Win Rate':<25}: {win_rate:>9.1f}%")
    print(f"  {'Avg Win':<25}: ${avg_win:>10,.2f}")
    print(f"  {'Avg Loss':<25}: ${avg_loss:>10,.2f}")
    print(f"  {'Exp Value / Trade':<25}: ${ev:>10,.2f}")
    print(f"  Bars skipped (ADF)  : {skipped_adf:,}")
    print(f"  Bars skipped (HL)   : {skipped_hl:,}")
    print(f"  Bars skipped (Corr) : {skipped_corr:,}")
    print(f"\n  Exit Breakdown:")
    for k, v in exit_counts.items():
        print(f"    {k:<20}: {v}")
    print(f"\033[1m{'='*55}\033[0m\n")

    SUMMARY_MATRIX.append({
        "Z":                   ENTRY_Z,
        "Total PnL":           round(total_pnl, 2),
        "Sharpe Ratio":        round(sharpe, 3),
        "Sortino Ratio":       round(sortino, 3),
        "Exp Value/Trade":     round(ev, 2),
        "Profit Factor":       round(profit_factor, 3),
        "Max Profit":          round(max_profit, 2),
        "Max Loss":            round(max_loss, 2),
        "Max Drawdown":        round(max_drawdown, 2),
        "Max Run-up":          round(max_runup, 2),
        "Winning Trades":      int(wins),
        "Losing Trades":       int(losses),
        "Total Trades":        num_trades,
        "Win Rate (%)":        round(win_rate, 2),
        "Avg Win":             round(avg_win, 2),
        "Avg Loss":            round(avg_loss, 2),
        "Hard Stop Count":     exit_counts["Hard Stop Loss"],
        "Mean Reversion Count":exit_counts["Mean Reversion"],
        "Z Stop Count":        exit_counts["Z Stop"],
        "Time Exit Count":     exit_counts["Time Exit"],
        "Bars Skipped (ADF)":  skipped_adf,
        "Bars Skipped (HL)":   skipped_hl,
        "Bars Skipped (Corr)": skipped_corr,
    })

    # Chart
    fig, ax = plt.subplots(3, 1, figsize=(10, 9))

    ax[0].plot(equity_series.values, color="#e07b00")
    ax[0].fill_between(range(len(equity_series)), equity_series.values, alpha=0.1, color="#e07b00")
    ax[0].set_title(f"Equity Curve  Z={ENTRY_Z}  |  WR={win_rate:.1f}%  |  PF={profit_factor:.2f}  |  Sharpe={sharpe:.2f}")
    ax[0].set_ylabel("Cumulative P&L ($)")
    ax[0].grid(alpha=0.3)

    ax[1].fill_between(range(len(drawdown)), drawdown.values, 0, alpha=0.5, color="red")
    ax[1].set_title(f"Drawdown  |  Max = ${max_drawdown:,.0f}")
    ax[1].set_ylabel("Drawdown ($)")
    ax[1].grid(alpha=0.3)

    ax[2].hist(pnl.values, bins=30, color="#e07b00", edgecolor="white", alpha=0.8)
    ax[2].axvline(0, color="red",    lw=1.5, linestyle="--", label="Break-even")
    ax[2].axvline(ev, color="black", lw=1.5, linestyle="--", label=f"EV=${ev:.0f}")
    ax[2].set_title("P&L Distribution per Trade")
    ax[2].set_xlabel("P&L ($)")
    ax[2].legend()

    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close(fig)
    img_buffer.seek(0)

    ws = writer.book.create_sheet(f"Z_{z_name}_Charts")
    img = Image(img_buffer)
    ws.add_image(img, "A1")

    # STORE MATRIX
    RESULT_MATRIX.append({
        "Z":        ENTRY_Z,
        "Trades":   num_trades,
        "WinRate":  round(win_rate, 2),
        "PnL":      round(total_pnl, 2),
        "Drawdown": round(max_drawdown, 2),
        "Sharpe":   round(sharpe, 3),
        "Sortino":  round(sortino, 3),
        "PF":       round(profit_factor, 3),
        "EV":       round(ev, 2),
    })

# ==========================
# FINAL MATRIX
# ==========================

result_df  = pd.DataFrame(RESULT_MATRIX)
summary_df = pd.DataFrame(SUMMARY_MATRIX)
summary_df.to_excel(writer, sheet_name="Summary", index=False)

print("\n\033[1m===== PERFORMANCE MATRIX =====\033[0m")
print(result_df.sort_values(by="PnL", ascending=False))

result_df.to_excel(writer, sheet_name="Z_Performance_Matrix", index=False)

# CLOSE FILE
writer.close()
print(f"\n\033[1mResults saved to: {OUTPUT_PATH.replace('.xlsx', '_FIXED.xlsx')}\033[0m")