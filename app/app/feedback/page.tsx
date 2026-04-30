"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function FeedbackPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([api.getMetrics(), api.getAlerts("resolved", 50)])
      .then(([m, a]) => { setMetrics(m); setAlerts(a.alerts || []); })
      .catch(() => {});
  }, []);

  const actions = metrics?.analyst_actions || {};

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
        <div className="card kpi"><div className="kpi-label">Confirmed Fraud</div><div className="kpi-value" style={{ color: "var(--danger)", fontSize: 24 }}>{actions.confirm_fraud || 0}</div></div>
        <div className="card kpi"><div className="kpi-label">Approved (False Positive)</div><div className="kpi-value" style={{ color: "var(--success)", fontSize: 24 }}>{actions.approve || 0}</div></div>
        <div className="card kpi"><div className="kpi-label">Escalated</div><div className="kpi-value" style={{ color: "var(--warning)", fontSize: 24 }}>{actions.escalate || 0}</div></div>
        <div className="card kpi"><div className="kpi-label">Feedback Rate</div><div className="kpi-value" style={{ color: "var(--accent)", fontSize: 24 }}>
          {metrics ? `${((metrics.resolved_alerts / Math.max(metrics.total_alerts, 1)) * 100).toFixed(0)}%` : "—"}
        </div><div className="kpi-sub">{metrics?.resolved_alerts || 0} / {metrics?.total_alerts || 0} resolved</div></div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Resolved Alerts — Analyst Feedback</span></div>
        <table className="data-table">
          <thead><tr><th>Alert ID</th><th>Transaction</th><th>Decision</th><th>Analyst Action</th><th>Score</th><th>Resolved</th></tr></thead>
          <tbody>
            {alerts.map((a: any) => (
              <tr key={a.alert_id}>
                <td className="mono" style={{ color: "var(--accent)", fontSize: 11 }}>AL-{String(a.alert_id).padStart(5, "0")}</td>
                <td className="mono" style={{ fontSize: 11 }}>{a.transaction_id}</td>
                <td><span className={`badge ${a.decision === "BLOCK" ? "badge-block" : "badge-review"}`}>{a.decision}</span></td>
                <td><span className={`badge ${a.analyst_action === "confirm_fraud" ? "badge-block" : a.analyst_action === "approve" ? "badge-approve" : "badge-review"}`}>{a.analyst_action}</span></td>
                <td className="mono" style={{ fontSize: 11 }}>{((a.combined_score || 0) * 100).toFixed(0)}%</td>
                <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{a.resolved_at ? new Date(a.resolved_at).toLocaleString() : "—"}</td>
              </tr>
            ))}
            {alerts.length === 0 && <tr><td colSpan={6} style={{ textAlign: "center", color: "var(--text-muted)", padding: 32 }}>No resolved alerts yet. Take actions in the Alert Queue.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
