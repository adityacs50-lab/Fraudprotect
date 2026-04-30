"use client";
import { AlertTriangle, Shield, Clock, CheckCircle, ChevronRight } from "lucide-react";

interface Alert {
  alert_id: number;
  transaction_id: string;
  user_id: string;
  decision: string;
  risk_level: string;
  combined_score: number;
  reason_codes: string[];
  analyst_action: string | null;
  amount?: number;
  merchant_category?: string;
  city?: string;
  fraud_probability?: number;
  tx_timestamp?: string;
}

interface Props {
  alerts: Alert[];
  onAction: (alertId: number, action: string) => void;
  onSelect: (txId: string) => void;
}

export function AlertQueue({ alerts, onAction, onSelect }: Props) {
  const pending = alerts.filter((a) => !a.analyst_action);
  const resolved = alerts.filter((a) => a.analyst_action);

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-4 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <div className="flex items-center gap-2">
          <AlertTriangle size={16} style={{ color: "var(--accent-amber)" }} />
          <h3 className="text-sm font-semibold">Alert Queue</h3>
        </div>
        <div className="flex gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>{pending.length} pending</span>
          <span>·</span>
          <span>{resolved.length} resolved</span>
        </div>
      </div>
      <div style={{ maxHeight: "600px", overflowY: "auto" }}>
        {pending.length === 0 && (
          <div className="p-8 text-center" style={{ color: "var(--text-muted)" }}>
            <CheckCircle size={24} className="mx-auto mb-2" style={{ color: "var(--accent-emerald)" }} />
            <p className="text-sm">No pending alerts</p>
          </div>
        )}
        {pending.map((alert) => (
          <div key={alert.alert_id} className="p-4" style={{ borderBottom: "1px solid rgba(99,102,241,0.07)" }}>
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={`badge ${alert.decision === "BLOCK" ? "badge-block" : "badge-review"}`}>
                  {alert.decision === "BLOCK" ? <Shield size={10} /> : <Clock size={10} />}
                  {alert.decision}
                </span>
                <span className="font-mono text-xs" style={{ color: "var(--accent-indigo)", cursor: "pointer" }} onClick={() => onSelect(alert.transaction_id)}>
                  {alert.transaction_id} <ChevronRight size={10} className="inline" />
                </span>
              </div>
              <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                ₹{alert.amount?.toLocaleString() || "—"}
              </span>
            </div>

            <div className="flex gap-4 text-xs mb-3" style={{ color: "var(--text-muted)" }}>
              <span>{alert.user_id}</span>
              <span>{alert.merchant_category}</span>
              <span>{alert.city}</span>
              <span>Score: {((alert.combined_score || 0) * 100).toFixed(0)}%</span>
            </div>

            {alert.reason_codes && alert.reason_codes.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                {alert.reason_codes.slice(0, 3).map((r, i) => (
                  <span key={i} className="text-xs px-2 py-1 rounded-md" style={{ background: "rgba(251,191,36,0.08)", color: "var(--accent-amber)", border: "1px solid rgba(251,191,36,0.15)" }}>
                    {r}
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <button className="btn-action btn-approve" onClick={() => onAction(alert.alert_id, "approve")}>
                <CheckCircle size={12} /> Approve
              </button>
              <button className="btn-action btn-escalate" onClick={() => onAction(alert.alert_id, "escalate")}>
                <AlertTriangle size={12} /> Escalate
              </button>
              <button className="btn-action btn-fraud" onClick={() => onAction(alert.alert_id, "confirm_fraud")}>
                <Shield size={12} /> Confirm Fraud
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
