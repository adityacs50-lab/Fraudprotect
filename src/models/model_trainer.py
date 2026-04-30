"""
Model Trainer — trains Isolation Forest (anomaly) + LightGBM (supervised)
and provides scoring functions for the hybrid decision engine.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, precision_recall_fscore_support,
    confusion_matrix, roc_auc_score,
)

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    from sklearn.ensemble import GradientBoostingClassifier
    HAS_LGB = False


class ModelTrainer:
    """Train and score with anomaly detector + supervised classifier."""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.iso_forest = None
        self.classifier = None
        self.feature_columns = []
        self.metrics = {}

    def train(self, df: pd.DataFrame, feature_columns: list, target_col: str = "is_fraud"):
        """Train both models on the provided DataFrame."""
        self.feature_columns = feature_columns
        X = df[feature_columns].fillna(0).values
        y = df[target_col].values

        # ---- Isolation Forest (unsupervised anomaly detection) ----
        self.iso_forest = IsolationForest(
            n_estimators=200,
            contamination=0.05,
            max_samples=0.8,
            random_state=42,
            n_jobs=-1,
        )
        self.iso_forest.fit(X)

        # ---- Supervised classifier ----
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        if HAS_LGB:
            # Compute scale_pos_weight for class imbalance
            n_neg = np.sum(y_train == 0)
            n_pos = max(np.sum(y_train == 1), 1)
            scale_pos = n_neg / n_pos

            self.classifier = lgb.LGBMClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                scale_pos_weight=scale_pos,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                verbose=-1,
                n_jobs=-1,
            )
        else:
            self.classifier = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                random_state=42,
            )

        self.classifier.fit(X_train, y_train)

        # ---- Evaluate ----
        y_pred = self.classifier.predict(X_test)
        y_proba = self.classifier.predict_proba(X_test)[:, 1]

        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average="binary", zero_division=0
        )
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

        try:
            auc = roc_auc_score(y_test, y_proba)
        except ValueError:
            auc = 0.0

        self.metrics = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "auc_roc": round(auc, 4),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn),
            "test_size": len(y_test),
            "fraud_rate_train": round(np.mean(y_train), 4),
            "fraud_rate_test": round(np.mean(y_test), 4),
        }

        # Save models
        joblib.dump(self.iso_forest, os.path.join(self.model_dir, "isolation_forest.joblib"))
        joblib.dump(self.classifier, os.path.join(self.model_dir, "classifier.joblib"))
        joblib.dump(self.feature_columns, os.path.join(self.model_dir, "feature_columns.joblib"))

        return self.metrics

    def load(self):
        """Load saved models."""
        self.iso_forest = joblib.load(os.path.join(self.model_dir, "isolation_forest.joblib"))
        self.classifier = joblib.load(os.path.join(self.model_dir, "classifier.joblib"))
        self.feature_columns = joblib.load(os.path.join(self.model_dir, "feature_columns.joblib"))

    def score_anomaly(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores (higher = more anomalous, 0-1 normalized)."""
        raw = self.iso_forest.decision_function(X)
        # Invert and normalize: decision_function returns negative for anomalies
        normalized = 1 - (raw - raw.min()) / (raw.max() - raw.min() + 1e-8)
        return normalized

    def score_fraud_probability(self, X: np.ndarray) -> np.ndarray:
        """Return fraud probability from supervised model."""
        return self.classifier.predict_proba(X)[:, 1]

    def score_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score a batch DataFrame. Returns df with anomaly_score and fraud_probability."""
        df = df.copy()
        X = df[self.feature_columns].fillna(0).values
        df["anomaly_score"] = self.score_anomaly(X)
        df["fraud_probability"] = self.score_fraud_probability(X)
        return df
