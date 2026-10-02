# DataWise AI — Production Model Package

## Project Overview
- **Session ID**: `test_agent_session_123`
- **Task Type**: `binary_classification`
- **Target Feature**: `churn`
- **Final Selected Model**: `ElasticNet`

## Performance Metrics (Test Set)
- **RMSE**: 0.6289
- **MAE**: 0.6288
- **R2**: 0.0
- **MAPE**: 0.6288

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