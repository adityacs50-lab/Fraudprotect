"""
SHAP Explainability Layer — generates local explanations for individual
transactions and global feature importance for the fraud model.

Produces human-readable reason codes from SHAP values.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


# Human-readable feature name mappings
FEATURE_DISPLAY_NAMES = {
    "amount": "Transaction Amount",
    "log_amount": "Log Transaction Amount",
    "hour": "Hour of Day",
    "day_of_week": "Day of Week",
    "is_night": "Night-time Transaction",
    "is_weekend": "Weekend Transaction",
    "merchant_risk_score": "Merchant Risk Score",
    "payment_risk_score": "Payment Method Risk",
    "tx_count_1h": "Transactions in Last Hour",
    "tx_count_24h": "Transactions in Last 24 Hours",
    "avg_amount_user": "User Average Amount",
    "std_amount_user": "User Amount Variability",
    "amount_zscore": "Amount Z-Score (vs Baseline)",
    "amount_ratio_to_baseline": "Amount vs User Baseline",
    "distance_from_prev_km": "Distance from Previous Location",
    "speed_kmh": "Implied Travel Speed",
    "is_new_device": "New Device Flag",
    "device_count_user": "Total User Devices",
    "merchant_frequency": "Merchant Familiarity",
}


def _generate_reason(feature: str, value: float, shap_val: float, direction: str) -> str:
    """Generate a human-readable reason code from a SHAP contribution."""
    display = FEATURE_DISPLAY_NAMES.get(feature, feature.replace("_", " ").title())

    if feature == "amount_ratio_to_baseline" and value > 1.5:
        return f"Transaction amount {value:.1f}x user baseline"
    if feature == "is_new_device" and value == 1:
        return "New device not seen before"
    if feature == "distance_from_prev_km" and value > 100:
        return f"Location changed {value:.0f} km from previous transaction"
    if feature == "speed_kmh" and value > 500:
        return f"Impossible travel speed: {value:.0f} km/h"
    if feature == "tx_count_1h" and value >= 3:
        return f"{int(value)} transactions in last hour — velocity spike"
    if feature == "is_night" and value == 1:
        return "Unusual night-time activity (12am–5am)"
    if feature == "merchant_risk_score" and value >= 0.35:
        return "High-risk merchant category"
    if feature == "merchant_frequency" and value < 0.1:
        return "Unusual merchant for this customer profile"
    if feature == "amount_zscore" and value > 2:
        return f"Amount deviates {value:.1f} standard deviations from user norm"
    if feature == "device_count_user" and value > 3:
        return f"User has {int(value)} devices — unusual count"

    return f"{display} {'elevated' if direction == 'positive' else 'reduced'} ({value:.2f})"


class SHAPExplainer:
    """Generate SHAP-based explanations for fraud decisions."""

    def __init__(self, model, feature_columns: List[str]):
        self.model = model
        self.feature_columns = feature_columns
        self.explainer = None
        self.global_importance = None

        if HAS_SHAP:
            try:
                self.explainer = shap.TreeExplainer(model)
            except Exception:
                self.explainer = None

    def explain_single(self, row_features: np.ndarray, row_data: Optional[pd.Series] = None,
                        top_k: int = 5) -> Dict:
        """Explain a single transaction. Returns reason codes and SHAP values."""
        if not HAS_SHAP or self.explainer is None:
            return self._fallback_explain(row_features, row_data, top_k)

        X = row_features.reshape(1, -1)
        shap_values = self.explainer.shap_values(X)

        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            # Binary classification: use class 1 (fraud)
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        else:
            sv = shap_values[0]

        return self._format_explanation(sv, row_features, row_data, top_k)

    def explain_batch(self, df: pd.DataFrame, top_k: int = 5) -> List[Dict]:
        """Explain a batch of transactions."""
        X = df[self.feature_columns].fillna(0).values
        explanations = []

        if HAS_SHAP and self.explainer is not None:
            shap_values = self.explainer.shap_values(X)
            if isinstance(shap_values, list):
                sv_array = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            else:
                sv_array = shap_values

            for i in range(len(df)):
                row_data = df.iloc[i]
                exp = self._format_explanation(sv_array[i], X[i], row_data, top_k)
                explanations.append(exp)
        else:
            for i in range(len(df)):
                row_data = df.iloc[i]
                exp = self._fallback_explain(X[i], row_data, top_k)
                explanations.append(exp)

        return explanations

    def compute_global_importance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Compute global feature importance using mean |SHAP|."""
        X = df[self.feature_columns].fillna(0).values

        if HAS_SHAP and self.explainer is not None:
            shap_values = self.explainer.shap_values(X)
            if isinstance(shap_values, list):
                sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            else:
                sv = shap_values

            importance = np.abs(sv).mean(axis=0)
        else:
            # Fallback to model feature importance
            if hasattr(self.model, "feature_importances_"):
                importance = self.model.feature_importances_
            else:
                importance = np.ones(len(self.feature_columns))

        total = importance.sum() + 1e-8
        self.global_importance = {
            self.feature_columns[i]: round(float(importance[i] / total), 4)
            for i in range(len(self.feature_columns))
        }

        # Sort descending
        self.global_importance = dict(
            sorted(self.global_importance.items(), key=lambda x: x[1], reverse=True)
        )
        return self.global_importance

    def _format_explanation(self, shap_vals: np.ndarray, features: np.ndarray,
                             row_data: Optional[pd.Series], top_k: int) -> Dict:
        """Format SHAP values into structured explanation."""
        # Pair features with SHAP values
        pairs = list(zip(self.feature_columns, shap_vals, features))
        # Sort by absolute SHAP value
        pairs.sort(key=lambda x: abs(x[1]), reverse=True)

        reasons = []
        shap_details = []
        for feat, sv, val in pairs[:top_k]:
            direction = "positive" if sv > 0 else "negative"
            reason = _generate_reason(feat, float(val), float(sv), direction)
            reasons.append(reason)
            shap_details.append({
                "feature": feat,
                "display_name": FEATURE_DISPLAY_NAMES.get(feat, feat),
                "value": round(float(val), 4),
                "shap_value": round(float(sv), 4),
                "direction": direction,
                "reason": reason,
            })

        base_value = float(self.explainer.expected_value[1]) if isinstance(
            self.explainer.expected_value, (list, np.ndarray)
        ) else float(self.explainer.expected_value)

        return {
            "reason_codes": reasons,
            "shap_details": shap_details,
            "base_value": round(base_value, 4),
            "output_value": round(base_value + float(np.sum(shap_vals)), 4),
        }

    def _fallback_explain(self, features: np.ndarray, row_data: Optional[pd.Series],
                           top_k: int) -> Dict:
        """Fallback explanation using feature importances when SHAP not available."""
        if hasattr(self.model, "feature_importances_"):
            imp = self.model.feature_importances_
        else:
            imp = np.ones(len(self.feature_columns))

        pairs = list(zip(self.feature_columns, imp, features))
        pairs.sort(key=lambda x: abs(x[1] * x[2]), reverse=True)

        reasons = []
        shap_details = []
        for feat, importance, val in pairs[:top_k]:
            contrib = importance * val
            direction = "positive" if contrib > 0 else "negative"
            reason = _generate_reason(feat, float(val), float(contrib), direction)
            reasons.append(reason)
            shap_details.append({
                "feature": feat,
                "display_name": FEATURE_DISPLAY_NAMES.get(feat, feat),
                "value": round(float(val), 4),
                "shap_value": round(float(contrib), 4),
                "direction": direction,
                "reason": reason,
            })

        return {
            "reason_codes": reasons,
            "shap_details": shap_details,
            "base_value": 0.0,
            "output_value": 0.0,
        }
