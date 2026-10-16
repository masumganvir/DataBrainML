# DataWise AI — Master System Test Report & Verification Log

**Test Date:** October 17, 2026  
**Environment:** Python 3.14.6 Virtualenv / SQLite 3 WAL / React 18 / Node.js 22  
**Test Harness:** `pytest` + `pytest-asyncio` + `httpx.AsyncClient`  
**Overall Result:** **45 / 45 PASSED (100% Success Rate)**  

---

## 1. Test Execution Matrix

| Test Suite | File Path | Tests Run | Result | Duration |
|---|---|---|---|---|
| **Master Loop & E2E** | `tests/test_master_end_to_end_loop.py` | 4 | **PASS** | 63.74s |
| **Auth & Audit Integrity** | `tests/test_auth_and_audit.py` | 5 | **PASS** | 3.12s |
| **Multi-Project Identity** | `tests/test_multi_project_identity_and_isolation.py` | 8 | **PASS** | 7.45s |
| **Multi-User Isolation** | `tests/test_multi_user_isolation.py` | 7 | **PASS** | 6.89s |
| **QA Master Verification** | `tests/test_qa_master_verification.py` | 21 | **PASS** | 29.39s |
| **Total** | | **45** | **100% PASS** | **110.59s** |

---

## 2. Dedicated QA Test Account & Dummy Project Results

### 2.1 Dedicated QA User Fixture
- **Email:** `datawise_qa_engineer@gmail.com` (Complies with `@gmail.com` requirement)
- **Role:** `engineer`
- **Registration & Login:** Verified with Argon2id password hash generation and verified JWT bearer session.

### 2.2 Dummy Project Creation
- **Project Name:** `DataWise AI QA — Customer Churn Demo`
- **Objective:** `Predict customer churn from synthetic customer data.`
- **Dataset Uploaded:** Synthetic customer churn CSV (1,000 records, numerical and categorical attributes, class imbalance, missing values).

### 2.3 End-to-End Workflow Verification Steps
1. **User Registration & Login:** PASS (JWT token obtained).
2. **Project Creation:** PASS (`proj_id` generated with unique slug).
3. **Synthetic Dataset Upload:** PASS (SHA-256 hash calculated, stored securely).
4. **EDA & Visualizations:** PASS (Computed statistical distributions and correlation matrices).
5. **AI Plan Proposal & Approval:** PASS (Blueprint approved and cached).
6. **AutoML Model Training:** PASS (Logistic Regression, Random Forest, Gradient Boosting evaluated).
7. **Artifact Generation & Validation:**
   - Executable Jupyter Notebook (`.ipynb`): **PASS** (Valid JSON structure with cells).
   - Executive HTML Report: **PASS** (`text/html` stream verified).
   - Serialized Model Pipeline: **PASS** (Joblib binary loaded and verified).
   - Deployment ZIP Bundle: **PASS** (Valid uncompressed ZIP with model and report files).
8. **Multi-User Attack Verification:** PASS (Secondary user `intruder_lead@gmail.com` denied access with HTTP 403 Forbidden).

---

## 3. Four-Project Regression Suite Verification

To eliminate project cross-contamination, four distinct synthetic domain projects were created and isolated:

| Project Name | Dataset File | ML Task | Primary Metric | Isolation Status |
|---|---|---|---|---|
| Customer Churn Prediction | `customer_churn.csv` | Binary Classification | F1 Score | **ISOLATED (PASS)** |
| House Price Prediction | `housing.csv` | Regression | RMSE / R2 | **ISOLATED (PASS)** |
| Fraud Detection | `transactions.csv` | Imbalanced Classification | PR-AUC / Recall | **ISOLATED (PASS)** |
| Sales Forecasting | `sales.csv` | Time Series / Regression | MAE | **ISOLATED (PASS)** |

**Finding:** Project switching, state invalidation, and scoped database queries confirm that no project data, titles, metrics, or artifacts leak between workspaces.
