import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
import io


# ==========================
# CONFIG
# ==========================

CSV_FILE = r"D:\data 3\CL_BR 1.csv"
OUTPUT_PATH = r"D:\ARB_PROJECT1\CL_BR PCA_RESULTS 15min.xlsx"

ROLLING_WINDOW = 150

ENTRY_Z = 2.0
EXIT_Z = 1.5
STOP_Z = 4.0

MAX_HOLD = 20
MAX_LOSS_PER_TRADE = -1500

CL_MULT = 1000   # crude oil multiplier (check your contract)
BR_MULT = 1000   # brent multiplier (adjust if needed)

TCOST = 5

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(CSV_FILE, parse_dates=["Date(GMT)"])
df.set_index("Date(GMT)", inplace=True)

# 🔥 CHANGE HERE (COLUMN NAMES)
df["CL"] = (df["CL High"] + df["CL Low"]) / 2
df["BR"] = (df["BR High"] + df["BR Low"]) / 2

df = df[["CL", "BR"]].dropna()

# ==========================
# VARIABLES
# ==========================

position = 0
trade_log = []
equity = 0
equity_curve = []

exit_counts = {
    "Hard Stop Loss": 0,
    "Mean Reversion": 0,
    "Z Stop": 0,
    "Time Exit": 0
}

print("\n\033[1m=== PCA STAT ARB (CL vs BR) STARTED ===\033[0m\n")

# ==========================
# LOOP
# ==========================

for i in range(ROLLING_WINDOW, len(df)):

    window = np.log(df.iloc[i - ROLLING_WINDOW:i][["CL", "BR"]])

    scaler = StandardScaler()
    X = scaler.fit_transform(window)

    pca = PCA(n_components=1)
    factor = pca.fit_transform(X).flatten()

    # regression
    beta_cl = np.polyfit(factor, window["CL"], 1)
    pred_cl = beta_cl[0] * factor + beta_cl[1]

    beta_br = np.polyfit(factor, window["BR"], 1)
    pred_br = beta_br[0] * factor + beta_br[1]

    # spread
    res_cl = window["CL"].values - pred_cl
    res_br = window["BR"].values - pred_br
    spread = res_cl - res_br

    mean = spread.mean()
    std = spread.std()

    if std == 0:
        continue

    z = (spread[-1] - mean) / std

    date = df.index[i]
    cl_price = df.iloc[i]["CL"]
    br_price = df.iloc[i]["BR"]

    # ==========================
    # ENTRY
    # ==========================

    if position == 0:

        if z > ENTRY_Z:
            position = -1
            entry = (date, cl_price, br_price, i, "SHORT")
            print(f"{date} | \033[91mSHORT CL LONG BR\033[0m | Z={z:.2f}")

        elif z < -ENTRY_Z:
            position = 1
            entry = (date, cl_price, br_price, i, "LONG")
            print(f"{date} | \033[92mLONG CL SHORT BR\033[0m | Z={z:.2f}")

    # ==========================
    # EXIT
    # ==========================

    else:

        holding = i - entry[3]

        cl_pnl = (cl_price - entry[1]) * CL_MULT * position
        br_pnl = (br_price - entry[2]) * BR_MULT * position

        pnl = cl_pnl - br_pnl - TCOST

        exit_flag = False

        if pnl <= MAX_LOSS_PER_TRADE:
            pnl = MAX_LOSS_PER_TRADE
            reason = "Hard Stop Loss"
            exit_flag = True

        elif abs(z) < EXIT_Z:
            reason = "Mean Reversion"
            exit_flag = True

        elif abs(z) > STOP_Z:
            reason = "Z Stop"
            exit_flag = True

        elif holding > MAX_HOLD:
            reason = "Time Exit"
            exit_flag = True

        if exit_flag:

            exit_counts[reason] += 1
            equity += pnl
            equity_curve.append(equity)

            color = "\033[92m" if pnl > 0 else "\033[91m"

            print(f"{date} | \033[93mEXIT\033[0m | {reason} | {color}PnL={pnl:.2f}\033[0m | Equity={equity:.2f}")

            trade_log.append({
                "Entry Date": entry[0],
                "Exit Date": date,
                "Direction": entry[4],
                "Entry CL": entry[1],
                "Exit CL": cl_price,
                "Entry BR": entry[2],
                "Exit BR": br_price,
                "Holding Bars": holding,
                "Exit Reason": reason,
                "PnL": pnl,
                "Equity": equity
            })

            position = 0


# ==========================
# SUMMARY
# ==========================

trades_df = pd.DataFrame(trade_log)

if trades_df.empty:
    print("\n No trades executed")
else:
    pnl = trades_df["PnL"]
    total_pnl = pnl.sum()
    max_profit = pnl.max()
    max_loss = pnl.min()
    equity_series = pnl.cumsum()
    drawdown = equity_series - equity_series.cummax()
    max_drawdown = drawdown.min()
    max_runup = equity_series.max()
    total_positive_trades = (pnl > 0).sum()
    total_negative_trades = (pnl < 0).sum()
    num_of_trades = len(pnl)
    success_rate = (total_positive_trades / num_of_trades) * 100

    summary_dict = {
        "Metric": [
            "Total PnL", "Max Profit", "Max Loss", "Max Drawdown", "Max Run-up",
            "Positive Trades", "Negative Trades", "Total Trades", "Success Rate", "Hard Stop Count", "Mean Reversion Count",
            "Z Stop Count", "Time Exit Count"
        ],
        "Value": [
            total_pnl, max_profit, max_loss, max_drawdown, max_runup,
            total_positive_trades, total_negative_trades, num_of_trades, success_rate,
            exit_counts["Hard Stop Loss"],
            exit_counts["Mean Reversion"],
            exit_counts["Z Stop"],
            exit_counts["Time Exit"]
        ]
    }
    summary_df = pd.DataFrame(summary_dict)

# ==========================
# SAVE TO EXCEL
# ==========================

with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
    trades_df.to_excel(writer, sheet_name="Trades", index=False)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

    # ==========================
    # SAVE CHARTS AS IMAGE IN EXCEL
    # ==========================
    fig, ax = plt.subplots(2, 1, figsize=(8, 6))
    ax[0].plot(equity_series)
    ax[0].set_title("Equity Curve")
    ax[1].plot(drawdown)
    ax[1].set_title("Drawdown")
    plt.tight_layout()

    # save to BytesIO buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close(fig)
    img_buffer.seek(0)

    # load workbook and add image
    book = writer.book
    ws = book.create_sheet("Charts")
    img = Image(img_buffer)
    ws.add_image(img, "A1")
    # writer.save()

print(f"\n✅ Saved results to: {OUTPUT_PATH}")