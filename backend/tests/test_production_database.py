"""DataWise AI — Production Database ORM & Integrity Tests."""

import pytest
from datetime import datetime
from sqlalchemy import select

from app.db.models.entities import (
    User,
    Project,
    DatasetEntity,
    DatasetVersion,
    Experiment,
    ExperimentRun,
    ModelEntity,
    ModelVersion,
    Deployment,
    AgentRun,
    AuditLog,
    BackgroundJob,
)
from app.db.session import AsyncSessionLocal, init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_user_and_project_lifecycle():
    import uuid
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"test_engineer_{uuid.uuid4().hex[:8]}@datawise.ai",
            name="Test Engineer",
            password_hash="testhash$12345",
            role="owner",
            status="active",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        assert user.id is not None
        assert user.role == "owner"

        project = Project(
            user_id=user.id,
            name="Fraud Detection Pilot",
            description="Anti-fraud classification workspace",
            status="active",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.id is not None
        assert project.user_id == user.id


@pytest.mark.asyncio
async def test_dataset_versioning_and_experiment_runs():
    import uuid
    async with AsyncSessionLocal() as session:
        # Create dedicated project for test isolation
        user = User(
            email=f"pilot_{uuid.uuid4().hex[:8]}@datawise.ai",
            name="Pilot User",
            password_hash="testhash$12345",
        )
        session.add(user)
        await session.commit()
        project = Project(user_id=user.id, name="Test Project")
        session.add(project)
        await session.commit()
        await session.refresh(project)

        dataset = DatasetEntity(
            project_id=project.id,
            name="Transactions 2026",
            original_filename="transactions.csv",
            file_type="csv",
            file_size=1048576,
            row_count=50000,
            column_count=24,
            status="ready",
        )
        session.add(dataset)
        await session.commit()
        await session.refresh(dataset)

        version = DatasetVersion(
            dataset_id=dataset.id,
            version="1.0.0",
            storage_key=f"projects/{dataset.id}/datasets/v1.csv",
            checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            row_count=50000,
            column_count=24,
            schema_definition={"columns": ["amount", "is_fraud"]},
        )
        session.add(version)
        await session.commit()

        # Create experiment
        experiment = Experiment(
            project_id=project.id,
            dataset_version_id=version.id,
            name="Fraud Classifier LightGBM",
            problem_type="classification",
            target_column="is_fraud",
            objective_metric="f1",
            status="running",
        )
        session.add(experiment)
        await session.commit()
        await session.refresh(experiment)

        run = ExperimentRun(
            experiment_id=experiment.id,
            run_number=1,
            status="completed",
        )
        session.add(run)
        await session.commit()
        assert run.id is not None


@pytest.mark.asyncio
async def test_model_registry_and_deployment_entities():
    import uuid
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"registry_{uuid.uuid4().hex[:8]}@datawise.ai",
            name="Registry User",
            password_hash="testhash$12345",
        )
        session.add(user)
        await session.commit()
        project = Project(user_id=user.id, name="Registry Project")
        session.add(project)
        await session.commit()
        await session.refresh(project)
        proj_id = project.id



        model = ModelEntity(
            project_id=proj_id,
            name="FraudDetectorXGB",
            problem_type="classification",
            status="staging",
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)

        mv = ModelVersion(
            model_id=model.id,
            version="1.0.0",
            framework="xgboost",
            model_type="XGBClassifier",
            status="staging",
            metrics={"auc": 0.98, "f1": 0.91},
        )
        session.add(mv)
        await session.commit()
        await session.refresh(mv)

        dep = Deployment(
            model_version_id=mv.id,
            environment="staging",
            endpoint="/api/v1/predict/fraud-xgb-v1",
            status="healthy",
            deployment_type="realtime",
        )
        session.add(dep)
        await session.commit()
        assert dep.id is not None
