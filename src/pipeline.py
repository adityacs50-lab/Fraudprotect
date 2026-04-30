"""
Pipeline Orchestrator — ties together all layers:
1. Generate/load transactions
2. Engineer features
3. Train models
4. Apply rules
5. Score with ML + anomaly
6. Combine decisions
7. Generate explanations
8. Persist to database
"""

import os
import sys
import json
import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.simulator.transaction_generator import TransactionSimulator
from src.features.feature_engineering import FeatureEngineer
from src.rules.rules_engine import RulesEngine
from src.models.model_trainer import ModelTrainer
from src.decisioning.decision_combiner import DecisionCombiner
from src.explainability.shap_explainer import SHAPExplainer
from src import database as db


class FraudPipeline:
    """End-to-end fraud detection pipeline."""

    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = os.path.join(PROJECT_ROOT, "models")
        self.model_dir = model_dir
        self.simulator = TransactionSimulator(n_users=500, fraud_rate=0.035, seed=42)
        self.feature_eng = FeatureEngineer()
        self.rules_engine = RulesEngine()
        self.model_trainer = ModelTrainer(model_dir=model_dir)
        self.decision_combiner = DecisionCombiner()
        self.explainer = None
        self.is_trained = False
        self._global_importance = None
        self._model_metrics = None

    def initialize(self, n_transactions: int = 15000, force_retrain: bool = False):
        """Full initialization: generate data, train models, score, persist."""
        print("[1/7] Generating synthetic transactions...")
        raw_df = self.simulator.generate_batch(n_transactions=n_transactions, days=30)

        print("[2/7] Engineering features...")
        featured_df = self.feature_eng.compute_features(raw_df)

        feature_cols = self.feature_eng.feature_columns

        model_path = os.path.join(self.model_dir, "classifier.joblib")
        if os.path.exists(model_path) and not force_retrain:
            print("[3/7] Loading existing models...")
            self.model_trainer.load()
            self._model_metrics = self.model_trainer.metrics
        else:
            print("[3/7] Training models...")
            self._model_metrics = self.model_trainer.train(featured_df, feature_cols)
            print(f"      Metrics: {json.dumps(self._model_metrics, indent=2)}")

        print("[4/7] Scoring transactions...")
        scored_df = self.model_trainer.score_batch(featured_df)

        print("[5/7] Applying fraud rules...")
        scored_df = self.rules_engine.evaluate_batch(scored_df)

        print("[6/7] Running decision engine...")
        scored_df = self.decision_combiner.decide_batch(scored_df)

        # Initialize SHAP explainer
        self.explainer = SHAPExplainer(
            self.model_trainer.classifier,
            self.model_trainer.feature_columns
        )

        print("[7/7] Generating explanations for flagged transactions...")
        flagged_mask = scored_df["decision"].isin(["REVIEW", "BLOCK"])
        flagged_df = scored_df[flagged_mask]

        if len(flagged_df) > 0:
            explanations = self.explainer.explain_batch(flagged_df, top_k=5)
            reason_codes_list = [e["reason_codes"] for e in explanations]
            shap_details_list = [e["shap_details"] for e in explanations]

            scored_df.loc[flagged_mask, "reason_codes"] = [json.dumps(r) for r in reason_codes_list]
            scored_df.loc[flagged_mask, "shap_details"] = [json.dumps(s) for s in shap_details_list]
        
        scored_df["reason_codes"] = scored_df["reason_codes"].fillna("[]")
        scored_df["shap_details"] = scored_df["shap_details"].fillna("[]")

        # Compute global importance
        self._global_importance = self.explainer.compute_global_importance(featured_df)

        # Persist to database
        print("      Persisting to database...")
        db.init_db()
        db.insert_transactions(scored_df)
        db.insert_scored_transactions(scored_df)
        n_alerts = db.create_alerts(scored_df)

        # Save model metrics
        conn = db.get_connection()
        conn.execute(
            "INSERT INTO model_metrics (metrics_json, model_type) VALUES (?, ?)",
            (json.dumps(self._model_metrics), "hybrid")
        )
        conn.commit()
        conn.close()

        self.is_trained = True
        stats = self.decision_combiner.get_decision_stats(scored_df)

        print(f"\n{'='*60}")
        print(f"Pipeline initialized successfully!")
        print(f"  Transactions: {len(scored_df)}")
        print(f"  Alerts created: {n_alerts}")
        print(f"  Decisions: APPROVE={stats.get('approved',0)} | REVIEW={stats.get('reviewed',0)} | BLOCK={stats.get('blocked',0)}")
        if 'fraud_capture_rate' in stats:
            print(f"  Fraud capture rate: {stats['fraud_capture_rate']*100:.1f}%")
            print(f"  False positive rate: {stats['false_positive_rate']*100:.2f}%")
            print(f"  Alert precision: {stats['alert_precision']*100:.1f}%")
        print(f"{'='*60}\n")

        return stats

    def score_new_transactions(self, n: int = 50) -> pd.DataFrame:
        """Score a new batch of transactions (for streaming demo)."""
        if not self.is_trained:
            self.model_trainer.load()
            self.explainer = SHAPExplainer(
                self.model_trainer.classifier,
                self.model_trainer.feature_columns
            )
            self.is_trained = True

        raw = self.simulator.generate_stream(batch_size=n)
        featured = self.feature_eng.compute_features(raw)
        scored = self.model_trainer.score_batch(featured)
        scored = self.rules_engine.evaluate_batch(scored)
        scored = self.decision_combiner.decide_batch(scored)

        flagged_mask = scored["decision"].isin(["REVIEW", "BLOCK"])
        flagged = scored[flagged_mask]

        if len(flagged) > 0:
            explanations = self.explainer.explain_batch(flagged, top_k=5)
            scored.loc[flagged_mask, "reason_codes"] = [json.dumps(e["reason_codes"]) for e in explanations]
            scored.loc[flagged_mask, "shap_details"] = [json.dumps(e["shap_details"]) for e in explanations]

        scored["reason_codes"] = scored["reason_codes"].fillna("[]")
        scored["shap_details"] = scored["shap_details"].fillna("[]")

        # Persist
        db.insert_transactions(scored)
        db.insert_scored_transactions(scored)
        db.create_alerts(scored)

        return scored

    def explain_transaction(self, tx_id: str) -> dict:
        """Get full explanation for a specific transaction."""
        detail = db.get_transaction_detail(tx_id)
        if not detail:
            return {"error": "Transaction not found"}

        result = {
            "transaction": detail,
            "reason_codes": json.loads(detail.get("reason_codes", "[]") or "[]"),
            "shap_details": json.loads(detail.get("shap_details", "[]") or "[]"),
        }
        return result

    def get_global_importance(self) -> dict:
        """Return global feature importance."""
        if self._global_importance:
            return self._global_importance
        return {}

    def get_model_metrics(self) -> dict:
        """Return model evaluation metrics."""
        if self._model_metrics:
            return self._model_metrics
        return self.model_trainer.metrics


if __name__ == "__main__":
    pipeline = FraudPipeline()
    pipeline.initialize(n_transactions=15000, force_retrain=True)
