from sklearn.linear_model import LogisticRegression
import pandas as pd

data = pd.DataFrame({
    'Hours_Studied': [1, 2, 3, 4, 5, 6],
    'Passed': [0, 0, 0, 1, 1, 1]
})

X = data[['Hours_Studied']]
y = data['Passed']

model = LogisticRegression()
model.fit(X, y)

print("Prediction for 3.5 hours:", model.predict([[3.5]])[0])
