"""
Feature Builder — recreates the exact feature engineering pipeline used during model training.

The trained XGBoost model expects 12 aggregate (provider-level) features.
This module transforms raw claim-level data into those aggregated features,
ensuring column names and ordering match ``feature_columns.json`` exactly.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
_DEFAULT_FEATURE_COLUMNS_PATH = _MODELS_DIR / "feature_columns.json"

# Raw claim columns required to compute every aggregate feature.
REQUIRED_INPUT_COLUMNS: List[str] = [
    "beneficiary_id",
    "attending_physician",
    "claim_amount",
    "deductible",
    "claim_type",
    "claim_duration",
    "diagnosis_codes",
    "chronic_condition_count",
]

# Canonical inpatient / outpatient keywords (case-insensitive matching).
_INPATIENT_KEYWORDS: set[str] = {"inpatient", "ip", "in-patient"}
_OUTPATIENT_KEYWORDS: set[str] = {"outpatient", "op", "out-patient"}

# Default fill values used when a column has missing data.
_DEFAULT_FILL = {
    "claim_amount": 0.0,
    "deductible": 0.0,
    "claim_duration": 0.0,
    "chronic_condition_count": 0,
}


class FeatureBuilderError(Exception):
    """Raised when feature construction fails due to invalid input."""


class FeatureBuilder:
    """Builds the 12 model-ready aggregate features from raw claim data.

    Parameters
    ----------
    feature_columns_path : str | Path | None
        Path to ``feature_columns.json``.  Defaults to the copy shipped
        alongside the trained model under ``ml/models/``.
    """

    def __init__(
        self,
        feature_columns_path: Optional[str | Path] = None,
    ) -> None:
        self._feature_columns_path = Path(
            feature_columns_path or _DEFAULT_FEATURE_COLUMNS_PATH
        )
        self._feature_columns: List[str] = self._load_feature_columns()
        logger.info(
            "FeatureBuilder initialised — expecting %d features: %s",
            len(self._feature_columns),
            self._feature_columns,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def feature_columns(self) -> List[str]:
        """Ordered list of feature names the model expects."""
        return list(self._feature_columns)

    def validate_input(self, df: pd.DataFrame) -> None:
        """Raise ``FeatureBuilderError`` if *df* is missing required columns.

        Columns that are optional but helpful (e.g. ``provider_id``) are not
        enforced here — callers can group before invoking ``build_features``.
        """
        missing = [c for c in REQUIRED_INPUT_COLUMNS if c not in df.columns]
        if missing:
            raise FeatureBuilderError(
                f"Claim data is missing required columns: {missing}. "
                f"Expected columns: {REQUIRED_INPUT_COLUMNS}"
            )

    def build_features(
        self,
        df: pd.DataFrame,
        group_by: Optional[str] = "provider_id",
    ) -> pd.DataFrame:
        """Transform raw claim rows into model-ready aggregate features.

        Parameters
        ----------
        df : pd.DataFrame
            Raw claim-level data.  Must contain every column listed in
            ``REQUIRED_INPUT_COLUMNS``.
        group_by : str | None
            Column to group claims by (e.g. ``"provider_id"``).  When
            ``None``, all rows are treated as belonging to a single group
            and a one-row DataFrame is returned.

        Returns
        -------
        pd.DataFrame
            DataFrame with exactly the columns from ``feature_columns.json``,
            in the correct order.  One row per group.
        """
        self.validate_input(df)

        working = df.copy()
        working = self._normalise_input(working)
        working = self._handle_missing_values(working)

        if group_by is not None and group_by in working.columns:
            aggregated = self._aggregate_by_group(working, group_by)
        else:
            aggregated = self._aggregate_single_group(working)

        # Ensure column order matches the trained model exactly.
        aggregated = aggregated.reindex(columns=self._feature_columns, fill_value=0)

        logger.info(
            "Built features for %d group(s), shape: %s",
            len(aggregated),
            aggregated.shape,
        )
        return aggregated

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_feature_columns(self) -> List[str]:
        """Load the canonical feature names from ``feature_columns.json``."""
        if not self._feature_columns_path.exists():
            raise FileNotFoundError(
                f"feature_columns.json not found at {self._feature_columns_path}"
            )
        with open(self._feature_columns_path, "r", encoding="utf-8") as fh:
            columns: List[str] = json.load(fh)
        if not isinstance(columns, list) or not columns:
            raise ValueError("feature_columns.json must be a non-empty JSON array")
        return columns

    # ----- input normalisation ----------------------------------------------

    def _normalise_input(self, df: pd.DataFrame) -> pd.DataFrame:
        """Coerce types and lowercase string columns for consistent matching."""
        # Ensure numeric columns are actually numeric.
        for col in ("claim_amount", "deductible", "claim_duration"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["chronic_condition_count"] = pd.to_numeric(
            df["chronic_condition_count"], errors="coerce"
        ).fillna(0).astype(int)

        # Normalise claim_type to lowercase strings for keyword matching.
        # Fill NaN first so .astype(str) doesn't produce "nan" literals.
        df["claim_type"] = (
            df["claim_type"]
            .fillna("unknown")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        # Ensure diagnosis_codes is always a list of strings.
        if "diagnosis_codes" in df.columns:
            df["diagnosis_codes"] = df["diagnosis_codes"].apply(self._parse_codes)

        return df

    # ----- missing-value handling -------------------------------------------

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill NaN / None values with safe defaults before aggregation."""
        for col, default in _DEFAULT_FILL.items():
            if col in df.columns:
                df[col] = df[col].fillna(default)

        # Categorical / identifier columns: fill with sentinel strings.
        for col in ("beneficiary_id", "attending_physician"):
            if col in df.columns:
                df[col] = df[col].fillna("UNKNOWN")

        return df

    # ----- aggregation ------------------------------------------------------

    def _aggregate_by_group(
        self,
        df: pd.DataFrame,
        group_by: str,
    ) -> pd.DataFrame:
        """Compute per-group aggregate features."""
        groups = df.groupby(group_by, sort=False)
        records: List[dict] = []

        for _group_key, group_df in groups:
            records.append(self._compute_aggregates(group_df))

        return pd.DataFrame(records)

    def _aggregate_single_group(self, df: pd.DataFrame) -> pd.DataFrame:
        """Treat the entire DataFrame as one group."""
        return pd.DataFrame([self._compute_aggregates(df)])

    def _compute_aggregates(self, df: pd.DataFrame) -> dict:
        """Compute the 12 model features from a single group of claims.

        This is the core feature-engineering logic that must mirror the
        training-time pipeline exactly.
        """
        total_claims = len(df)
        total_reimbursement = float(df["claim_amount"].sum())
        average_claim_amount = float(df["claim_amount"].mean()) if total_claims > 0 else 0.0
        total_deductible = float(df["deductible"].sum())
        unique_beneficiaries = int(df["beneficiary_id"].nunique())
        unique_attending_physicians = int(df["attending_physician"].nunique())
        average_claim_duration = float(df["claim_duration"].mean()) if total_claims > 0 else 0.0

        # Claim-type counts (inpatient vs outpatient).
        inpatient_mask = df["claim_type"].apply(self._is_inpatient)
        outpatient_mask = df["claim_type"].apply(self._is_outpatient)
        inpatient_claims = int(inpatient_mask.sum())
        outpatient_claims = int(outpatient_mask.sum())

        # Inpatient-to-outpatient ratio.  Avoid division by zero.
        if outpatient_claims > 0:
            ratio = inpatient_claims / outpatient_claims
        elif inpatient_claims > 0:
            # All claims are inpatient — represent as a large ratio.
            ratio = float(inpatient_claims)
        else:
            ratio = 0.0

        # Percentage of beneficiaries with 3+ chronic conditions.
        if unique_beneficiaries > 0 and "chronic_condition_count" in df.columns:
            beneficiaries_3plus = (
                df.groupby("beneficiary_id")["chronic_condition_count"]
                .max()
                .ge(3)
                .sum()
            )
            pct_beneficiaries_3plus = float(beneficiaries_3plus / unique_beneficiaries)
        else:
            pct_beneficiaries_3plus = 0.0

        # Distinct diagnosis codes across all claims in the group.
        if "diagnosis_codes" in df.columns:
            all_codes: set[str] = set()
            for codes in df["diagnosis_codes"]:
                if isinstance(codes, list):
                    all_codes.update(codes)
            distinct_diagnosis_codes = len(all_codes)
        else:
            distinct_diagnosis_codes = 0

        return {
            "TotalClaims": total_claims,
            "TotalReimbursement": total_reimbursement,
            "AverageClaimAmount": average_claim_amount,
            "TotalDeductible": total_deductible,
            "UniqueBeneficiaries": unique_beneficiaries,
            "UniqueAttendingPhysicians": unique_attending_physicians,
            "AverageClaimDuration": average_claim_duration,
            "InpatientClaims": inpatient_claims,
            "OutpatientClaims": outpatient_claims,
            "Ratio": ratio,
            "PctBeneficiaries3PlusChronic": pct_beneficiaries_3plus,
            "DistinctDiagnosisCodes": distinct_diagnosis_codes,
        }

    # ----- classification helpers -------------------------------------------

    @staticmethod
    def _is_inpatient(claim_type: object) -> bool:
        """Return ``True`` if the normalised claim type is inpatient."""
        ct = str(claim_type).lower()
        return any(kw in ct for kw in _INPATIENT_KEYWORDS)

    @staticmethod
    def _is_outpatient(claim_type: object) -> bool:
        """Return ``True`` if the normalised claim type is outpatient."""
        ct = str(claim_type).lower()
        return any(kw in ct for kw in _OUTPATIENT_KEYWORDS)

    @staticmethod
    def _parse_codes(value: object) -> list[str]:
        """Parse a diagnosis/procedure code field into a list of strings.

        Handles:
        - Already a list → returned as-is
        - Comma-separated string → split
        - Semicolon-separated string → split
        - Single code → wrapped in a list
        - None / NaN → empty list
        """
        if isinstance(value, list):
            return [str(c).strip() for c in value if str(c).strip()]
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            # Handle both comma and semicolon separators.
            for sep in (";", ","):
                if sep in value:
                    return [c.strip() for c in value.split(sep) if c.strip()]
            return [value]
        return []
