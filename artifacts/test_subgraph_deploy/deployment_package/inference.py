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
    test_sample = [{"feature_1": 0, "feature_2": 0}]
    print("Inference Test Output:", predict(test_sample))
