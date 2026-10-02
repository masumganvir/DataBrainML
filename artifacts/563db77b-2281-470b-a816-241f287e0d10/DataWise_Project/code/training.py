"""
DataWise AI — Training Script
Reproduces training of Logistic Regression on clean data.
"""

import sys
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from preprocessing import create_preprocessor

TARGET_COL = "is_churn"
TASK_TYPE = "classification"


def train(data_path: str):
    df = pd.read_csv(data_path)
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    preprocessor = create_preprocessor()
    # Replace with selected estimator architecture
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    estimator = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42) if TASK_TYPE == "classification" else RandomForestRegressor(n_estimators=50, random_state=42)

    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    print("Training pipeline...")
    pipe.fit(X_train, y_train)
    score = pipe.score(X_test, y_test)
    print(f"Test Score: {round(score, 4)}")

    joblib.dump(pipe, "retrained_model.joblib")
    print("Model saved to retrained_model.joblib")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python training.py <path_to_dataset.csv>")
        sys.exit(1)
    train(sys.argv[1])