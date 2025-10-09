from sklearn.cluster import KMeans
import pandas as pd

data = pd.DataFrame({
    'Income': [15, 16, 17, 45, 46, 47],
    'Spending': [39, 40, 41, 80, 81, 82]
})

kmeans = KMeans(n_clusters=2, random_state=0).fit(data)
data['Cluster'] = kmeans.labels_

print(data)
