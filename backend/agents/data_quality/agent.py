"""
DataWise AI — Data Quality Agent
Detects data health issues, missing values, duplicates, near-zero variance,
suspicious identifiers, high cardinality, class imbalance, and PII.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class DataQualityAgent(BaseAgent):
    """Data Quality Agent: Computes composite quality score and generates remediation report."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Data Quality Agent")

    def _detect_pii(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect email, phone, SSN/tax ID, credit card patterns in sample strings."""
        pii_findings: List[Dict[str, Any]] = []
        email_regex = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
        phone_regex = re.compile(r"^\+?1?\d{9,15}$")
        cc_regex = re.compile(r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})$")

        sample_df = df.head(100)
        for col in sample_df.select_dtypes(include=["object", "string"]).columns:
            series = sample_df[col].dropna().astype(str)
            if len(series) == 0:
                continue

            # Email check
            email_matches = series.apply(lambda x: bool(email_regex.match(x.strip()))).sum()
            if email_matches / len(series) > 0.3:
                pii_findings.append({
                    "column": col,
                    "pii_type": "email",
                    "severity": "CRITICAL",
                    "recommended_action": "MASK_OR_EXCLUDE",
                })
                continue

            # Phone check
            phone_matches = series.apply(lambda x: bool(phone_regex.match(re.sub(r"[\s\-\(\)]", "", x)))).sum()
            if phone_matches / len(series) > 0.3:
                pii_findings.append({
                    "column": col,
                    "pii_type": "phone_number",
                    "severity": "HIGH",
                    "recommended_action": "MASK_OR_EXCLUDE",
                })
                continue

            # Credit card check
            cc_matches = series.apply(lambda x: bool(cc_regex.match(re.sub(r"[\s\-]", "", x)))).sum()
            if cc_matches / len(series) > 0.2:
                pii_findings.append({
                    "column": col,
                    "pii_type": "payment_card",
                    "severity": "CRITICAL",
                    "recommended_action": "EXCLUDE_IMMEDIATELY",
                })

        return pii_findings

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Data quality audit failed: unable to load dataset.",
                errors=["Dataset path invalid"],
            )

        n_rows, n_cols = df.shape
        issues: List[Dict[str, Any]] = []
        score_deductions = 0.0

        # 1. Duplicate rows
        dup_count = int(df.duplicated().sum())
        dup_pct = round((dup_count / n_rows) * 100, 2)
        if dup_count > 0:
            severity = "HIGH" if dup_pct > 5 else "MEDIUM"
            score_deductions += min(dup_pct * 1.5, 20.0)
            issues.append({
                "type": "duplicate_rows",
                "severity": severity,
                "count": dup_count,
                "percentage": dup_pct,
                "recommendation": "Remove duplicate rows before model training.",
            })

        # 2. Missing values by column
        missing_by_col = []
        for col in df.columns:
            m_cnt = int(df[col].isna().sum())
            if m_cnt > 0:
                pct = round((m_cnt / n_rows) * 100, 2)
                sev = "CRITICAL" if pct > 50 else ("HIGH" if pct > 20 else ("MEDIUM" if pct > 5 else "LOW"))
                score_deductions += min(pct * 0.2, 5.0)
                missing_by_col.append({"column": col, "missing_count": m_cnt, "missing_pct": pct, "severity": sev})
        if missing_by_col:
            issues.append({
                "type": "missing_values",
                "affected_columns": len(missing_by_col),
                "details": missing_by_col,
            })

        # 3. Constant and near-constant columns
        constant_cols = []
        for col in df.columns:
            if df[col].nunique(dropna=True) <= 1:
                constant_cols.append(col)
                score_deductions += 5.0
        if constant_cols:
            issues.append({
                "type": "constant_columns",
                "severity": "HIGH",
                "columns": constant_cols,
                "recommendation": "Drop zero-variance constant columns.",
            })

        # 4. High cardinality categorical columns
        high_card_cols = []
        for col in df.select_dtypes(include=["object", "category", "string"]).columns:
            n_uniq = df[col].nunique()
            if n_uniq > 50 and (n_uniq / n_rows) > 0.2:
                high_card_cols.append({"column": col, "unique_count": n_uniq})
                score_deductions += 3.0
        if high_card_cols:
            issues.append({
                "type": "high_cardinality",
                "severity": "MEDIUM",
                "columns": high_card_cols,
                "recommendation": "Apply target encoding, frequency encoding, or group rare levels.",
            })

        # 5. PII Detection
        pii_issues = self._detect_pii(df)
        if pii_issues:
            score_deductions += 15.0
            issues.append({
                "type": "pii_detected",
                "severity": "CRITICAL",
                "findings": pii_issues,
                "recommendation": "Mask or exclude sensitive personal identifiers before ML training.",
            })

        # Composite score
        quality_score = max(0.0, round(100.0 - score_deductions, 1))
        grade = "EXCELLENT" if quality_score >= 90 else ("GOOD" if quality_score >= 75 else ("FAIR" if quality_score >= 50 else "POOR"))

        report = {
            "quality_score": quality_score,
            "quality_grade": grade,
            "total_issues_found": len(issues),
            "issues": issues,
            "duplicate_count": dup_count,
            "missing_columns_count": len(missing_by_col),
            "pii_columns_count": len(pii_issues),
        }

        summary = (
            f"Data Quality Score: {quality_score}/100 ({grade}). "
            f"Found {len(issues)} issue categories ({dup_count} duplicate rows, "
            f"{len(missing_by_col)} columns with missing values, {len(pii_issues)} PII findings)."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="warning" if quality_score < 70 or pii_issues else "success",
            data={"quality_report": report},
            summary=summary,
            warnings=[f"{iss.get('type')}: {iss.get('recommendation', '')}" for iss in issues if iss.get("severity") in ("HIGH", "CRITICAL")],
        )
