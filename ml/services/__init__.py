"""
ML services package for the FraudShield system.

Contains the core service modules: feature engineering, prediction,
risk scoring, explainability, investigation persistence, and report
generation.
"""

from ml.services.explainability import ExplainabilityEngine
from ml.services.feature_builder import FeatureBuilder
from ml.services.investigation_repository import InvestigationRepository
from ml.services.pipeline import Pipeline
from ml.services.predictor import Predictor
from ml.services.report_generator import generate_report
from ml.services.risk_scorer import RiskScorer

__all__ = [
    "ExplainabilityEngine",
    "FeatureBuilder",
    "InvestigationRepository",
    "Pipeline",
    "Predictor",
    "RiskScorer",
    "generate_report",
]
