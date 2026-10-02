"""
Agentic AutoML Intelligence Platform — Deployment Package
"""

from deployment.shadow_manager import (
    ShadowInferenceComparison,
    ModelDeploymentManager,
    deployment_manager,
)

__all__ = [
    "ShadowInferenceComparison",
    "ModelDeploymentManager",
    "deployment_manager",
]
