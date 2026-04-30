"""
Database Layer — SQLite persistence for transactions, alerts, and analyst actions.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "fraud_platform.db")


def get_connection(db_path: str = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str = None):
    """Create all tables."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            merchant_category TEXT,
            city TEXT,
            latitude REAL,
            longitude REAL,
            device_id TEXT,
            payment_method TEXT,
            timestamp TEXT NOT NULL,
            is_fraud INTEGER DEFAULT 0,
            fraud_type TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scored_transactions (
            transaction_id TEXT PRIMARY KEY,
            fraud_probability REAL,
            anomaly_score REAL,
            rule_score REAL,
            rule_severity TEXT,
            rule_reasons TEXT,
            combined_score REAL,
            decision TEXT,
            risk_level TEXT,
            reason_codes TEXT,
            shap_details TEXT,
            scored_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            risk_level TEXT,
            combined_score REAL,
            reason_codes TEXT,
            analyst_action TEXT,
            analyst_notes TEXT,
            analyst_id TEXT,
            resolved_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        );

        CREATE TABLE IF NOT EXISTS model_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metrics_json TEXT NOT NULL,
            model_type TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_alerts_decision ON alerts(decision);
        CREATE INDEX IF NOT EXISTS idx_alerts_action ON alerts(analyst_action);
        CREATE INDEX IF NOT EXISTS idx_scored_decision ON scored_transactions(decision);
    """)

    conn.commit()
    conn.close()


def insert_transactions(df: pd.DataFrame, db_path: str = None):
    """Insert raw transactions into the database."""
    conn = get_connection(db_path)
    cols = ["transaction_id", "user_id", "amount", "merchant_category", "city",
            "latitude", "longitude", "device_id", "payment_method", "timestamp",
            "is_fraud", "fraud_type"]
    sub = df[[c for c in cols if c in df.columns]].copy()
    sub["timestamp"] = sub["timestamp"].astype(str)
    sub.to_sql("transactions", conn, if_exists="append", index=False)
    conn.close()


def insert_scored_transactions(df: pd.DataFrame, db_path: str = None):
    """Insert scoring results."""
    conn = get_connection(db_path)
    records = []
    for _, row in df.iterrows():
        records.append({
            "transaction_id": row["transaction_id"],
            "fraud_probability": row.get("fraud_probability", 0),
            "anomaly_score": row.get("anomaly_score", 0),
            "rule_score": row.get("rule_score", 0),
            "rule_severity": row.get("rule_severity", "none"),
            "rule_reasons": row.get("rule_reasons", ""),
            "combined_score": row.get("combined_score", 0),
            "decision": row.get("decision", "APPROVE"),
            "risk_level": row.get("risk_level", "low"),
            "reason_codes": json.dumps(row.get("reason_codes", [])) if isinstance(row.get("reason_codes"), list) else row.get("reason_codes", "[]"),
            "shap_details": json.dumps(row.get("shap_details", [])) if isinstance(row.get("shap_details"), list) else row.get("shap_details", "[]"),
        })
    pd.DataFrame(records).to_sql("scored_transactions", conn, if_exists="append", index=False)
    conn.close()


def create_alerts(df: pd.DataFrame, db_path: str = None):
    """Create alerts for REVIEW and BLOCK decisions."""
    conn = get_connection(db_path)
    flagged = df[df["decision"].isin(["REVIEW", "BLOCK"])]
    records = []
    for _, row in flagged.iterrows():
        records.append({
            "transaction_id": row["transaction_id"],
            "user_id": row["user_id"],
            "decision": row["decision"],
            "risk_level": row.get("risk_level", "medium"),
            "combined_score": row.get("combined_score", 0),
            "reason_codes": json.dumps(row.get("reason_codes", [])) if isinstance(row.get("reason_codes"), list) else row.get("reason_codes", "[]"),
        })
    if records:
        pd.DataFrame(records).to_sql("alerts", conn, if_exists="append", index=False)
    conn.close()
    return len(records)


def get_alerts(status: str = None, limit: int = 100, offset: int = 0, db_path: str = None) -> List[Dict]:
    """Fetch alerts with optional filtering."""
    conn = get_connection(db_path)
    query = """
        SELECT a.*, t.amount, t.merchant_category, t.city, t.device_id,
               t.payment_method, t.timestamp as tx_timestamp,
               s.fraud_probability, s.anomaly_score, s.rule_reasons, s.shap_details
        FROM alerts a
        JOIN transactions t ON a.transaction_id = t.transaction_id
        LEFT JOIN scored_transactions s ON a.transaction_id = s.transaction_id
    """
    params = []
    if status == "pending":
        query += " WHERE a.analyst_action IS NULL"
    elif status == "resolved":
        query += " WHERE a.analyst_action IS NOT NULL"

    query += " ORDER BY a.combined_score DESC, a.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transaction_detail(tx_id: str, db_path: str = None) -> Optional[Dict]:
    """Get full transaction detail with scoring and alert info."""
    conn = get_connection(db_path)
    row = conn.execute("""
        SELECT t.*, s.fraud_probability, s.anomaly_score, s.rule_score,
               s.rule_severity, s.rule_reasons, s.combined_score, s.decision,
               s.risk_level, s.reason_codes, s.shap_details,
               a.alert_id, a.analyst_action, a.analyst_notes, a.resolved_at
        FROM transactions t
        LEFT JOIN scored_transactions s ON t.transaction_id = s.transaction_id
        LEFT JOIN alerts a ON t.transaction_id = a.transaction_id
        WHERE t.transaction_id = ?
    """, (tx_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_alert_action(alert_id: int, action: str, notes: str = "",
                        analyst_id: str = "analyst-1", db_path: str = None):
    """Record analyst action on an alert."""
    conn = get_connection(db_path)
    conn.execute("""
        UPDATE alerts SET analyst_action = ?, analyst_notes = ?,
               analyst_id = ?, resolved_at = ?
        WHERE alert_id = ?
    """, (action, notes, analyst_id, datetime.now().isoformat(), alert_id))
    conn.commit()
    conn.close()


def get_dashboard_metrics(db_path: str = None) -> Dict:
    """Compute operational dashboard metrics."""
    conn = get_connection(db_path)

    total_tx = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    total_alerts = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM alerts WHERE analyst_action IS NULL").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM alerts WHERE analyst_action IS NOT NULL").fetchone()[0]

    # Decision distribution
    decisions = conn.execute(
        "SELECT decision, COUNT(*) as cnt FROM scored_transactions GROUP BY decision"
    ).fetchall()
    decision_dist = {r["decision"]: r["cnt"] for r in decisions}

    # Analyst action distribution
    actions = conn.execute(
        "SELECT analyst_action, COUNT(*) as cnt FROM alerts WHERE analyst_action IS NOT NULL GROUP BY analyst_action"
    ).fetchall()
    action_dist = {r["analyst_action"]: r["cnt"] for r in actions}

    # Fraud detection rate
    total_fraud = conn.execute("SELECT COUNT(*) FROM transactions WHERE is_fraud = 1").fetchone()[0]
    caught = conn.execute("""
        SELECT COUNT(*) FROM scored_transactions s
        JOIN transactions t ON s.transaction_id = t.transaction_id
        WHERE t.is_fraud = 1 AND s.decision IN ('BLOCK', 'REVIEW')
    """).fetchone()[0]

    # False positive count
    false_positives = conn.execute("""
        SELECT COUNT(*) FROM scored_transactions s
        JOIN transactions t ON s.transaction_id = t.transaction_id
        WHERE t.is_fraud = 0 AND s.decision IN ('BLOCK', 'REVIEW')
    """).fetchone()[0]

    legit_total = conn.execute("SELECT COUNT(*) FROM transactions WHERE is_fraud = 0").fetchone()[0]

    # Top alert reasons
    reasons_raw = conn.execute(
        "SELECT reason_codes FROM alerts ORDER BY created_at DESC LIMIT 500"
    ).fetchall()
    reason_counts = {}
    for r in reasons_raw:
        try:
            codes = json.loads(r["reason_codes"]) if r["reason_codes"] else []
            for code in codes:
                reason_counts[code] = reason_counts.get(code, 0) + 1
        except (json.JSONDecodeError, TypeError):
            pass
    top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    conn.close()

    return {
        "total_transactions": total_tx,
        "total_alerts": total_alerts,
        "pending_alerts": pending,
        "resolved_alerts": resolved,
        "decision_distribution": decision_dist,
        "analyst_actions": action_dist,
        "total_fraud": total_fraud,
        "fraud_caught": caught,
        "fraud_capture_rate": round(caught / total_fraud, 4) if total_fraud > 0 else 0,
        "false_positives": false_positives,
        "false_positive_rate": round(false_positives / legit_total, 4) if legit_total > 0 else 0,
        "alert_precision": round(caught / (caught + false_positives), 4) if (caught + false_positives) > 0 else 0,
        "top_alert_reasons": [{"reason": r, "count": c} for r, c in top_reasons],
    }


def get_recent_transactions(limit: int = 50, db_path: str = None) -> List[Dict]:
    """Get most recent transactions with scores."""
    conn = get_connection(db_path)
    rows = conn.execute("""
        SELECT t.*, s.fraud_probability, s.anomaly_score, s.combined_score,
               s.decision, s.risk_level, s.rule_reasons
        FROM transactions t
        LEFT JOIN scored_transactions s ON t.transaction_id = s.transaction_id
        ORDER BY t.timestamp DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
