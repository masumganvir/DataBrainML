"""
DataWise AI — Preprocessing: Train/Test & Cross-Validation Splitting
"""

from typing import Any, Dict, Optional, Tuple
import pandas as pd
from sklearn.model_selection import (
    KFold,
    StratifiedKFold,
    TimeSeriesSplit,
    train_test_split,
)


def split_dataset(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    test_size: float = 0.2,
    stratify: bool = True,
    time_column: Optional[str] = None,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.Series], Optional[pd.Series]]:
    """
    Performs leakage-safe train/test split.
    If time_column is given, performs chronological temporal split.
    If stratify is True and task is classification, stratifies by target.
    """
    if time_column and time_column in df.columns:
        # Chronological split
        sorted_df = df.sort_values(by=time_column)
        split_idx = int(len(sorted_df) * (1 - test_size))
        train_df = sorted_df.iloc[:split_idx]
        test_df = sorted_df.iloc[split_idx:]
    else:
        stratify_arr = None
        if stratify and target_column and target_column in df.columns:
            target_series = df[target_column]
            # Only stratify if classification with at least 2 instances per class
            vc = target_series.value_counts()
            if len(vc) < 50 and (vc >= 2).all():
                stratify_arr = target_series

        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify_arr,
        )

    if target_column and target_column in df.columns:
        X_train = train_df.drop(columns=[target_column])
        y_train = train_df[target_column]
        X_test = test_df.drop(columns=[target_column])
        y_test = test_df[target_column]
        return X_train, X_test, y_train, y_test

    return train_df, test_df, None, None
