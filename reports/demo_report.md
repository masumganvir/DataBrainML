# DataWise AI — Data Intelligence & ML Preparation Report

**Target Dataset:** `Dataset`  
**Generated:** 2026-09-27 08:40:04 UTC  
**ML Readiness Score:** **65.0/100** (NEEDS_PREPROCESSING)  
**Target Column:** `Not Specified` | **Task Type:** `Unassigned`  

---

## 1. Executive Summary

- **Dimensions:** 0 rows × 0 columns (0.0 KB)
- **Numerical Features:** 5
- **Categorical Features:** 4
- **Datetime Features:** 0
- **Duplicate Rows:** 0 (0.0%)
- **Leakage Flags:** 2 potential risk items identified

## 2. Data Quality & Hygiene Assessment

### Missing Values
| Column | Missing Count | Missing % | Severity | Recommended Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | 0 | 0.0% | **NONE** | none |
| `age` | 0 | 0.0% | **NONE** | none |
| `tenure_months` | 0 | 0.0% | **NONE** | none |
| `monthly_charges` | 0 | 0.0% | **NONE** | none |
| `total_charges` | 0 | 0.0% | **NONE** | none |
| `num_products` | 0 | 0.0% | **NONE** | none |
| `contract_type` | 0 | 0.0% | **NONE** | none |
| `payment_method` | 0 | 0.0% | **NONE** | none |
| `internet_service` | 0 | 0.0% | **NONE** | none |
| `gender` | 0 | 0.0% | **NONE** | none |
| `senior_citizen` | 0 | 0.0% | **NONE** | none |
| `churn` | 0 | 0.0% | **NONE** | none |

### Outliers & Anomalies
| Column | Method | Outlier Count | Outlier % | Severity |
| :--- | :--- | :--- | :--- | :--- |
| `age` | IQR (x1.5) | 0 | 0.0% | none |
| `tenure_months` | IQR (x1.5) | 0 | 0.0% | none |
| `monthly_charges` | IQR (x1.5) | 0 | 0.0% | none |
| `total_charges` | IQR (x1.5) | 0 | 0.0% | none |
| `num_products` | IQR (x1.5) | 0 | 0.0% | none |
| `senior_citizen` | IQR (x1.5) | 308 | 15.4% | severe |
| `churn` | IQR (x1.5) | 82 | 4.1% | moderate |

## 3. Multicollinearity & Correlation Analysis

No critical pairwise multicollinearity flags detected (|r| > 0.85).

## 4. Feature Engineering & Selection

- **Engineered Features (0):** None generated
- **Selected Features (12):** `customer_id`, `age`, `tenure_months`, `monthly_charges`, `total_charges`, `num_products`, `contract_type`, `payment_method`, `internet_service`, `gender`, `senior_citizen`, `churn`

## 5. Target Leakage & Risk Audit

⚠️ **Warning:** The following features have suspicious relationships with `Not Specified`:

- **`customer_id`** (HIGH Risk): 
- **`gender`** (HIGH Risk): 

## 6. Recommended ML Models & Strategy

### 1. Gradient Boosting (XGBoost / LightGBM) (`xgboost.XGBClassifier`)


**Pros:**
- State-of-the-art performance on tabular data
- Handles missing values natively
- Built-in regularization
- Fast with GPU support
**Cons:**
- Requires hyperparameter tuning
- Prone to overfitting on small datasets
- Less interpretable

**Suggested Metrics:** f1_weighted, roc_auc, log_loss

### 2. Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)


**Pros:**
- Robust to outliers and missing value proxies
- Built-in feature importance
- Handles high-dimensional data well
- No feature scaling required
**Cons:**
- Can be slow on very large datasets
- Less interpretable than linear models
- Memory-intensive for many trees

**Suggested Metrics:** accuracy, f1_weighted, roc_auc, precision_recall_auc

### 3. Logistic Regression (`sklearn.linear_model.LogisticRegression`)


**Pros:**
- Highly interpretable coefficients
- Fast training and inference
- Good baseline model
- Probabilistic output
**Cons:**
- Assumes linear decision boundary
- Sensitive to multicollinearity
- Requires feature scaling

**Suggested Metrics:** accuracy, f1_weighted, roc_auc

## 7. Next Actions
1. Download the generated `pipeline.py` artifact for reproducible scikit-learn preprocessing.
2. Validate that target leakage columns are removed prior to training.
3. Establish baseline performance using the top recommended algorithm.

*Report compiled autonomously by DataWise AI Engine.*