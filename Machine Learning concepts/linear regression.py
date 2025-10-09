from sklearn.linear_model import LinearRegression
import pandas as pd

# Sample data
data = pd.DataFrame({
    'Size': [1000, 1500, 1800, 2400, 3000],
    'Price': [100, 150, 180, 240, 300]
})

X = data[['Size']]
y = data['Price']

model = LinearRegression()
model.fit(X, y)

print("Predicted Price for 2000 sqft:", model.predict([[2000]])[0])
