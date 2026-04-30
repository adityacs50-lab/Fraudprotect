"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { AlertTriangle, CheckCircle, Shield, ChevronRight, X, Clock, MapPin, Smartphone, CreditCard, User } from "lucide-react";

function AlertDetail({ detail, onClose, onAction }: { detail: any; onClose: () => void; onAction: (id: number, action: string) => void }) {
  if (!detail) return null;
  const reasons: string[] = Array.isArray(detail.reason_codes) ? detail.reason_codes : [];
  const shapDetails: any[] = Array.isArray(detail.shap_details) ? detail.shap_details : [];
  const maxShap = Math.max(...shapDetails.map((s: any) => Math.abs(s.shap_value || 0)), 0.01);

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer">
        <div className="drawer-section" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Alert Detail</div>
            <div className="mono" style={{ fontSize: 14, color: "var(--accent)", marginTop: 2 }}>AL-{String(detail.alert_id).padStart(5, "0")}</div>
          </div>
          <button className="btn" style={{ padding: 6 }} onClick={onClose}><X size={14} /></button>
        </div>

        {/* Decision banner */}
        <div className="drawer-section" style={{ background: detail.decision === "BLOCK" ? "var(--danger-muted)" : "var(--warning-muted)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className={`badge ${detail.decision === "BLOCK" ? "badge-block" : "badge-review"}`}>{detail.decision}</span>
            <span style={{ fontSize: 22, fontWeight: 700 }}>₹{detail.amount?.toLocaleString()}</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginTop: 12 }}>
            <div><div style={{ fontSize: 11, color: "var(--text-muted)" }}>Fraud Prob</div><div style={{ fontSize: 14, fontWeight: 600, color: "var(--danger)" }}>{((detail.fraud_probability || 0) * 100).toFixed(1)}%</div></div>
            <div><div style={{ fontSize: 11, color: "var(--text-muted)" }}>Anomaly</div><div style={{ fontSize: 14, fontWeight: 600, color: "var(--warning)" }}>{((detail.anomaly_score || 0) * 100).toFixed(1)}%</div></div>
            <div><div style={{ fontSize: 11, color: "var(--text-muted)" }}>Combined</div><div style={{ fontSize: 14, fontWeight: 600, color: "var(--accent)" }}>{((detail.combined_score || 0) * 100).toFixed(1)}%</div></div>
          </div>
        </div>

        {/* Transaction info */}
        <div className="drawer-section">
          <div className="drawer-section-title">Transaction Info</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {[
              { icon: <User size={12} />, label: "User", val: detail.user_id },
              { icon: <CreditCard size={12} />, label: "Payment", val: detail.payment_method },
              { icon: <MapPin size={12} />, label: "City", val: detail.city },
              { icon: <Smartphone size={12} />, label: "Device", val: detail.device_id?.slice(0, 18) },
              { icon: <Shield size={12} />, label: "Merchant", val: detail.merchant_category },
              { icon: <Clock size={12} />, label: "Time", val: detail.tx_timestamp ? new Date(detail.tx_timestamp).toLocaleString() : "—" },
            ].map((item, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--text-muted)" }}>{item.icon}</span>
                <div><div style={{ fontSize: 11, color: "var(--text-muted)" }}>{item.label}</div><div style={{ fontSize: 12, color: "var(--text-secondary)" }}>{item.val || "—"}</div></div>
              </div>
            ))}
          </div>
        </div>

        {/* Reason codes */}
        {reasons.length > 0 && (
          <div className="drawer-section">
            <div className="drawer-section-title">Why It Was Flagged</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {reasons.map((r: string, i: number) => (
                <div key={i} className="reason-chip">
                  <span className="reason-icon">⚠</span>
                  <span>{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SHAP */}
        {shapDetails.length > 0 && (
          <div className="drawer-section">
            <div className="drawer-section-title">SHAP Feature Impact</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {shapDetails.map((s: any, i: number) => {
                const pct = (Math.abs(s.shap_value) / maxShap) * 100;
                return (
                  <div key={i}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                      <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{s.display_name || s.feature}</span>
                      <span className="mono" style={{ fontSize: 11, color: s.shap_value > 0 ? "var(--danger)" : "var(--success)" }}>
                        {s.shap_value > 0 ? "+" : ""}{s.shap_value?.toFixed(3)}
                      </span>
                    </div>
                    <div style={{ width: "100%", height: 6, borderRadius: 3, background: "rgba(255,255,255,0.03)" }}>
                      <div className={`shap-bar ${s.shap_value > 0 ? "shap-up" : "shap-down"}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Actions */}
        {!detail.analyst_action && (
          <div className="drawer-section" style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-success" onClick={() => onAction(detail.alert_id, "approve")}><CheckCircle size={13} /> Approve</button>
            <button className="btn btn-warning" onClick={() => onAction(detail.alert_id, "escalate")}><AlertTriangle size={13} /> Escalate</button>
            <button className="btn btn-danger" onClick={() => onAction(detail.alert_id, "confirm_fraud")}><Shield size={13} /> Confirm Fraud</button>
          </div>
        )}
        {detail.analyst_action && (
          <div className="drawer-section">
            <span className="badge badge-info">Resolved: {detail.analyst_action}</span>
          </div>
        )}
      </div>
    </>
  );
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [filter, setFilter] = useState<string>("pending");
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts(filter === "all" ? undefined : filter, 200);
      setAlerts(data.alerts || []);
    } catch { }
    setLoading(false);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const handleAction = async (alertId: number, action: string) => {
    try {
      await api.alertAction(alertId, action);
      setSelected(null);
      load();
    } catch { }
  };

  const handleSelect = async (alert: any) => {
    try {
      const detail = await api.getTransaction(alert.transaction_id);
      setSelected({ ...alert, ...detail });
    } catch {
      setSelected(alert);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Filter bar */}
      <div className="card">
        <div className="filter-bar">
          {["pending", "resolved", "all"].map((f) => (
            <button key={f} className={`filter-btn ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{alerts.length} alerts</span>
        </div>
        <div style={{ overflowX: "auto", maxHeight: "calc(100vh - 200px)", overflowY: "auto" }}>
          {loading ? (
            <div style={{ padding: 32 }}>{[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: 42, marginBottom: 8, borderRadius: 6 }} />)}</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Alert ID</th>
                  <th>Score</th>
                  <th>Action</th>
                  <th>Amount</th>
                  <th>Customer</th>
                  <th>Merchant</th>
                  <th>Top Reason</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a: any) => {
                  const reasons = Array.isArray(a.reason_codes) ? a.reason_codes : [];
                  return (
                    <tr key={a.alert_id} className={a.decision === "BLOCK" ? "row-block" : a.decision === "REVIEW" ? "row-review" : ""} onClick={() => handleSelect(a)}>
                      <td className="mono" style={{ color: "var(--accent)" }}>AL-{String(a.alert_id).padStart(5, "0")}</td>
                      <td style={{ fontWeight: 600, color: a.combined_score > 0.7 ? "var(--danger)" : a.combined_score > 0.4 ? "var(--warning)" : "var(--text-muted)" }}>{((a.combined_score || 0) * 100).toFixed(0)}%</td>
                      <td><span className={`badge ${a.decision === "BLOCK" ? "badge-block" : "badge-review"}`}>{a.decision}</span></td>
                      <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>₹{a.amount?.toLocaleString()}</td>
                      <td className="mono" style={{ fontSize: 11 }}>{a.user_id}</td>
                      <td>{a.merchant_category}</td>
                      <td style={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: 12 }}>{reasons[0] || "—"}</td>
                      <td>
                        {a.analyst_action ? (
                          <span className="badge badge-approve">{a.analyst_action}</span>
                        ) : (
                          <span className="badge badge-info">pending</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Detail drawer */}
      {selected && <AlertDetail detail={selected} onClose={() => setSelected(null)} onAction={handleAction} />}
    </div>
  );
}
