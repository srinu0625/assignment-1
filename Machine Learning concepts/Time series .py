import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

# Simulated monthly sales
sales = pd.DataFrame({
    'Month': [1, 2, 3, 4, 5, 6],
    'Sales': [200, 220, 250, 270, 300, 330]
})

X = sales[['Month']]
y = sales['Sales']

model = LinearRegression().fit(X, y)
next_month = 7
print("Predicted sales for month 7:", model.predict([[next_month]])[0])
