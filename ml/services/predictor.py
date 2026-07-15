"""
Predictor — runs inference using the trained XGBoost fraud detection model.

Loads the XGBoost classifier and label encoder once (lazy singleton) and
exposes a clean ``predict`` API that accepts either raw claim DataFrames
or pre-engineered feature matrices.

The module does **not** apply business-level risk thresholds — it returns
the model's raw prediction and fraud probability so that downstream
components (``analyze.py``, the Fraud Intelligence Agent) can apply their
own categorisation logic.
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from ml.services.feature_builder import FeatureBuilder, FeatureBuilderError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODELS_DIR: Path = Path(__file__).resolve().parent.parent / "models"
_DEFAULT_MODEL_PATH: Path = _MODELS_DIR / "xgboost_fraud_model.pkl"
_DEFAULT_ENCODER_PATH: Path = _MODELS_DIR / "label_encoder.pkl"
_DEFAULT_FEATURE_COLUMNS_PATH: Path = _MODELS_DIR / "feature_columns.json"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PredictorError(Exception):
    """Raised when prediction fails due to invalid input or model errors."""


class ModelLoadError(PredictorError):
    """Raised when the model or encoder artefact cannot be loaded."""


# ---------------------------------------------------------------------------
# Predictor
# ---------------------------------------------------------------------------


class Predictor:
    """Thin wrapper around the trained XGBoost fraud detection model.

    Parameters
    ----------
    model_path : str | Path | None
        Path to the serialised ``XGBClassifier``.  Defaults to
        ``ml/models/xgboost_fraud_model.pkl``.
    encoder_path : str | Path | None
        Path to the serialised ``LabelEncoder``.  Defaults to
        ``ml/models/label_encoder.pkl``.
    feature_columns_path : str | Path | None
        Path to ``feature_columns.json``.  Defaults to the copy shipped
        alongside the trained model under ``ml/models/``.
    """

    # Class-level singleton cache — shared across all instances.
    _model: Optional[XGBClassifier] = None
    _encoder: Optional[Any] = None
    _feature_columns: Optional[List[str]] = None
    _class_labels: Optional[List[str]] = None

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        encoder_path: Optional[Union[str, Path]] = None,
        feature_columns_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._model_path = Path(model_path or _DEFAULT_MODEL_PATH)
        self._encoder_path = Path(encoder_path or _DEFAULT_ENCODER_PATH)
        self._feature_columns_path = Path(
            feature_columns_path or _DEFAULT_FEATURE_COLUMNS_PATH
        )

        # Eagerly load on first instantiation (subsequent calls are no-ops).
        self._ensure_loaded(
            self._model_path, self._encoder_path, self._feature_columns_path
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def feature_columns(self) -> List[str]:
        """Ordered feature names the model expects."""
        return list(Predictor._feature_columns)

    @property
    def class_labels(self) -> List[str]:
        """Human-readable class labels in model-output order."""
        return list(Predictor._class_labels)

    def predict(
        self,
        df: pd.DataFrame,
        *,
        group_by: Optional[str] = "provider_id",
        provider_ids: Optional[pd.Series] = None,
    ) -> List[Dict[str, Any]]:
        """Run fraud prediction on claim data.

        Parameters
        ----------
        df : pd.DataFrame
            Either raw claim-level data (will be passed through
            ``FeatureBuilder``) or an already-engineered feature matrix
            whose columns match ``feature_columns.json``.
        group_by : str | None
            Column in *df* to group raw claims by before feature
            engineering.  Passed directly to
            ``FeatureBuilder.build_features``.  Ignored when *df*
            already contains model features.
        provider_ids : pd.Series | None
            Explicit provider identifiers corresponding to the rows of
            *df* **after** feature engineering.  Use this when *df* is
            already engineered and does not carry a grouping key.
            When *df* is raw claim data and *group_by* is set, provider
            IDs are extracted automatically.

        Returns
        -------
        list[dict]
            One dict per provider with keys:

            - ``provider_id`` — traced from the grouping key or
              *provider_ids*; ``None`` when unavailable.
            - ``prediction`` — human-readable label decoded from the
              model's integer output.
            - ``fraud_probability`` — ``predict_proba`` score for the
              positive (fraud) class.
            - ``confidence`` — ``fraud_probability`` expressed as a
              percentage (0–100).

        Raises
        ------
        PredictorError
            If the input cannot be scored.
        """
        try:
            features_df, resolved_ids = self._prepare_features(
                df, group_by=group_by, provider_ids=provider_ids
            )
        except (FeatureBuilderError, ValueError, FileNotFoundError) as exc:
            raise PredictorError(
                f"Feature preparation failed: {exc}"
            ) from exc

        if features_df.empty:
            return []

        # Validate columns before inference.
        self._validate_columns(features_df)

        # Inference.
        try:
            X = features_df.to_numpy(dtype=np.float32)
            raw_predictions: np.ndarray = Predictor._model.predict(X)
            probabilities: np.ndarray = Predictor._model.predict_proba(X)
        except Exception as exc:
            raise PredictorError(
                f"Model inference failed: {exc}"
            ) from exc

        # The fraud (positive) class probability is at index 1 for binary
        # classifiers.  For multi-class models we locate the class with
        # the highest probability.
        fraud_col_index = self._fraud_class_index(raw_predictions)
        fraud_probs = probabilities[:, fraud_col_index]

        results: List[Dict[str, Any]] = []
        for i in range(len(features_df)):
            class_idx = int(raw_predictions[i])
            results.append(
                {
                    "provider_id": resolved_ids[i] if resolved_ids is not None else None,
                    "prediction": Predictor._class_labels[class_idx],
                    "fraud_probability": float(fraud_probs[i]),
                    "confidence": round(float(fraud_probs[i]) * 100, 2),
                }
            )

        logger.info(
            "[ml/predictor] Generated predictions for %d provider(s)", len(results)
        )
        return results

    # ------------------------------------------------------------------
    # Internal — model loading
    # ------------------------------------------------------------------

    @classmethod
    def _ensure_loaded(
        cls,
        model_path: Path,
        encoder_path: Path,
        feature_columns_path: Path,
    ) -> None:
        """Load model, encoder, and feature columns once (singleton)."""
        if cls._model is not None:
            return

        cls._model = cls._load_model(model_path)
        cls._encoder = cls._load_encoder(encoder_path)
        cls._feature_columns = cls._load_feature_columns(feature_columns_path)
        cls._class_labels = cls._resolve_class_labels()

        logger.info(
            "[ml/predictor] Model loaded — %d classes: %s, %d features",
            len(cls._class_labels),
            cls._class_labels,
            len(cls._feature_columns),
        )

    @staticmethod
    def _load_model(path: Path) -> XGBClassifier:
        """Deserialise the XGBClassifier from disk."""
        if not path.exists():
            raise ModelLoadError(f"Model file not found: {path}")
        try:
            with open(path, "rb") as fh:
                model: XGBClassifier = pickle.load(fh, encoding="latin1")
            return model
        except Exception as exc:
            raise ModelLoadError(
                f"Failed to load XGBoost model from {path}: {exc}"
            ) from exc

    @staticmethod
    def _load_encoder(path: Path) -> Any:
        """Deserialise the LabelEncoder from disk (joblib format)."""
        if not path.exists():
            logger.warning(
                "[ml/predictor] Label encoder not found at %s — "
                "class labels will be integer indices",
                path,
            )
            return None
        try:
            encoder = joblib.load(path)
            return encoder
        except Exception as exc:
            logger.warning(
                "[ml/predictor] Could not load label encoder: %s — "
                "class labels will be integer indices",
                exc,
            )
            return None

    @staticmethod
    def _load_feature_columns(path: Path) -> List[str]:
        """Load the canonical feature names from ``feature_columns.json``."""
        if not path.exists():
            raise ModelLoadError(f"feature_columns.json not found at {path}")
        with open(path, "r", encoding="utf-8") as fh:
            columns: List[str] = json.load(fh)
        if not isinstance(columns, list) or not columns:
            raise ModelLoadError("feature_columns.json must be a non-empty JSON array")
        return columns

    @classmethod
    def _resolve_class_labels(cls) -> List[str]:
        """Map model class indices to human-readable labels.

        Uses the label encoder when available; otherwise falls back to
        the model's own ``classes_`` attribute (integer values) or
        generic ``"class_0"``, ``"class_1"`` labels.
        """
        # Prefer the label encoder if it was loaded successfully.
        if cls._encoder is not None and hasattr(cls._encoder, "classes_"):
            return [str(c) for c in cls._encoder.classes_]

        # Fall back to the model's own class information.
        if hasattr(cls._model, "classes_"):
            return [str(c) for c in cls._model.classes_]

        # Last resort — generate generic names.
        n = cls._model.n_classes_ if hasattr(cls._model, "n_classes_") else 2
        return [f"class_{i}" for i in range(n)]

    # ------------------------------------------------------------------
    # Internal — feature preparation & validation
    # ------------------------------------------------------------------

    def _prepare_features(
        self,
        df: pd.DataFrame,
        *,
        group_by: Optional[str],
        provider_ids: Optional[pd.Series],
    ) -> tuple[pd.DataFrame, Optional[list]]:
        """Determine whether *df* is raw or engineered and return features.

        Returns
        -------
        (features_df, provider_ids_list)
        """
        if df.empty:
            return df, []

        # If *df* already contains model features, skip FeatureBuilder.
        if self._looks_engineered(df):
            ids = (
                list(provider_ids)
                if provider_ids is not None
                else self._extract_ids_from_index(df)
            )
            return df, ids

        # Raw claims — run through FeatureBuilder.
        fb = FeatureBuilder(feature_columns_path=self._feature_columns_path)
        group_col = group_by if group_by and group_by in df.columns else None

        # Extract group keys *before* feature building since
        # FeatureBuilder does not preserve them in the output index.
        ids: Optional[list] = None
        if group_col is not None:
            ids = list(df[group_col].drop_duplicates())

        features_df = fb.build_features(df, group_by=group_col)

        return features_df, ids

    def _looks_engineered(self, df: pd.DataFrame) -> bool:
        """Return ``True`` when *df*'s columns match the model features."""
        return set(Predictor._feature_columns).issubset(set(df.columns))

    @staticmethod
    def _extract_ids_from_index(df: pd.DataFrame) -> Optional[list]:
        """Pull provider IDs from the DataFrame index if available."""
        if df.index.name and df.index.name != "":
            return list(df.index)
        return None

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Ensure *df* has exactly the columns the model expects."""
        expected = set(Predictor._feature_columns)
        actual = set(df.columns)

        missing = expected - actual
        extra = actual - expected

        if missing:
            raise PredictorError(
                f"Engineered features are missing columns required by the model: "
                f"{sorted(missing)}"
            )
        if extra:
            logger.warning(
                "[ml/predictor] Engineered features contain extra columns "
                "not used by the model (will be ignored): %s",
                sorted(extra),
            )

    # ------------------------------------------------------------------
    # Internal — prediction helpers
    # ------------------------------------------------------------------

    def _fraud_class_index(self, raw_predictions: np.ndarray) -> int:
        """Identify which ``predict_proba`` column is the fraud class.

        For binary classifiers the positive class is at index 1.
        For multi-class models we select the class with the highest
        average predicted probability.
        """
        if len(Predictor._class_labels) == 2:
            # Binary — conventionally index 1 is the positive class.
            return 1

        # Multi-class fallback: pick the class that appears most
        # frequently as the predicted label (most likely the positive
        # class in an imbalanced dataset).
        counts = np.bincount(raw_predictions.astype(int))
        return int(np.argmax(counts))

    # ------------------------------------------------------------------
    # Class-level reset (useful for testing)
    # ------------------------------------------------------------------

    @classmethod
    def _reset(cls) -> None:
        """Clear the singleton cache.  For testing only."""
        cls._model = None
        cls._encoder = None
        cls._feature_columns = None
        cls._class_labels = None
