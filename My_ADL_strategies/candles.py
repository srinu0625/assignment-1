import eikon as ek
import pandas as pd
import datetime
 
# Set Eikon API Key
ek.set_app_key('7124cc602cee484ab6297f9468d491c9f585afdd')
 
# Define instrument and time window
instrument = '.SPX'  # You can try 'ESc1' if this fails
start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%dT09:15:00')
end_date = datetime.datetime.now().strftime('%Y-%m-%dT15:30:00')
 
# Fetch 1-minute datas
df = ek.get_timeseries(
    instrument,
    interval='minute',
    start_date=start_date,
    end_date=end_date,
    fields='*'
)
 
# Clean and process data
if df is not None and not df.empty:
    df.reset_index(inplace=True)
    df.rename(columns={df.columns[0]: 'datetime'}, inplace=True)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
 
    # Keep only the columns that exist
    expected_cols = ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']
    available_cols = [col for col in expected_cols if col in df.columns]
    df = df[available_cols].dropna()
    df.columns = [col.lower() for col in df.columns]
 
    print(df.head())
else:
    print("❌ No data returned.")