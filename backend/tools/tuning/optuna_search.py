"""
DataWise AI — Tuning: Optuna Bayesian Search
"""

from typing import Any, Dict, Optional


def run_optuna_search(
    model_name: str,
    X: Any,
    y: Any,
    task_type: str = "classification",
    n_trials: int = 25,
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """Bayesian hyperparameter optimization with trial budget limits."""
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        from sklearn.model_selection import cross_val_score
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

        def objective(trial):
            n_estimators = trial.suggest_int("n_estimators", 50, 150, step=25)
            max_depth = trial.suggest_int("max_depth", 3, 12)
            min_samples_split = trial.suggest_int("min_samples_split", 2, 8)

            if task_type.lower() == "classification":
                clf = RandomForestClassifier(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    random_state=42,
                    n_jobs=-1,
                )
                score = cross_val_score(clf, X, y, cv=3, scoring="f1_weighted").mean()
            else:
                reg = RandomForestRegressor(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    random_state=42,
                    n_jobs=-1,
                )
                score = cross_val_score(reg, X, y, cv=3, scoring="r2").mean()
            return score

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, timeout=timeout_seconds)

        return {
            "method": "Optuna Bayesian Optimization",
            "best_params": study.best_params,
            "best_score": round(float(study.best_value), 4),
            "trials_completed": len(study.trials),
        }
    except ImportError:
        return {
            "method": "Optuna (Unavailable)",
            "status": "Optuna not installed, using fallback parameter grid",
            "best_params": {"n_estimators": 100, "max_depth": 6},
            "best_score": None,
        }
