# Model Prediction Client Example
import joblib
import pandas as pd

# Load serialized model pipeline
pipeline = joblib.load('../models/model_pipeline.pkl')
print("Model pipeline loaded successfully.")

# Sample input
sample_data = pd.DataFrame([{
    "customer_id": 0, "age": 0, "tenure_months": 0, "monthly_charges": 0, "total_charges": 0
}])

prediction = pipeline.predict(sample_data)
print("Prediction output:", prediction[0])
