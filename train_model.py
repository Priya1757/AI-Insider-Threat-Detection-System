import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

# Load CSV file
data = pd.read_csv("valid.csv")

# Select features
X = data[['login_hour', 'files_accessed', 'usb_used']]

# Create AI model
model = IsolationForest(contamination=0.35, random_state=42)

# Train model
model.fit(X)

# Save trained model
joblib.dump(model, 'model.pkl')

print("Model trained successfully!")