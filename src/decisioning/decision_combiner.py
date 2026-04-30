"""
Decision Combiner — merges rule severity, anomaly score, and fraud probability
into a final triage action: APPROVE, REVIEW, or BLOCK.

Thresholds are configurable to support threshold tuning for FPR reduction.
"""

from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np


@dataclass
class DecisionThresholds:
    """Configurable thresholds for the decision combiner."""
    # Block thresholds
    block_fraud_prob: float = 0.85
    block_rule_severity: str = "critical"
    block_combined_score: float = 0.80

    # Review thresholds
    review_fraud_prob: float = 0.40
    review_anomaly_score: float = 0.70
    review_rule_score: float = 0.40
    review_combined_score: float = 0.45

    # Weights for combined score
    weight_fraud_prob: float = 0.45
    weight_anomaly: float = 0.25
    weight_rules: float = 0.30


class DecisionCombiner:
    """Combine rule, anomaly, and ML outputs into a triage decision."""

    def __init__(self, thresholds: Optional[DecisionThresholds] = None):
        self.thresholds = thresholds or DecisionThresholds()

    def decide_single(self, fraud_prob: float, anomaly_score: float,
                       rule_score: float, rule_severity: str) -> dict:
        """Decide action for a single transaction."""
        t = self.thresholds

        # Combined weighted score
        combined = (
            t.weight_fraud_prob * fraud_prob +
            t.weight_anomaly * anomaly_score +
            t.weight_rules * rule_score
        )

        # BLOCK conditions
        if (rule_severity == "critical" and fraud_prob > 0.5) or \
           fraud_prob >= t.block_fraud_prob or \
           combined >= t.block_combined_score:
            action = "BLOCK"
            risk_level = "critical"

        # REVIEW conditions
        elif fraud_prob >= t.review_fraud_prob or \
             anomaly_score >= t.review_anomaly_score or \
             rule_score >= t.review_rule_score or \
             combined >= t.review_combined_score:
            action = "REVIEW"
            risk_level = "high" if combined > 0.6 else "medium"

        # APPROVE
        else:
            action = "APPROVE"
            risk_level = "low"

        return {
            "action": action,
            "risk_level": risk_level,
            "combined_score": round(combined, 4),
            "fraud_probability": round(fraud_prob, 4),
            "anomaly_score": round(anomaly_score, 4),
            "rule_score": round(rule_score, 4),
        }

    def decide_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply decisioning to entire DataFrame."""
        df = df.copy()
        actions = []
        risk_levels = []
        combined_scores = []

        for _, row in df.iterrows():
            result = self.decide_single(
                fraud_prob=row.get("fraud_probability", 0),
                anomaly_score=row.get("anomaly_score", 0),
                rule_score=row.get("rule_score", 0),
                rule_severity=row.get("rule_severity", "none"),
            )
            actions.append(result["action"])
            risk_levels.append(result["risk_level"])
            combined_scores.append(result["combined_score"])

        df["decision"] = actions
        df["risk_level"] = risk_levels
        df["combined_score"] = combined_scores
        return df

    def get_decision_stats(self, df: pd.DataFrame) -> dict:
        """Compute operational stats from decisioned DataFrame."""
        total = len(df)
        if total == 0:
            return {}

        n_block = len(df[df["decision"] == "BLOCK"])
        n_review = len(df[df["decision"] == "REVIEW"])
        n_approve = len(df[df["decision"] == "APPROVE"])

        # If is_fraud column exists, compute quality metrics
        stats = {
            "total_transactions": total,
            "blocked": n_block,
            "reviewed": n_review,
            "approved": n_approve,
            "block_rate": round(n_block / total, 4),
            "review_rate": round(n_review / total, 4),
            "approve_rate": round(n_approve / total, 4),
        }

        if "is_fraud" in df.columns:
            flagged = df[df["decision"].isin(["BLOCK", "REVIEW"])]
            actual_fraud = df[df["is_fraud"] == 1]
            caught = flagged[flagged["is_fraud"] == 1]

            stats["total_fraud"] = len(actual_fraud)
            stats["fraud_caught"] = len(caught)
            stats["fraud_capture_rate"] = round(
                len(caught) / len(actual_fraud), 4
            ) if len(actual_fraud) > 0 else 0

            false_positives = flagged[flagged["is_fraud"] == 0]
            stats["false_positives"] = len(false_positives)
            stats["false_positive_rate"] = round(
                len(false_positives) / len(df[df["is_fraud"] == 0]), 4
            ) if len(df[df["is_fraud"] == 0]) > 0 else 0

            # Precision among flagged
            stats["alert_precision"] = round(
                len(caught) / len(flagged), 4
            ) if len(flagged) > 0 else 0

        return stats
