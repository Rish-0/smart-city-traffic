import pickle
import numpy as np

data = pickle.load(open('Dataset/adj_METR-LA.pkl', 'rb'), encoding='latin1')
# Item 0: list of sensor IDs
# Item 1: dict (sensor_id -> index mapping)
# Item 2: ndarray (207,207) adjacency matrix

print("Sensor IDs (first 10):", data[0][:10])
print("Sensor count:", len(data[0]))
print("Dict sample (first 5):", dict(list(data[1].items())[:5]))
print("Adjacency matrix shape:", data[2].shape)
print("Adjacency matrix sample (5x5):")
print(data[2][:5, :5])
print("Non-zero entries:", np.count_nonzero(data[2]))
print("Max value:", data[2].max())
print("Min non-zero value:", data[2][data[2] > 0].min() if np.any(data[2] > 0) else "N/A")

# Check CSV
import pandas as pd
csv_df = pd.read_csv('traffic_simulation.csv')
print("\n--- CSV Data ---")
print("Shape:", csv_df.shape)
print("Columns:", list(csv_df.columns))
print(csv_df.head(3))
