import pandas_datareader.data as web

df = web.DataReader("^SPX", "stooq")   # S&P 500 index
print(df.head())
