# DataWise AI — Production Model Package

## Project Overview
- **Session ID**: `2b90d7a6-6eff-4865-9d4f-a77007aa198d`
- **Task Type**: `classification`
- **Target Feature**: `is_churn`
- **Final Selected Model**: `Random Forest`

## Performance Metrics (Test Set)
- **Accuracy**: 0.8333
- **Balanced Accuracy**: 0.75
- **F1**: 0.8148
- **Precision**: 0.8667
- **Recall**: 0.8333
- **ROC-AUC**: 1.0
- **PR-AUC**: 1.0

## Package Structure
```text
DataWise_Project/
├── report/
│   └── analysis_report.html       # Full interactive analysis & diagnostic report
├── notebook/
│   └── dataset_analysis.ipynb     # Complete 24-section reproducible Jupyter Notebook
├── model/
│   ├── final_model.joblib         # Scikit-learn Pipeline (preprocessing + model)
│   └── model_metadata.json        # Reproducibility metadata, versions, hash
├── code/
│   ├── preprocessing.py           # Standalone preprocessing transformer
│   ├── training.py                # Standalone training script
│   └── inference.py               # Standalone production inference script
└── README.md
```

## Running Inference
```bash
pip install pandas scikit-learn joblib
python code/inference.py path/to/new_data.csv
```