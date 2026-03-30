import pandas as pd

df = pd.read_csv('D:\Data 2\ES_NQ D.csv')

df.fillna(inplace = True)

print(df.to_string())