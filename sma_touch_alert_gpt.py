import pandas as pd
from tabulate import tabulate
from datetime import datetime
import time

FILES={
    "60min":r"D:\Data\CL 60min.csv",
    "240min":r"D:\Data\CL 240min.csv",
    "Daily":r"D:\Data\CL Daily.csv",
}

SMA_PERIODS=[50,100,200]

COL_MAP={
    "date":"Date",
    "open":"Open",
    "high":"High",
    "low":"Low",
    "close":"Close",
}

PRINT_DELAY= 1

def load_csv(file_path:str,tf_label:str)->pd.DataFrame:
    try:
        df=pd.read_csv(file_path)
        df.columns=df.columns.str.strip()
        rename={v:k for k,v in COL_MAP.items()}
        df.rename(columns=rename,inplace=True)

        if "date" in df.columns:
            df["date"]=pd.to_datetime(df["date"],errors="coerce")
            df.dropna(subset=["date"],inplace=True)
            df.sort_values("date",inplace=True)
            df.set_index("date",inplace=True)
            df.index=pd.to_datetime(df.index)

        for col in ["open","high","low","close"]:
            df[col]=pd.to_numeric(df[col],errors="coerce")
        df.dropna(subset=["high","low","close"],inplace=True)

        print(f"✓ Loaded [{tf_label}] {len(df)} bars → {file_path}")
        return df

    except Exception as e:
        print(f"✗ Error [{tf_label}] : {e}")
        return pd.DataFrame()

def compute_sma(series:pd.Series,period:int):
    return series.rolling(window=period,min_periods=period).mean()

def sma_touch(df:pd.DataFrame,sma_period:int):
    sma=compute_sma(df["close"],sma_period)
    touched=(df["low"]<=sma)&(df["high"]>=sma)
    return touched,sma

def scan_latest(dataframes:dict):
    alerts=[]
    for tf_label,df in dataframes.items():
        if df.empty:
            continue

        for sma_period in SMA_PERIODS:
            touched_s,sma_s=sma_touch(df,sma_period)
            if bool(touched_s.iloc[-1]):

                alerts.append({
                    "time":str(df.index[-1])[:16],
                    "timeframe":tf_label,
                    "sma_period":sma_period,
                    "sma_value":round(float(sma_s.iloc[-1]),4),
                    "high":round(float(df["high"].iloc[-1]),4),
                    "low":round(float(df["low"].iloc[-1]),4),
                    "close":round(float(df["close"].iloc[-1]),4),
                })

    return alerts

def print_status_table(dataframes:dict):
    rows=[]
    for tf_label,df in dataframes.items():

        if df.empty:
            continue

        for sp in SMA_PERIODS:
            touched_s,sma_s=sma_touch(df,sp)

            rows.append({
                "Timeframe":tf_label,
                "SMA":sp,
                "SMA Value":round(float(sma_s.iloc[-1]),4),
                "High":round(float(df["high"].iloc[-1]),4),
                "Low":round(float(df["low"].iloc[-1]),4),
                "Close":round(float(df["close"].iloc[-1]),4),
                "Touch?":"✅ YES" if touched_s.iloc[-1] else "❌ NO"
            })

    print(tabulate(rows,headers="keys",tablefmt="pretty"))

def backtest_all(dataframes:dict):

    rows=[]

    print("\n"+"="*120)
    print("FULL HISTORICAL SMA SCAN")
    print("="*120)

    for tf_label,df in dataframes.items():

        if df.empty:
            continue

        print(f"\nScanning → {tf_label}")
        for i in range(max(SMA_PERIODS),len(df)):
            current_bar=df.iloc[i]
            current_time=df.index[i]

            for sma_period in SMA_PERIODS:

                sma_series=compute_sma(df["close"].iloc[:i+1],sma_period)
                sma_value=sma_series.iloc[-1]
                if pd.isna(sma_value):
                    continue

                high_price=float(current_bar["high"])
                low_price=float(current_bar["low"])
                close_price=float(current_bar["close"])
                touched=low_price<=sma_value<=high_price
                status="✅ TOUCHED" if touched else "❌ NO TOUCH"

                print(
                    f"{str(current_time)[:16]} | "
                    f"{tf_label:7s}       | "
                    f"SMA {sma_period:3d} | "
                    f"SMA={sma_value:9.4f}| "
                    f"H={high_price:9.4f} | "
                    f"L={low_price:9.4f}  | "
                    f"C={close_price:9.4f}| "
                    f"{status}"
                )

                if touched:

                    rows.append({
                        "Time":current_time,
                        "Timeframe":tf_label,
                        "SMA":sma_period,
                        "SMA Value":round(sma_value,4),
                        "High":round(high_price,4),
                        "Low":round(low_price,4),
                        "Close":round(close_price,4),
                    })

                time.sleep(PRINT_DELAY)
    result=pd.DataFrame(rows)

    if not result.empty:

        result["Time"]=pd.to_datetime(result["Time"])
        result.sort_values(
            "Time",
            ascending=False,
            inplace=True
        )

        result.reset_index(
            drop=True,
            inplace=True
        )
    return result

def print_backtest_results(result:pd.DataFrame):
    if result.empty:
        print("No touches found.")
        return

    summary=(
        result.groupby(["Timeframe","SMA"])
        .size()
        .reset_index(name="Touches")
    )

    print("\nSUMMARY\n")

    print(
        tabulate(
            summary,
            headers="keys",
            tablefmt="simple",
            showindex=False
        )
    )

    recent=result.head(30).copy()
    recent["Time"]=pd.to_datetime(
        recent["Time"]
    ).dt.strftime("%Y-%m-%d %H:%M")
    print("\nMOST RECENT 30 TOUCHES\n")

    print(
        tabulate(
            recent,
            headers="keys",
            tablefmt="simple",
            showindex=False
        )
    )

    ts=datetime.now().strftime("%Y%m%d_%H%M%S")
    out=f"sma_touch_backtest_{ts}.csv"
    result.to_csv(out,index=False)
    print(f"\nSaved → {out}")

def main():

    print("\n"+"="*60)
    print("SMA Touch Alert | Local CSV Mode")
    print("="*60)
    print("\nLoading files ...")

    dataframes={
        tf:load_csv(path,tf)
        for tf,path in FILES.items()
    }

    print("\n"+"="*60)
    print_status_table(dataframes)
    print("\nChecking latest alerts...\n")
    alerts=scan_latest(dataframes)

    if alerts:
        print("🔔 ALERTS TRIGGERED\n")
        for a in alerts:

            print(
                f"{a['time']} | "
                f"{a['timeframe']:7s} | "
                f"SMA {a['sma_period']:3d} = "
                f"{a['sma_value']:.4f} | "
                f"H={a['high']:.4f} | "
                f"L={a['low']:.4f} | "
                f"C={a['close']:.4f}"
            )

    else:
        print("No latest SMA touches.")
    print("\n"+"="*60)
    result=backtest_all(dataframes)
    print_backtest_results(result)
    print("\n"+"="*60)

if __name__=="__main__":
    main()


