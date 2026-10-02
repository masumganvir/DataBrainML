"""
DataWise AI — Analysis Endpoints

APIs for profiling datasets, running statistical scans, and generating analytical summaries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.db_models import Dataset, Session
from app.tools.profiler import profile_dataframe
from app.tools.storage import storage_manager

router = APIRouter()


# ------------------------------------------------------------------ #
#  Schemas
# ------------------------------------------------------------------ #

class ColumnProfileResponse(BaseModel):
    name: str
    dtype: str
    unique_count: int
    unique_ratio: float
    missing_count: int
    missing_pct: float
    detected_type: Optional[str] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[Any] = None
    std: Optional[float] = None
    variance: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None
    iqr: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    zero_count: Optional[int] = None
    negative_count: Optional[int] = None
    is_identifier: bool = False
    is_constant: bool = False
    is_near_constant: bool = False


class ClassificationResponse(BaseModel):
    numerical: List[str]
    categorical: List[str]
    binary: List[str]
    datetime: List[str]
    text: List[str]
    identifiers: List[str]
    constants: List[str]
    near_constants: List[str]


class ProfileReportResponse(BaseModel):
    session_id: str
    dataset_id: str
    total_rows: int
    total_columns: int
    memory_usage_bytes: int
    has_duplicates: bool
    duplicate_rows_count: int
    classification: ClassificationResponse
    column_profiles: List[ColumnProfileResponse]


# ------------------------------------------------------------------ #
#  Endpoints
# ------------------------------------------------------------------ #

@router.post(
    "/{session_id}/datasets/{dataset_id}/profile",
    response_model=ProfileReportResponse,
    summary="Compute full statistical profile for a dataset",
)
async def run_dataset_profiling(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Autonomously inspects all columns, calculates comprehensive statistics,
    classifies column types, and detects constants / identifiers.
    """
    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found in session '{session_id}'.",
        )

    try:
        df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dataset: {str(exc)}",
        )

    # Run profiler
    profile_data = profile_dataframe(df)

    # Persist summary into dataset record
    dataset.profile_summary = profile_data

    # Update session stage
    sess_query = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_query.scalar_one_or_none()
    if session:
        session.current_stage = "DATA_QUALITY"

    await db.commit()

    return ProfileReportResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        total_rows=profile_data["total_rows"],
        total_columns=profile_data["total_columns"],
        memory_usage_bytes=profile_data["memory_usage_bytes"],
        has_duplicates=profile_data["has_duplicates"],
        duplicate_rows_count=profile_data["duplicate_rows_count"],
        classification=ClassificationResponse(**profile_data["classification"]),
        column_profiles=[ColumnProfileResponse(**c) for c in profile_data["column_profiles"]],
    )


@router.get(
    "/{session_id}/datasets/{dataset_id}/profile",
    response_model=ProfileReportResponse,
    summary="Retrieve previously computed profile report",
)
async def get_dataset_profile(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns the cached profile report if available, or computes it on the fly."""
    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    if dataset.profile_summary:
        profile_data = dataset.profile_summary
    else:
        # Compute if not cached
        df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
        profile_data = profile_dataframe(df)
        dataset.profile_summary = profile_data
        await db.commit()

    return ProfileReportResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        total_rows=profile_data["total_rows"],
        total_columns=profile_data["total_columns"],
        memory_usage_bytes=profile_data["memory_usage_bytes"],
        has_duplicates=profile_data["has_duplicates"],
        duplicate_rows_count=profile_data["duplicate_rows_count"],
        classification=ClassificationResponse(**profile_data["classification"]),
        column_profiles=[ColumnProfileResponse(**c) for c in profile_data["column_profiles"]],
    )


# ------------------------------------------------------------------ #
#  Quality & Missing Value Schemas & Endpoints
# ------------------------------------------------------------------ #

class MissingReportResponse(BaseModel):
    column: str
    missing_count: int
    missing_pct: float
    dtype: str
    severity: str
    recommended_strategy: str
    alternative_strategies: List[str]
    explanation: str


class DuplicatesResponse(BaseModel):
    has_duplicates: bool
    duplicate_count: int
    duplicate_pct: float
    sample_duplicates: List[Dict[str, Any]]
    recommendation: str


class QualityReportResponse(BaseModel):
    session_id: str
    dataset_id: str
    total_rows: int
    total_columns: int
    total_missing_cells: int
    overall_missing_pct: float
    columns_with_missing_count: int
    missing_reports: List[MissingReportResponse]
    duplicates: DuplicatesResponse


@router.post(
    "/{session_id}/datasets/{dataset_id}/quality",
    response_model=QualityReportResponse,
    summary="Analyze missing values and duplicates for a dataset",
)
async def run_quality_analysis(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates missing values across severity levels, provides adaptive
    imputation strategies, and checks for duplicate rows.
    """
    from app.tools.quality import analyze_data_quality

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    quality_data = analyze_data_quality(df)

    dataset.quality_summary = quality_data

    # Update session stage
    sess_query = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_query.scalar_one_or_none()
    if session:
        session.current_stage = "OUTLIER_DETECTION"

    await db.commit()

    return QualityReportResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        total_rows=quality_data["total_rows"],
        total_columns=quality_data["total_columns"],
        total_missing_cells=quality_data["total_missing_cells"],
        overall_missing_pct=quality_data["overall_missing_pct"],
        columns_with_missing_count=quality_data["columns_with_missing_count"],
        missing_reports=[MissingReportResponse(**r) for r in quality_data["missing_reports"]],
        duplicates=DuplicatesResponse(**quality_data["duplicates"]),
    )


@router.get(
    "/{session_id}/datasets/{dataset_id}/quality",
    response_model=QualityReportResponse,
    summary="Retrieve previously computed quality report",
)
async def get_quality_report(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.tools.quality import analyze_data_quality

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    if dataset.quality_summary:
        quality_data = dataset.quality_summary
    else:
        df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
        quality_data = analyze_data_quality(df)
        dataset.quality_summary = quality_data
        await db.commit()

    return QualityReportResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        total_rows=quality_data["total_rows"],
        total_columns=quality_data["total_columns"],
        total_missing_cells=quality_data["total_missing_cells"],
        overall_missing_pct=quality_data["overall_missing_pct"],
        columns_with_missing_count=quality_data["columns_with_missing_count"],
        missing_reports=[MissingReportResponse(**r) for r in quality_data["missing_reports"]],
        duplicates=DuplicatesResponse(**quality_data["duplicates"]),
    )


# ------------------------------------------------------------------ #
#  Outlier Schemas & Endpoints
# ------------------------------------------------------------------ #

class SingleOutlierReportResponse(BaseModel):
    column: str
    method: str
    outlier_count: int
    outlier_pct: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    severity: str
    interpretation: str


class IsolationForestResponse(BaseModel):
    method: str
    contamination_param: float
    outlier_count: int
    outlier_pct: float
    sample_outlier_indices: List[int]
    severity: str
    recommendation: str


class OutlierSuiteResponse(BaseModel):
    session_id: str
    dataset_id: str
    numerical_columns_analyzed: List[str]
    iqr_reports: List[SingleOutlierReportResponse]
    zscore_reports: List[SingleOutlierReportResponse]
    mad_reports: List[SingleOutlierReportResponse]
    isolation_forest: IsolationForestResponse


@router.post(
    "/{session_id}/datasets/{dataset_id}/outliers",
    response_model=OutlierSuiteResponse,
    summary="Detect and evaluate outliers across numerical features",
)
async def run_outlier_analysis(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs multi-method outlier analysis using IQR (1.5x), Z-score (3.0),
    MAD (3.5), and unsupervised Isolation Forest.
    """
    from app.tools.outliers import analyze_dataset_outliers

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    outlier_data = analyze_dataset_outliers(df)

    # Cache in dataset record metadata or session
    sess_query = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_query.scalar_one_or_none()
    if session:
        session.current_stage = "VISUALIZATION"
    await db.commit()

    return OutlierSuiteResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        numerical_columns_analyzed=outlier_data["numerical_columns_analyzed"],
        iqr_reports=[SingleOutlierReportResponse(**r) for r in outlier_data["iqr_reports"]],
        zscore_reports=[SingleOutlierReportResponse(**r) for r in outlier_data["zscore_reports"]],
        mad_reports=[SingleOutlierReportResponse(**r) for r in outlier_data["mad_reports"]],
        isolation_forest=IsolationForestResponse(**outlier_data["isolation_forest"]),
    )


@router.get(
    "/{session_id}/datasets/{dataset_id}/outliers",
    response_model=OutlierSuiteResponse,
    summary="Retrieve outlier scan results",
)
async def get_outlier_analysis(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.tools.outliers import analyze_dataset_outliers

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    outlier_data = analyze_dataset_outliers(df)

    return OutlierSuiteResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        numerical_columns_analyzed=outlier_data["numerical_columns_analyzed"],
        iqr_reports=[SingleOutlierReportResponse(**r) for r in outlier_data["iqr_reports"]],
        zscore_reports=[SingleOutlierReportResponse(**r) for r in outlier_data["zscore_reports"]],
        mad_reports=[SingleOutlierReportResponse(**r) for r in outlier_data["mad_reports"]],
        isolation_forest=IsolationForestResponse(**outlier_data["isolation_forest"]),
    )


# ------------------------------------------------------------------ #
#  Visualization Schemas & Endpoints
# ------------------------------------------------------------------ #

class VisualizationResponse(BaseModel):
    chart_type: str
    column: Optional[str] = None
    title: str
    html_path: str
    figure_json: Dict[str, Any]
    interpretation: str


class VisualizationSuiteResponse(BaseModel):
    session_id: str
    dataset_id: str
    visualizations: List[VisualizationResponse]


@router.post(
    "/{session_id}/datasets/{dataset_id}/visualizations/suite",
    response_model=VisualizationSuiteResponse,
    summary="Generate an autonomous suite of Plotly charts with AI interpretation",
)
async def generate_visualization_suite(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Constructs smart distribution histograms, bar charts, correlation heatmaps,
    and bivariate scatter plots with dark theme styling.
    """
    from app.models.db_models import Artifact
    from app.tools.visualization import VisualizationEngine

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    engine = VisualizationEngine(df, session_id=session_id)
    plot_results = engine.generate_recommended_suite(max_plots=6)

    # Persist artifacts in database
    for p in plot_results:
        artifact = Artifact(
            session_id=session_id,
            artifact_type="plot",
            name=p["title"],
            description=p["interpretation"],
            file_path=p["html_path"],
            file_format="html",
            file_size_bytes=len(p["html_path"]),
            artifact_metadata={"chart_type": p["chart_type"], "column": p["column"]},
        )
        db.add(artifact)

    sess_query = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_query.scalar_one_or_none()
    if session:
        session.current_stage = "CORRELATION_ANALYSIS"

    await db.commit()

    return VisualizationSuiteResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        visualizations=[VisualizationResponse(**p) for p in plot_results],
    )


@router.post(
    "/{session_id}/datasets/{dataset_id}/visualizations/column/{column_name}",
    response_model=VisualizationResponse,
    summary="Generate tailored visualization for a specific column",
)
async def generate_column_visualization(
    session_id: str,
    dataset_id: str,
    column_name: str,
    db: AsyncSession = Depends(get_db),
):
    from app.tools.visualization import VisualizationEngine

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    if column_name not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Column '{column_name}' not found in dataset.",
        )

    engine = VisualizationEngine(df, session_id=session_id)
    col_series = df[column_name]

    if pd.api.types.is_numeric_dtype(col_series) and not pd.api.types.is_bool_dtype(col_series):
        plot = engine.plot_numerical_distribution(column_name)
    else:
        plot = engine.plot_categorical_distribution(column_name)

    return VisualizationResponse(**plot)


# ------------------------------------------------------------------ #
#  Distribution & Normality Schemas & Endpoints
# ------------------------------------------------------------------ #

class NormalityResponse(BaseModel):
    test_name: str
    statistic: float
    p_value: float
    is_normal: bool
    sample_size: int


class TransformationRecommendationResponse(BaseModel):
    recommended_transformation: str
    alternative_transformations: List[str]
    rationale: str


class ColumnDistributionResponse(BaseModel):
    column: str
    skewness: float
    skewness_category: str
    kurtosis: float
    kurtosis_category: str
    normality: NormalityResponse
    transformation_recommendation: TransformationRecommendationResponse


class DistributionsReportResponse(BaseModel):
    session_id: str
    dataset_id: str
    analyzed_columns_count: int
    columns: List[ColumnDistributionResponse]


@router.post(
    "/{session_id}/datasets/{dataset_id}/distributions",
    response_model=DistributionsReportResponse,
    summary="Evaluate normality, skewness, and transformation recommendations",
)
async def run_distribution_analysis(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.tools.distributions import analyze_distributions

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    dist_data = analyze_distributions(df)

    return DistributionsReportResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        analyzed_columns_count=dist_data["analyzed_columns_count"],
        columns=[ColumnDistributionResponse(**c) for c in dist_data["columns"]],
    )


@router.get(
    "/{session_id}/datasets/{dataset_id}/distributions",
    response_model=DistributionsReportResponse,
    summary="Retrieve distribution analysis",
)
async def get_distribution_analysis(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.tools.distributions import analyze_distributions

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    dist_data = analyze_distributions(df)

    return DistributionsReportResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        analyzed_columns_count=dist_data["analyzed_columns_count"],
        columns=[ColumnDistributionResponse(**c) for c in dist_data["columns"]],
    )


# ------------------------------------------------------------------ #
#  Correlation & Multicollinearity Schemas & Endpoints
# ------------------------------------------------------------------ #

class CorrelationPairResponse(BaseModel):
    feature_1: str
    feature_2: str
    pearson_r: float
    absolute_r: float
    strength: str
    recommendation: Dict[str, Any]


class CorrelationReportResponse(BaseModel):
    session_id: str
    dataset_id: str
    columns_count: int
    columns: List[str]
    high_correlation_pairs: List[CorrelationPairResponse]
    high_correlation_count: int
    multicollinearity_risk: str


@router.post(
    "/{session_id}/datasets/{dataset_id}/correlations",
    response_model=CorrelationReportResponse,
    summary="Detect feature correlations and multicollinearity risks",
)
async def run_correlation_analysis(
    session_id: str,
    dataset_id: str,
    threshold: float = 0.80,
    db: AsyncSession = Depends(get_db),
):
    from app.tools.correlations import analyze_correlations

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    corr_data = analyze_correlations(df, threshold=threshold)

    sess_query = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_query.scalar_one_or_none()
    if session:
        session.current_stage = "PREPROCESSING_RECOMMENDATIONS"
    await db.commit()

    return CorrelationReportResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        columns_count=corr_data["columns_count"],
        columns=corr_data["columns"],
        high_correlation_pairs=[CorrelationPairResponse(**p) for p in corr_data["high_correlation_pairs"]],
        high_correlation_count=corr_data["high_correlation_count"],
        multicollinearity_risk=corr_data["multicollinearity_risk"],
    )


@router.get(
    "/{session_id}/datasets/{dataset_id}/correlations",
    response_model=CorrelationReportResponse,
    summary="Retrieve correlation and multicollinearity report",
)
async def get_correlation_analysis(
    session_id: str,
    dataset_id: str,
    threshold: float = 0.80,
    db: AsyncSession = Depends(get_db),
):
    from app.tools.correlations import analyze_correlations

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)
    corr_data = analyze_correlations(df, threshold=threshold)

    return CorrelationReportResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        columns_count=corr_data["columns_count"],
        columns=corr_data["columns"],
        high_correlation_pairs=[CorrelationPairResponse(**p) for p in corr_data["high_correlation_pairs"]],
        high_correlation_count=corr_data["high_correlation_count"],
        multicollinearity_risk=corr_data["multicollinearity_risk"],
    )


# ------------------------------------------------------------------ #
#  Preprocessing Recommendation Schemas & Endpoints
# ------------------------------------------------------------------ #

class PreprocessingSuiteResponse(BaseModel):
    session_id: str
    dataset_id: str
    imputation_plan: List[Dict[str, Any]]
    encoding_plan: List[Dict[str, Any]]
    scaling_plan: List[Dict[str, Any]]
    transformation_plan: List[Dict[str, Any]]
    destructive_actions: List[Dict[str, Any]]
    human_approval_required: bool


@router.post(
    "/{session_id}/datasets/{dataset_id}/preprocessing/recommendations",
    response_model=PreprocessingSuiteResponse,
    summary="Generate unified preprocessing recommendation suite",
)
async def generate_preprocessing_recommendations(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Combines imputation, encoding, scaling, and transformation recommendations.
    Flags any destructive action (e.g. dropping columns with critical missingness or collinearity)
    that requires human approval.
    """
    from app.tools.encoding import recommend_categorical_encoding
    from app.tools.quality import analyze_data_quality
    from app.tools.scaling import recommend_numerical_scaling
    from app.tools.transformation import recommend_transformations

    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    df = storage_manager.load_dataframe(dataset.file_path, dataset.file_format)

    quality_res = analyze_data_quality(df)
    imputation_plan = quality_res["missing_reports"]
    encoding_plan = recommend_categorical_encoding(df)
    scaling_plan = recommend_numerical_scaling(df)
    transformation_plan = recommend_transformations(df)

    # Detect destructive actions requiring human sign-off
    destructive_actions = []
    for r in imputation_plan:
        if r["recommended_strategy"] == "drop_column":
            destructive_actions.append({
                "action": "drop_column",
                "target": r["column"],
                "reason": f"High missingness ({r['missing_pct']}%)",
                "severity": "high",
            })

    for e in encoding_plan:
        if e["strategy"] == "drop_or_id":
            destructive_actions.append({
                "action": "drop_column",
                "target": e["column"],
                "reason": f"Identifier / near-unique column ({e['cardinality']} unique values)",
                "severity": "medium",
            })

    sess_query = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_query.scalar_one_or_none()
    if session:
        session.current_stage = "HUMAN_APPROVAL" if destructive_actions else "FEATURE_ENGINEERING"
    await db.commit()

    return PreprocessingSuiteResponse(
        session_id=session_id,
        dataset_id=dataset_id,
        imputation_plan=imputation_plan,
        encoding_plan=encoding_plan,
        scaling_plan=scaling_plan,
        transformation_plan=transformation_plan,
        destructive_actions=destructive_actions,
        human_approval_required=len(destructive_actions) > 0,
    )


@router.get(
    "/{session_id}/datasets/{dataset_id}/preprocessing/recommendations",
    response_model=PreprocessingSuiteResponse,
    summary="Retrieve preprocessing recommendations",
)
async def get_preprocessing_recommendations(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await generate_preprocessing_recommendations(session_id, dataset_id, db)
