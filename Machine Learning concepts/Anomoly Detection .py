from sklearn.ensemble import IsolationForest
import pandas as pd

data = pd.DataFrame({'SensorValue': [10, 11, 10, 12, 200, 11, 10]})

model = IsolationForest(contamination=0.1, random_state=0)
model.fit(data)

data['Anomaly'] = model.predict(data)
print(data)
# -1 = anomaly, 1 = normal
