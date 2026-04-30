"""
FastAPI Backend — REST API for the Fraud Decisioning Platform.

Endpoints:
  GET  /api/health              — health check
  POST /api/initialize          — run full pipeline
  GET  /api/transactions        — recent transactions
  GET  /api/transactions/{id}   — transaction detail + explanation
  GET  /api/alerts              — alert queue
  POST /api/alerts/{id}/action  — analyst action on alert
  GET  /api/metrics             — dashboard metrics
  GET  /api/metrics/model       — model evaluation metrics
  GET  /api/metrics/importance  — global feature importance
  POST /api/stream              — generate new transaction batch
"""

import os
import sys
import json
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import FraudPipeline
from src import database as db

app = FastAPI(
    title="Fraud Decisioning Platform",
    description="Hybrid fraud detection with rules, anomaly detection, ML, and SHAP explainability",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
pipeline = FraudPipeline()


class ActionRequest(BaseModel):
    action: str  # approve, escalate, confirm_fraud
    notes: str = ""
    analyst_id: str = "analyst-1"


class InitRequest(BaseModel):
    n_transactions: int = 15000
    force_retrain: bool = False


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    db.init_db()
    # Check if models exist
    model_path = os.path.join(PROJECT_ROOT, "models", "classifier.joblib")
    if os.path.exists(model_path):
        try:
            pipeline.model_trainer.load()
            pipeline.explainer = None  # Will be created on demand
            pipeline.is_trained = True
            print("Models loaded from disk.")
        except Exception as e:
            print(f"Could not load models: {e}")


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "models_loaded": pipeline.is_trained,
        "version": "1.0.0",
    }


@app.post("/api/initialize")
async def initialize(req: InitRequest):
    """Run full pipeline: generate data, train, score, persist."""
    try:
        stats = pipeline.initialize(
            n_transactions=req.n_transactions,
            force_retrain=req.force_retrain,
        )
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions")
async def get_transactions(limit: int = Query(50, le=500)):
    """Get recent transactions with scores."""
    try:
        rows = db.get_recent_transactions(limit=limit)
        return {"transactions": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/{tx_id}")
async def get_transaction(tx_id: str):
    """Get full transaction detail with explanation."""
    detail = db.get_transaction_detail(tx_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Parse JSON fields
    try:
        detail["reason_codes"] = json.loads(detail.get("reason_codes", "[]") or "[]")
    except (json.JSONDecodeError, TypeError):
        detail["reason_codes"] = []
    try:
        detail["shap_details"] = json.loads(detail.get("shap_details", "[]") or "[]")
    except (json.JSONDecodeError, TypeError):
        detail["shap_details"] = []

    return detail


@app.get("/api/alerts")
async def get_alerts(
    status: Optional[str] = Query(None, regex="^(pending|resolved)$"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
):
    """Get alert queue with optional filtering."""
    try:
        alerts = db.get_alerts(status=status, limit=limit, offset=offset)
        # Parse JSON fields
        for alert in alerts:
            try:
                alert["reason_codes"] = json.loads(alert.get("reason_codes", "[]") or "[]")
            except (json.JSONDecodeError, TypeError):
                alert["reason_codes"] = []
            try:
                alert["shap_details"] = json.loads(alert.get("shap_details", "[]") or "[]")
            except (json.JSONDecodeError, TypeError):
                alert["shap_details"] = []
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/{alert_id}/action")
async def alert_action(alert_id: int, req: ActionRequest):
    """Record analyst action on an alert."""
    valid_actions = {"approve", "escalate", "confirm_fraud"}
    if req.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

    try:
        db.update_alert_action(
            alert_id=alert_id,
            action=req.action,
            notes=req.notes,
            analyst_id=req.analyst_id,
        )
        return {"status": "success", "alert_id": alert_id, "action": req.action}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
async def get_metrics():
    """Get operational dashboard metrics."""
    try:
        metrics = db.get_dashboard_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/model")
async def get_model_metrics():
    """Get model evaluation metrics."""
    metrics = pipeline.get_model_metrics()
    if not metrics:
        raise HTTPException(status_code=404, detail="No model metrics available. Run /api/initialize first.")
    return metrics


@app.get("/api/metrics/importance")
async def get_feature_importance():
    """Get global feature importance."""
    importance = pipeline.get_global_importance()
    if not importance:
        raise HTTPException(status_code=404, detail="No importance data. Run /api/initialize first.")
    return {"feature_importance": importance}


@app.post("/api/stream")
async def stream_transactions(n: int = Query(50, le=200)):
    """Generate and score new transactions (near-real-time simulation)."""
    if not pipeline.is_trained:
        raise HTTPException(status_code=400, detail="Pipeline not initialized. Run /api/initialize first.")
    try:
        scored_df = pipeline.score_new_transactions(n=n)
        flagged = scored_df[scored_df["decision"].isin(["REVIEW", "BLOCK"])]
        return {
            "status": "success",
            "total": len(scored_df),
            "flagged": len(flagged),
            "decisions": scored_df["decision"].value_counts().to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}")
async def get_user_profile(user_id: str):
    """Get user behavioral profile."""
    profile = pipeline.simulator.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile
