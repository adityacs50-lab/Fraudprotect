import unittest
import pandas as pd
from src.rules.rules_engine import RulesEngine
from src.decisioning.decision_combiner import DecisionCombiner

class TestFraudLogic(unittest.TestCase):
    def setUp(self):
        self.rules_engine = RulesEngine()
        self.decision_combiner = DecisionCombiner()

    def test_impossible_travel_rule(self):
        # Create a mock transaction with high speed
        tx = pd.Series({
            "speed_kmh": 1200,
            "distance_from_prev_km": 500
        })
        results = self.rules_engine.evaluate(tx)
        rule_names = [r.rule_name for r in results]
        self.assertIn("impossible_travel", rule_names)
        
        # Check critical severity
        critical_rules = [r for r in results if r.severity == "critical"]
        self.assertTrue(len(critical_rules) > 0)

    def test_decision_logic_block(self):
        # Fraud prob 0.9 should result in BLOCK
        decision = self.decision_combiner.decide_single(
            fraud_prob=0.95,
            anomaly_score=0.5,
            rule_score=0.2,
            rule_severity="none"
        )
        self.assertEqual(decision["action"], "BLOCK")

    def test_decision_logic_review(self):
        # Mixed signals should result in REVIEW
        decision = self.decision_combiner.decide_single(
            fraud_prob=0.45,
            anomaly_score=0.2,
            rule_score=0.3,
            rule_severity="medium"
        )
        self.assertEqual(decision["action"], "REVIEW")

if __name__ == "__main__":
    unittest.main()
