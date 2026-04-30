import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.features.feature_engineering import FeatureEngineer, _haversine_km
from src.rules.rules_engine import RulesEngine
from src.decisioning.decision_combiner import DecisionCombiner, DecisionThresholds

# --- Feature Engineering Tests ---

def test_haversine_distance():
    # New York to LA
    lat1, lon1 = 40.7128, -74.0060
    lat2, lon2 = 34.0522, -118.2437
    dist = _haversine_km(lat1, lon1, lat2, lon2)
    assert 3900 < dist < 4000  # ~3940 km

def test_time_features():
    fe = FeatureEngineer()
    df = pd.DataFrame([
        {"timestamp": "2023-10-01 02:30:00", "user_id": "u1", "amount": 100, "merchant_category": "retail", "payment_method": "credit_card", "device_id": "d1", "latitude": 0, "longitude": 0},
        {"timestamp": "2023-10-02 14:00:00", "user_id": "u1", "amount": 100, "merchant_category": "retail", "payment_method": "credit_card", "device_id": "d1", "latitude": 0, "longitude": 0}
    ])
    res = fe.compute_features(df)
    assert res.iloc[0]["hour"] == 2
    assert res.iloc[0]["is_night"] == 1
    assert res.iloc[0]["is_weekend"] == 1  # Oct 1, 2023 was Sunday
    assert res.iloc[1]["hour"] == 14
    assert res.iloc[1]["is_night"] == 0
    assert res.iloc[1]["is_weekend"] == 0  # Oct 2, 2023 was Monday

def test_rolling_features():
    fe = FeatureEngineer()
    df = pd.DataFrame([
        {"timestamp": "2023-10-01 10:00:00", "user_id": "u1", "amount": 100, "merchant_category": "A", "payment_method": "upi", "device_id": "d1", "latitude": 0, "longitude": 0},
        {"timestamp": "2023-10-01 10:30:00", "user_id": "u1", "amount": 200, "merchant_category": "A", "payment_method": "upi", "device_id": "d1", "latitude": 0, "longitude": 0},
        {"timestamp": "2023-10-02 10:00:00", "user_id": "u1", "amount": 300, "merchant_category": "B", "payment_method": "upi", "device_id": "d1", "latitude": 0, "longitude": 0}
    ])
    res = fe.compute_features(df)
    assert res.iloc[0]["tx_count_1h"] == 0
    assert res.iloc[1]["tx_count_1h"] == 1
    assert res.iloc[2]["tx_count_1h"] == 0  # Oct 2 is more than 1h after Oct 1
    assert res.iloc[2]["tx_count_24h"] == 2 # The two txs from Oct 1
    assert res.iloc[2]["avg_amount_user"] == 150.0  # avg of 100, 200 (previous)

# --- Rules Engine Tests ---

def test_rule_high_amount_new_device():
    re = RulesEngine()
    # Should trigger
    row1 = pd.Series({"is_new_device": 1, "amount_ratio_to_baseline": 4.0})
    res1 = re._rule_high_amount_new_device(row1)
    assert res1.severity == "critical"
    
    # Shouldn't trigger (not new device)
    row2 = pd.Series({"is_new_device": 0, "amount_ratio_to_baseline": 4.0})
    res2 = re._rule_high_amount_new_device(row2)
    assert res2.severity == "none"

def test_rule_impossible_travel():
    re = RulesEngine()
    row = pd.Series({"speed_kmh": 900, "distance_from_prev_km": 400})
    res = re._rule_impossible_travel(row)
    assert res.severity == "critical"

def test_rule_velocity_spike():
    re = RulesEngine()
    row_crit = pd.Series({"tx_count_1h": 10})
    res_crit = re._rule_velocity_spike(row_crit)
    assert res_crit.severity == "critical"
    
    row_med = pd.Series({"tx_count_1h": 4})
    res_med = re._rule_velocity_spike(row_med)
    assert res_med.severity == "medium"

def test_evaluate_batch_max_severity():
    re = RulesEngine()
    df = pd.DataFrame([
        {"is_new_device": 1, "amount_ratio_to_baseline": 4.0, "tx_count_1h": 4, "merchant_risk_score": 0.1}
    ])
    res = re.evaluate_batch(df)
    assert res.iloc[0]["rule_severity"] == "critical"  # overrides medium from velocity
    assert "New device with amount" in res.iloc[0]["rule_reasons"]
    assert "transactions in last hour" in res.iloc[0]["rule_reasons"]

# --- Decision Combiner Tests ---

def test_decision_block_critical_rule():
    dc = DecisionCombiner()
    res = dc.decide_single(fraud_prob=0.6, anomaly_score=0.1, rule_score=1.0, rule_severity="critical")
    assert res["action"] == "BLOCK"
    assert res["risk_level"] == "critical"

def test_decision_review_threshold():
    dc = DecisionCombiner()
    # fraud prob is 0.45 (>= review_fraud_prob of 0.40 but < block of 0.85)
    res = dc.decide_single(fraud_prob=0.45, anomaly_score=0.1, rule_score=0.0, rule_severity="none")
    assert res["action"] == "REVIEW"

def test_decision_approve_low_scores():
    dc = DecisionCombiner()
    res = dc.decide_single(fraud_prob=0.1, anomaly_score=0.1, rule_score=0.0, rule_severity="none")
    assert res["action"] == "APPROVE"
    assert res["risk_level"] == "low"
