"""
DataWise AI — Production Inference Script
Generated automatically for target: churn (binary_classification)
"""

import sys
import json
from pathlib import Path
import pandas as pd
import joblib

MODEL_PATH = Path(__file__).parent.parent / "model" / "final_model.joblib"
METADATA_PATH = Path(__file__).parent.parent / "model" / "model_metadata.json"


def load_model():
    """Loads the serialized end-to-end scikit-learn pipeline."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


def predict(data_source):
    """
    Accepts a pandas DataFrame or path to a CSV file.
    Executes end-to-end preprocessing, scaling, encoding, and inference.
    """
    if isinstance(data_source, (str, Path)):
        df = pd.read_csv(data_source)
    elif isinstance(data_source, pd.DataFrame):
        df = data_source.copy()
    else:
        raise TypeError("Expected filepath or pandas DataFrame.")

    # Drop target column if present in evaluation input
    if "churn" in df.columns:
        df = df.drop(columns=["churn"])

    model = load_model()
    predictions = model.predict(df)
    results = pd.DataFrame({"prediction": predictions})

    # Generate probabilities for classification
    if hasattr(model, "predict_proba"):
        try:
            probas = model.predict_proba(df)
            if probas.shape[1] == 2:
                results["probability_positive"] = probas[:, 1]
            else:
                for i in range(probas.shape[1]):
                    results[f"probability_class_{i}"] = probas[:, i]
        except Exception:
            pass

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inference.py <path_to_new_data.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    print(f"Loading data from {csv_path}...")
    preds = predict(csv_path)
    print("\n=== Inference Results (first 10 rows) ===")
    print(preds.head(10))
    output_path = "predictions_output.csv"
    preds.to_csv(output_path, index=False)
    print(f"\nSaved full predictions to {output_path}")