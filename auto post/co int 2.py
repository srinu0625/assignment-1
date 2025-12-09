import time 
import eikon as ek 

START_DATE = '2023-01-01'
END_DATE   = '2024-01-01'
INTERVAL   = '15min'

RIC_1 = "NQZ25"
RIC_2 = "NQH26"


 
ek.set_app_key("92e0a59a8e994142bab0f82d8294e1df404da224")

def clean_columns(raw_df , ric1 , ric2):
    print("Cleaning columns...")
    time.sleep(1.5)

    if not isinstance(raw_df, pd.DataFrame):
        print("Input is not a DataFrame.")
        raise ValueError("Input must be a pandas DataFrame.")
    
    if not isinstance(raw_df, pd.DataFrame):
        raise ValueError("Unexpected datatype returned from Eikon API")
    if raw_df.empty:
        raise ValueError("Input DataFrame is empty.")
    
    try:

        raw_df.columns = pd.MultiIndex.from_tuples(
            [(col.split('.')[0], col.split('.')[1]) for col in raw_df.columns]
        )
        return raw_df    
    
    except Exception as e:
        print(f"An error occurred: {e}")
        raise ValueError('expected to multiindex OHLC format.')
        # Further processing...

print("clean data downloaded")

def download_data(ric1, ric2):
    print(f"Downloading data...for {ric1} and {ric2}")
    print(f"Data range:{START_DATE} , {END_DATE}")
    print(F'interval:{INTERVAL}ella')
    time.sleep(1.5)

def clean_columns(raw_df,ric1 , ric2):
    print('cleaning columns ')
    if not isinstance(raw_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame.")

def run_backtest(df, hedge_ratio, z_window = 30, entry_thr = 2 , stop_thr = 4):
    print("Running backtest...")

    time.sleep(1.5)
    s1 = df['close_1']    
    s2 = df['close_2']   

    spread = s1 - hedge_ratio * s2
    spread_mean = spread.rolling(window=z_window).mean()
    spread_std = spread.rolling(window=z_window).std()
    z_score = (spread - spread_mean) / spread_std

    backtest_df = pd.DataFrame({"spread": spread, "z_score": z_score})
    
