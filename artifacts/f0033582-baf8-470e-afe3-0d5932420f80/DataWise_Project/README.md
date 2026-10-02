# DataWise AI — Production Model Package

## Project Overview
- **Session ID**: `f0033582-baf8-470e-afe3-0d5932420f80`
- **Task Type**: `classification`
- **Target Feature**: `is_churn`
- **Final Selected Model**: `Selected Model`

## Performance Metrics (Test Set)


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