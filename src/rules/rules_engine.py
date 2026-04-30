"""
Rules Engine — deterministic fraud rules with severity levels.
Each rule returns a severity (none, low, medium, high, critical) and a reason code.
"""

from dataclasses import dataclass
from typing import List, Tuple
import pandas as pd


@dataclass
class RuleResult:
    rule_name: str
    severity: str  # none, low, medium, high, critical
    reason: str
    score: float  # 0.0 - 1.0


SEVERITY_SCORES = {
    "none": 0.0,
    "low": 0.2,
    "medium": 0.4,
    "high": 0.7,
    "critical": 1.0,
}


class RulesEngine:
    """Evaluate a transaction against deterministic fraud rules."""

    def evaluate(self, row: pd.Series) -> List[RuleResult]:
        """Run all rules on a single transaction row. Returns list of triggered rules."""
        results = []
        for rule_fn in [
            self._rule_high_amount_new_device,
            self._rule_impossible_travel,
            self._rule_velocity_spike,
            self._rule_night_high_risk_merchant,
            self._rule_amount_spike,
            self._rule_new_device_high_risk,
            self._rule_multiple_devices,
            self._rule_high_merchant_risk,
        ]:
            result = rule_fn(row)
            if result.severity != "none":
                results.append(result)
        return results

    def evaluate_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Evaluate rules for entire DataFrame. Adds rule columns."""
        rule_severities = []
        rule_reasons_list = []
        rule_scores = []
        rule_counts = []

        for _, row in df.iterrows():
            results = self.evaluate(row)
            if results:
                max_result = max(results, key=lambda r: SEVERITY_SCORES[r.severity])
                rule_severities.append(max_result.severity)
                rule_reasons_list.append(" | ".join(r.reason for r in results))
                rule_scores.append(max(SEVERITY_SCORES[r.severity] for r in results))
                rule_counts.append(len(results))
            else:
                rule_severities.append("none")
                rule_reasons_list.append("")
                rule_scores.append(0.0)
                rule_counts.append(0)

        df = df.copy()
        df["rule_severity"] = rule_severities
        df["rule_reasons"] = rule_reasons_list
        df["rule_score"] = rule_scores
        df["rule_count"] = rule_counts
        return df

    # ---- Individual Rules ----

    def _rule_high_amount_new_device(self, row) -> RuleResult:
        if row.get("is_new_device", 0) == 1 and row.get("amount_ratio_to_baseline", 1) > 3:
            return RuleResult("high_amount_new_device", "critical",
                              f"New device with amount {row.get('amount_ratio_to_baseline', 0):.1f}x baseline", 1.0)
        return RuleResult("high_amount_new_device", "none", "", 0.0)

    def _rule_impossible_travel(self, row) -> RuleResult:
        speed = row.get("speed_kmh", 0)
        dist = row.get("distance_from_prev_km", 0)
        if speed > 800 and dist > 300:
            return RuleResult("impossible_travel", "critical",
                              f"Location changed {dist:.0f}km at {speed:.0f}km/h — impossible travel", 1.0)
        if speed > 500 and dist > 200:
            return RuleResult("impossible_travel", "high",
                              f"Suspicious travel: {dist:.0f}km at {speed:.0f}km/h", 0.7)
        return RuleResult("impossible_travel", "none", "", 0.0)

    def _rule_velocity_spike(self, row) -> RuleResult:
        count_1h = row.get("tx_count_1h", 0)
        if count_1h >= 8:
            return RuleResult("velocity_spike", "critical",
                              f"{count_1h} transactions in last hour — velocity abuse", 1.0)
        if count_1h >= 5:
            return RuleResult("velocity_spike", "high",
                              f"{count_1h} transactions in last hour", 0.7)
        if count_1h >= 3:
            return RuleResult("velocity_spike", "medium",
                              f"{count_1h} transactions in last hour", 0.4)
        return RuleResult("velocity_spike", "none", "", 0.0)

    def _rule_night_high_risk_merchant(self, row) -> RuleResult:
        if row.get("is_night", 0) == 1 and row.get("merchant_risk_score", 0) >= 0.35:
            return RuleResult("night_high_risk", "high",
                              f"Night-time transaction at high-risk merchant ({row.get('merchant_category', 'unknown')})", 0.7)
        return RuleResult("night_high_risk", "none", "", 0.0)

    def _rule_amount_spike(self, row) -> RuleResult:
        zscore = row.get("amount_zscore", 0)
        ratio = row.get("amount_ratio_to_baseline", 1)
        if zscore > 4 and ratio > 5:
            return RuleResult("amount_spike", "critical",
                              f"Amount {ratio:.1f}x user baseline (z={zscore:.1f})", 1.0)
        if zscore > 3 and ratio > 3:
            return RuleResult("amount_spike", "high",
                              f"Amount {ratio:.1f}x user baseline (z={zscore:.1f})", 0.7)
        if zscore > 2:
            return RuleResult("amount_spike", "medium",
                              f"Amount {ratio:.1f}x user baseline", 0.4)
        return RuleResult("amount_spike", "none", "", 0.0)

    def _rule_new_device_high_risk(self, row) -> RuleResult:
        if row.get("is_new_device", 0) == 1 and row.get("merchant_risk_score", 0) >= 0.3:
            return RuleResult("new_device_high_risk", "high",
                              f"New device at high-risk merchant ({row.get('merchant_category', 'unknown')})", 0.7)
        return RuleResult("new_device_high_risk", "none", "", 0.0)

    def _rule_multiple_devices(self, row) -> RuleResult:
        if row.get("device_count_user", 1) > 4:
            return RuleResult("multiple_devices", "medium",
                              f"User has {row.get('device_count_user', 0)} devices", 0.4)
        return RuleResult("multiple_devices", "none", "", 0.0)

    def _rule_high_merchant_risk(self, row) -> RuleResult:
        if row.get("merchant_risk_score", 0) >= 0.4 and row.get("amount", 0) > 5000:
            return RuleResult("high_merchant_risk", "medium",
                              f"High-risk merchant ({row.get('merchant_category', '')}) with large amount", 0.4)
        return RuleResult("high_merchant_risk", "none", "", 0.0)
