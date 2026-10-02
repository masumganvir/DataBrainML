"""
Standalone Inference Script for DataWise AI Exported Pipeline
"""
import sys
import json
import joblib
import pandas as pd

def predict(input_records):
    pipeline = joblib.load("model.joblib")
    df = pd.DataFrame(input_records)
    preds = pipeline.predict(df)
    return preds.tolist()

if __name__ == "__main__":
    test_sample = [{"age": 0, "monthly_charges": 0, "total_charges": 0, "num_products": 0}]
    print("Inference Test Output:", predict(test_sample))
