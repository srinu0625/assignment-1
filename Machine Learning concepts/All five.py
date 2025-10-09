# ==========================================
# MACHINE LEARNING PREDICTIVE MODEL DEMO
# Covers 5 major types:
# 1. Regression
# 2. Classification
# 3. Time Series Forecasting
# 4. Clustering
# 5. Anomaly Detection
# ==========================================

import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
import warnings

warnings.filterwarnings("ignore")  # clean output

print("\n============================")
print("1️⃣  REGRESSION MODEL")
print("============================")
# Predict continuous value (house price)
data_reg = pd.DataFrame({
    'Size': [1000, 1500, 1800, 2400, 3000],
    'Rooms': [2, 3, 3, 4, 5],
    'Price': [100, 150, 180, 240, 300]
})
X_reg = data_reg[['Size', 'Rooms']]
y_reg = data_reg['Price']
model_reg = LinearRegression().fit(X_reg, y_reg)
pred_reg = model_reg.predict(pd.DataFrame({'Size': [2000], 'Rooms': [3]}))
print(f"Predicted Price for 2000 sqft, 3 rooms: {pred_reg[0]:.2f}")

# ==========================================

print("\n============================")
print("2️⃣  CLASSIFICATION MODEL")
print("============================")
# Predict discrete category (pass/fail)
data_cls = pd.DataFrame({
    'Hours_Studied': [1, 2, 3, 4, 5, 6],
    'Passed': [0, 0, 0, 1, 1, 1]
})
X_cls = data_cls[['Hours_Studied']]
y_cls = data_cls['Passed']
model_cls = LogisticRegression().fit(X_cls, y_cls)
pred_cls = model_cls.predict(pd.DataFrame({'Hours_Studied': [3.5]}))
print(f"Predicted result for 3.5 study hours: {'Pass' if pred_cls[0] == 1 else 'Fail'}")

# ==========================================

print("\n============================")
print("3️⃣  TIME SERIES MODEL")
print("============================")
# Predict future value based on historical trend
sales = pd.DataFrame({
    'Month': [1, 2, 3, 4, 5, 6],
    'Sales': [200, 220, 250, 270, 300, 330]
})
X_ts = sales[['Month']]
y_ts = sales['Sales']
model_ts = LinearRegression().fit(X_ts, y_ts)
next_month = 7
pred_sales = model_ts.predict(pd.DataFrame({'Month': [next_month]}))
print(f"Predicted sales for month {next_month}: {pred_sales[0]:.2f}")

# ==========================================

print("\n============================")
print("4️⃣  CLUSTERING MODEL")
print("============================")
# Group similar data points (customers)
data_clust = pd.DataFrame({
    'Income': [15, 16, 17, 45, 46, 47],
    'Spending': [39, 40, 41, 80, 81, 82]
})
kmeans = KMeans(n_clusters=2, random_state=0).fit(data_clust)
data_clust['Cluster'] = kmeans.labels_
print("Customer clusters:\n", data_clust)

# ==========================================

print("\n============================")
print("5️⃣  ANOMALY DETECTION MODEL")
print("============================")
# Identify unusual data points
data_ano = pd.DataFrame({'SensorValue': [10, 11, 10, 12, 200, 11, 10]})
iso = IsolationForest(contamination=0.1, random_state=0)
iso.fit(data_ano)
data_ano['Anomaly'] = iso.predict(data_ano)
print("Anomaly detection results (-1 = anomaly):\n", data_ano)

print("\n✅ All 5 model types executed successfully!\n")
