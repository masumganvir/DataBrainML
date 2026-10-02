# Object Storage & File Security (S3 / MinIO)

## 1. Purpose
Provides scalable, durable, and secure binary storage for large assets including raw datasets, preprocessed parquet files, ML model checkpoints (joblib, pickle, onnx), high-resolution EDA plots, notebooks, and compiled PDF reports.

## 2. Directory & Key Hierarchy
```
projects/{project_id}/
├── datasets/{dataset_id}/
│   └── {uuid}_{sanitized_name}.csv
├── models/
│   └── {model_id}/{version}/model.joblib
├── notebooks/
│   └── {uuid}_eda_pipeline.ipynb
├── reports/
│   └── {uuid}_executive_summary.pdf
└── plots/
    └── {uuid}_feature_importance.png
```

## 3. Presigned URLs
Raw storage credentials are never exposed to the frontend. Direct downloads are served via signed URLs (`generate_presigned_url`) with a default expiration of 3600 seconds.

## 4. File Security & Validation
All uploaded files are treated as untrusted:
- **Allowlist Extensions**: `.csv`, `.xlsx`, `.xls`, `.json`, `.parquet`.
- **Magic Bytes Validation**: Inspects headers (e.g. `PAR1` for Parquet, `PK\x03\x04` for XLSX) to block executable binary masquerading.
- **Filename Sanitization**: Path traversal sequences (`..`), shell metacharacters, and leading dots are stripped.
- **Upload Limit**: Enforced 100 MB per file limit (`MAX_UPLOAD_SIZE_MB`).

## 5. Local Fallback & High Availability
In local development environments without an active MinIO cluster, `StorageService` seamlessly stages files into `./data/uploads/` while maintaining the identical hierarchical key schema.
