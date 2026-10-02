"""
End-to-End Training & Best Model Selection for Student Exam Performance
Target: pass_status ('Pass' vs 'Fail')
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

DATASET_PATH = r"C:\Users\Chokha\Desktop\DATAPREPAGENT\student_exam_performance.csv"
ARTIFACTS_DIR = r"C:\Users\Chokha\Desktop\DATAPREPAGENT\artifacts\student_project"
MODELS_DIR = r"C:\Users\Chokha\Desktop\DATAPREPAGENT\models"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

print("=" * 60)
print("1. LOADING DATASET...")
df = pd.read_csv(DATASET_PATH)
print(f"Dataset shape: {df.shape}")

# Inspect target
print("\nTarget 'pass_status' distribution:")
print(df["pass_status"].value_counts(dropna=False))

# Identify target leakage columns:
# student_id: identifier
# exam_score, performance_grade, performance_level, questions_correct: post-exam outcome proxies
LEAKAGE_COLS = [
    "student_id",
    "exam_score",
    "performance_grade",
    "performance_level",
    "questions_correct"
]

target_col = "pass_status"
feature_cols = [c for c in df.columns if c not in LEAKAGE_COLS and c != target_col]
print(f"\nNumber of predictive features: {len(feature_cols)}")

X = df[feature_cols].copy()
y_raw = df[target_col].copy()

# Binary encoding: Pass -> 1, Fail -> 0
y = (y_raw.str.strip().str.lower() == "pass").astype(int)

# Separate numeric and categorical
numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
categorical_features = X.select_dtypes(exclude=[np.number]).columns.tolist()

print(f"Numeric features ({len(numeric_features)}): {numeric_features}")
print(f"Categorical features ({len(categorical_features)}): {categorical_features}")

# Build Preprocessor
numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ]
)

# Train/Test Split (80/20 stratified)
print("\n" + "=" * 60)
print("2. STRATIFIED TRAIN/TEST SPLIT...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"Train set: {X_train.shape[0]} samples")
print(f"Test set:  {X_test.shape[0]} samples")

# Candidate Models
candidates = {
    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_iter=150, learning_rate=0.08, max_leaf_nodes=31, random_state=42
    ),
    "RandomForest": RandomForestClassifier(
        n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
    ),
    "LogisticRegression": LogisticRegression(
        max_iter=1000, random_state=42
    )
}

results = {}
trained_pipelines = {}

print("\n" + "=" * 60)
print("3. TRAINING & EVALUATING CANDIDATE MODELS...")

for name, clf in candidates.items():
    print(f"\n---> Training {name}...")
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", clf)
    ])
    
    # Fit pipeline
    pipeline.fit(X_train, y_train)
    trained_pipelines[name] = pipeline
    
    # Predict on test
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else y_pred
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_proba)
    
    results[name] = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4),
    }
    
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {roc_auc:.4f}")

# Select Champion Model based on ROC-AUC then F1
champion_name = max(results, key=lambda k: (results[k]["roc_auc"], results[k]["f1_score"]))
champion_pipeline = trained_pipelines[champion_name]

print("\n" + "=" * 60)
print(f"4. CHAMPION MODEL SELECTED: {champion_name}")
print(json.dumps(results[champion_name], indent=2))

# Classification report and confusion matrix for champion
y_pred_champ = champion_pipeline.predict(X_test)
cm = confusion_matrix(y_test, y_pred_champ).tolist()
cls_report = classification_report(y_test, y_pred_champ, target_names=["Fail", "Pass"], output_dict=True)

# Save Schema & Sample Defaults for UI Form
cat_unique_values = {col: [str(v) for v in X[col].dropna().unique().tolist()][:20] for col in categorical_features}
num_summary = {
    col: {
        "min": float(X[col].min()),
        "max": float(X[col].max()),
        "mean": float(X[col].mean()),
        "median": float(X[col].median()),
        "default": float(X[col].median())
    } for col in numeric_features
}

schema = {
    "target": "pass_status",
    "classes": ["Fail", "Pass"],
    "features": feature_cols,
    "numeric_features": numeric_features,
    "categorical_features": categorical_features,
    "categorical_options": cat_unique_values,
    "numeric_summary": num_summary,
    "leakage_excluded": LEAKAGE_COLS
}

metadata = {
    "project_name": "Student Exam Performance Pass/Fail Predictor",
    "champion_algorithm": champion_name,
    "metrics": results[champion_name],
    "all_candidate_metrics": results,
    "confusion_matrix": cm,
    "classification_report": cls_report,
    "dataset_shape": list(df.shape),
    "train_samples": int(X_train.shape[0]),
    "test_samples": int(X_test.shape[0])
}

# Serialize Pipeline and Artifacts
pipeline_path_1 = os.path.join(MODELS_DIR, "student_model_pipeline.pkl")
pipeline_path_2 = os.path.join(ARTIFACTS_DIR, "model_pipeline.pkl")
schema_path = os.path.join(ARTIFACTS_DIR, "feature_schema.json")
metadata_path = os.path.join(ARTIFACTS_DIR, "model_metadata.json")

print("\n" + "=" * 60)
print("5. SAVING SERIALIZED CHAMPION MODEL & METADATA...")
joblib.dump(champion_pipeline, pipeline_path_1)
joblib.dump(champion_pipeline, pipeline_path_2)

with open(schema_path, "w") as f:
    json.dump(schema, f, indent=2)

with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Saved pipeline to: {pipeline_path_1}")
print(f"Saved pipeline to: {pipeline_path_2}")
print(f"Saved schema to:   {schema_path}")
print(f"Saved metadata to: {metadata_path}")

# Sanity Test Inference
print("\n" + "=" * 60)
print("6. VERIFYING INFERENCE ON REAL SAMPLES...")
sample_rows = X_test.head(3)
preds = champion_pipeline.predict(sample_rows)
probas = champion_pipeline.predict_proba(sample_rows)

for i, (pred, proba) in enumerate(zip(preds, probas)):
    pred_label = "Pass" if pred == 1 else "Fail"
    actual_label = "Pass" if y_test.iloc[i] == 1 else "Fail"
    print(f"Sample #{i+1}: Predicted = {pred_label} (P(Pass)={proba[1]:.4f}, P(Fail)={proba[0]:.4f}) | Actual = {actual_label}")

print("\nPipeline ready and verified!")
