"""
DataWise AI — Test Dataset Generator

Creates a comprehensive suite of test CSV files that cover
all edge cases the agent must handle:

  1. clean_dataset.csv            — Well-structured, minimal issues
  2. missing_values_dataset.csv   — Heavy missing values across types
  3. outliers_dataset.csv         — Extreme outliers in multiple columns
  4. imbalanced_classification.csv— Severely imbalanced binary target
  5. high_cardinality.csv         — High-cardinality categorical column
  6. skewed_distributions.csv     — Heavy skewness in numerical columns
  7. correlated_features.csv      — High multicollinearity
  8. datetime_features.csv        — Datetime columns requiring extraction
  9. mixed_types.csv              — Mixed data types, identifiers, constants
 10. duplicate_rows.csv           — Rows with exact duplicates

Run:  python data/test_datasets/generate_test_datasets.py
"""

from __future__ import annotations

import os
import random
import string
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_DIR = Path(__file__).parent
random.seed(42)
np.random.seed(42)


def make_clean_dataset(n: int = 1000) -> pd.DataFrame:
    """Well-structured dataset: predict customer churn."""
    df = pd.DataFrame({
        "customer_id": [f"CUST{i:05d}" for i in range(n)],
        "age": np.random.randint(18, 80, n),
        "tenure_months": np.random.randint(1, 120, n),
        "monthly_charges": np.round(np.random.uniform(20, 120, n), 2),
        "total_charges": np.round(np.random.uniform(100, 8000, n), 2),
        "num_products": np.random.randint(1, 5, n),
        "contract_type": np.random.choice(["Month-to-month", "One year", "Two year"], n),
        "payment_method": np.random.choice(["Credit card", "Bank transfer", "Electronic check", "Mailed check"], n),
        "internet_service": np.random.choice(["DSL", "Fiber optic", "No"], n),
        "gender": np.random.choice(["Male", "Female"], n),
        "senior_citizen": np.random.choice([0, 1], n, p=[0.85, 0.15]),
        "churn": np.random.choice([0, 1], n, p=[0.73, 0.27]),
    })
    return df


def make_missing_values_dataset(n: int = 1200) -> pd.DataFrame:
    """Dataset with strategic missing values at different severities."""
    df = make_clean_dataset(n)
    # LOW: 3% missing in age
    idx_low = np.random.choice(n, int(n * 0.03), replace=False)
    df.loc[idx_low, "age"] = np.nan
    # MEDIUM: 15% missing in monthly_charges
    idx_med = np.random.choice(n, int(n * 0.15), replace=False)
    df.loc[idx_med, "monthly_charges"] = np.nan
    # HIGH: 35% missing in num_products
    idx_high = np.random.choice(n, int(n * 0.35), replace=False)
    df.loc[idx_high, "num_products"] = np.nan
    # CRITICAL: 55% missing in total_charges
    idx_crit = np.random.choice(n, int(n * 0.55), replace=False)
    df.loc[idx_crit, "total_charges"] = np.nan
    # Categorical: 12% missing in payment_method
    idx_cat = np.random.choice(n, int(n * 0.12), replace=False)
    df.loc[idx_cat, "payment_method"] = np.nan
    return df


def make_outliers_dataset(n: int = 800) -> pd.DataFrame:
    """Dataset with clearly identifiable outliers using IQR/Z-score."""
    df = make_clean_dataset(n)
    # Inject extreme outliers in monthly_charges
    outlier_idx = np.random.choice(n, 25, replace=False)
    df.loc[outlier_idx[:15], "monthly_charges"] = np.random.uniform(500, 1500, 15)
    df.loc[outlier_idx[15:], "monthly_charges"] = np.random.uniform(-200, -50, 10)
    # Inject outliers in tenure_months
    outlier_idx2 = np.random.choice(n, 10, replace=False)
    df.loc[outlier_idx2, "tenure_months"] = np.random.randint(500, 1000, 10)
    # Inject outliers in age
    outlier_idx3 = np.random.choice(n, 8, replace=False)
    df.loc[outlier_idx3, "age"] = np.random.randint(150, 300, 8)
    return df


def make_imbalanced_dataset(n: int = 2000) -> pd.DataFrame:
    """Severely imbalanced binary classification (95/5 split)."""
    df = make_clean_dataset(n)
    df["churn"] = np.random.choice([0, 1], n, p=[0.95, 0.05])
    return df


def make_high_cardinality_dataset(n: int = 500) -> pd.DataFrame:
    """Dataset with a high-cardinality categorical column (city names)."""
    cities = [f"City_{i}" for i in range(400)]  # 400 unique cities in 500 rows
    df = make_clean_dataset(n)
    df["city"] = np.random.choice(cities, n)
    df["zip_code"] = [f"{np.random.randint(10000,99999)}" for _ in range(n)]
    df["product_code"] = [
        "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        for _ in range(n)
    ]
    return df


def make_skewed_dataset(n: int = 1000) -> pd.DataFrame:
    """Dataset with heavily right-skewed numerical columns."""
    df = pd.DataFrame({
        "id": range(n),
        "income": np.random.exponential(scale=30000, size=n),         # heavy right skew
        "transaction_amount": np.random.lognormal(mean=4, sigma=2, size=n),
        "page_views": np.random.poisson(lam=2, size=n),               # count data
        "session_duration_sec": np.random.gamma(shape=1.5, scale=30, size=n),
        "age": np.random.normal(loc=35, scale=10, size=n).clip(18, 90),  # approx normal
        "clicks": np.random.negative_binomial(n=1, p=0.3, size=n),
        "conversion": np.random.choice([0, 1], n, p=[0.85, 0.15]),
    })
    return df


def make_correlated_dataset(n: int = 1000) -> pd.DataFrame:
    """Dataset with highly correlated features (multicollinearity)."""
    base = np.random.normal(0, 1, n)
    df = pd.DataFrame({
        "feature_a": base,
        "feature_b": base + np.random.normal(0, 0.05, n),   # corr ≈ 0.98 with a
        "feature_c": base * 2 + np.random.normal(0, 0.3, n),# corr ≈ 0.95 with a
        "feature_d": np.random.normal(0, 1, n),               # independent
        "feature_e": base * -1 + np.random.normal(0, 0.1, n),# strong negative corr
        "revenue": np.random.uniform(1000, 100000, n),
        "profit": None,  # will derive from revenue
        "profit_margin": np.random.uniform(0.05, 0.35, n),
        "target": np.random.choice([0, 1], n),
    })
    df["profit"] = df["revenue"] * df["profit_margin"] + np.random.normal(0, 100, n)
    return df


def make_datetime_dataset(n: int = 800) -> pd.DataFrame:
    """Dataset with datetime columns requiring extraction."""
    start = pd.Timestamp("2020-01-01")
    end = pd.Timestamp("2024-12-31")
    timestamps = pd.to_datetime(
        np.random.randint(start.value, end.value, n, dtype=np.int64)
    )
    df = pd.DataFrame({
        "transaction_id": [f"TXN{i:06d}" for i in range(n)],
        "transaction_date": timestamps,
        "signup_date": pd.to_datetime(
            np.random.randint(
                pd.Timestamp("2019-01-01").value,
                start.value, n, dtype=np.int64
            )
        ),
        "amount": np.round(np.random.uniform(5, 500, n), 2),
        "category": np.random.choice(["Electronics", "Clothing", "Food", "Books", "Sports"], n),
        "customer_region": np.random.choice(["North", "South", "East", "West"], n),
        "is_returned": np.random.choice([0, 1], n, p=[0.92, 0.08]),
    })
    return df


def make_mixed_types_dataset(n: int = 600) -> pd.DataFrame:
    """Dataset with identifiers, constants, near-constants, and mixed types."""
    df = pd.DataFrame({
        # Identifier columns (should be flagged, not auto-dropped)
        "user_id": [f"USR{i:05d}" for i in range(n)],
        "email": [f"user{i}@example.com" for i in range(n)],
        # Constant column (useless)
        "data_source": ["platform_v2"] * n,
        # Near-constant (99% same value)
        "verified": np.random.choice(
            ["yes", "no"], n, p=[0.99, 0.01]
        ),
        # Normal features
        "age": np.random.randint(18, 75, n),
        "purchase_amount": np.round(np.random.uniform(10, 500, n), 2),
        "num_orders": np.random.randint(1, 50, n),
        "country": np.random.choice(["US", "UK", "CA", "AU", "IN"], n),
        # Binary
        "is_premium": np.random.choice([0, 1], n, p=[0.6, 0.4]),
        # Target
        "will_renew": np.random.choice([0, 1], n, p=[0.55, 0.45]),
    })
    return df


def make_duplicate_rows_dataset(n: int = 500) -> pd.DataFrame:
    """Dataset with intentional duplicate rows."""
    df = make_clean_dataset(n)
    # Duplicate 8% of rows
    dup_count = int(n * 0.08)
    dup_rows = df.sample(n=dup_count, random_state=42)
    df = pd.concat([df, dup_rows], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
    return df


def make_fraud_dataset(n: int = 2500) -> pd.DataFrame:
    """
    Financial fraud dataset with rare meaningful observations (1.6% fraud).
    CRITICAL: Outliers in transaction_amount and risk_score correlate with fraud=1.
    Deleting these statistical outliers destroys the entire predictive signal.
    """
    np.random.seed(42)
    # 98.4% legitimate, 1.6% fraudulent
    n_fraud = int(n * 0.016)
    n_legit = n - n_fraud

    # Legitimate transactions: typical spend $10-$250, low risk score
    legit_amounts = np.random.lognormal(mean=3.5, sigma=0.8, size=n_legit).clip(5, 500)
    legit_risk = np.random.beta(a=1, b=5, size=n_legit) * 30
    legit_velocity = np.random.poisson(lam=1.5, size=n_legit)
    legit_intl = np.random.choice([0, 1], n_legit, p=[0.95, 0.05])
    legit_target = np.zeros(n_legit, dtype=int)

    # Fraudulent transactions: extreme spend $1500-$15000 (extreme statistical outliers!), high risk score
    fraud_amounts = np.random.uniform(1500, 15000, size=n_fraud)
    fraud_risk = np.random.uniform(70, 99, size=n_fraud)
    fraud_velocity = np.random.poisson(lam=8.0, size=n_fraud)
    fraud_intl = np.random.choice([0, 1], n_fraud, p=[0.30, 0.70])
    fraud_target = np.ones(n_fraud, dtype=int)

    amounts = np.concatenate([legit_amounts, fraud_amounts])
    risks = np.concatenate([legit_risk, fraud_risk])
    velocities = np.concatenate([legit_velocity, fraud_velocity])
    intls = np.concatenate([legit_intl, fraud_intl])
    targets = np.concatenate([legit_target, fraud_target])

    df = pd.DataFrame({
        "transaction_id": [f"TXN_{i:07d}" for i in range(n)],
        "transaction_amount": np.round(amounts, 2),
        "risk_score": np.round(risks, 2),
        "transaction_velocity_1h": velocities,
        "is_international": intls,
        "channel": np.random.choice(["web", "mobile_app", "pos", "atm"], n, p=[0.4, 0.35, 0.2, 0.05]),
        "device_trust_score": np.random.uniform(0.1, 1.0, n).round(3),
        "is_fraud": targets,
    })

    # Shuffle rows
    return df.sample(frac=1, random_state=42).reset_index(drop=True)


# ------------------------------------------------------------------ #
#  Generate All Datasets
# ------------------------------------------------------------------ #

DATASETS = {
    "clean_dataset.csv": make_clean_dataset,
    "missing_values_dataset.csv": make_missing_values_dataset,
    "outliers_dataset.csv": make_outliers_dataset,
    "imbalanced_classification.csv": make_imbalanced_dataset,
    "high_cardinality.csv": make_high_cardinality_dataset,
    "skewed_distributions.csv": make_skewed_dataset,
    "correlated_features.csv": make_correlated_dataset,
    "datetime_features.csv": make_datetime_dataset,
    "mixed_types.csv": make_mixed_types_dataset,
    "duplicate_rows.csv": make_duplicate_rows_dataset,
    "fraud_detection.csv": make_fraud_dataset,
}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {len(DATASETS)} test datasets -> {OUTPUT_DIR}")
    for filename, generator_fn in DATASETS.items():
        df = generator_fn()
        out_path = OUTPUT_DIR / filename
        df.to_csv(out_path, index=False)
        print(f"  [OK] {filename:40s} rows={len(df):5d}  cols={len(df.columns):3d}")
    print("\nAll test datasets generated successfully!")


if __name__ == "__main__":
    main()
