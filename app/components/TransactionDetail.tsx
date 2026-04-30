"use client";
import { X, Shield, MapPin, Smartphone, CreditCard, Clock, User } from "lucide-react";

interface Props {
  detail: any;
  onClose: () => void;
}

export function TransactionDetail({ detail, onClose }: Props) {
  if (!detail) return null;

  const reasons: string[] = Array.isArray(detail.reason_codes) ? detail.reason_codes : [];
  const shapDetails: any[] = Array.isArray(detail.shap_details) ? detail.shap_details : [];
  const maxShap = Math.max(...shapDetails.map((s: any) => Math.abs(s.shap_value || 0)), 0.01);

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 50, display: "flex", justifyContent: "flex-end" }}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }} onClick={onClose} />
      <div style={{ position: "relative", width: "560px", maxWidth: "100%", background: "var(--bg-secondary)", borderLeft: "1px solid var(--border-subtle)", overflowY: "auto", animation: "fadeInUp 0.3s ease" }}>
        {/* Header */}
        <div className="p-5 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-subtle)", background: "var(--bg-card)" }}>
          <div>
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>Transaction Detail</div>
            <div className="font-mono text-sm mt-1" style={{ color: "var(--accent-indigo)" }}>{detail.transaction_id}</div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg" style={{ background: "rgba(255,255,255,0.05)" }}><X size={16} /></button>
        </div>

        {/* Decision Banner */}
        <div className="p-4 mx-4 mt-4 rounded-xl" style={{ background: detail.decision === "BLOCK" ? "rgba(251,113,133,0.1)" : detail.decision === "REVIEW" ? "rgba(251,191,36,0.1)" : "rgba(52,211,153,0.1)", border: `1px solid ${detail.decision === "BLOCK" ? "rgba(251,113,133,0.2)" : detail.decision === "REVIEW" ? "rgba(251,191,36,0.2)" : "rgba(52,211,153,0.2)"}` }}>
          <div className="flex items-center justify-between">
            <span className={`badge ${detail.decision === "BLOCK" ? "badge-block" : detail.decision === "REVIEW" ? "badge-review" : "badge-approve"}`}>{detail.decision || "UNKNOWN"}</span>
            <span className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>₹{detail.amount?.toLocaleString()}</span>
          </div>
          <div className="grid grid-cols-3 gap-3 mt-3">
            <div><div className="text-xs" style={{ color: "var(--text-muted)" }}>Fraud Prob</div><div className="text-sm font-semibold" style={{ color: "var(--accent-rose)" }}>{((detail.fraud_probability || 0) * 100).toFixed(1)}%</div></div>
            <div><div className="text-xs" style={{ color: "var(--text-muted)" }}>Anomaly</div><div className="text-sm font-semibold" style={{ color: "var(--accent-amber)" }}>{((detail.anomaly_score || 0) * 100).toFixed(1)}%</div></div>
            <div><div className="text-xs" style={{ color: "var(--text-muted)" }}>Combined</div><div className="text-sm font-semibold" style={{ color: "var(--accent-indigo)" }}>{((detail.combined_score || 0) * 100).toFixed(1)}%</div></div>
          </div>
        </div>

        {/* Transaction Info */}
        <div className="p-4 mx-4 mt-4 rounded-xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
          <h4 className="text-xs font-semibold mb-3" style={{ color: "var(--text-muted)", letterSpacing: "0.5px", textTransform: "uppercase" }}>Transaction Info</h4>
          <div className="grid grid-cols-2 gap-3">
            {[
              { icon: <User size={13} />, label: "User", value: detail.user_id },
              { icon: <CreditCard size={13} />, label: "Payment", value: detail.payment_method },
              { icon: <MapPin size={13} />, label: "City", value: detail.city },
              { icon: <Smartphone size={13} />, label: "Device", value: detail.device_id?.slice(0, 16) },
              { icon: <Shield size={13} />, label: "Merchant", value: detail.merchant_category },
              { icon: <Clock size={13} />, label: "Time", value: detail.timestamp ? new Date(detail.timestamp).toLocaleString() : "—" },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-2">
                <span style={{ color: "var(--accent-indigo)" }}>{item.icon}</span>
                <div>
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>{item.label}</div>
                  <div className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>{item.value || "—"}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Reason Codes */}
        {reasons.length > 0 && (
          <div className="p-4 mx-4 mt-4 rounded-xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
            <h4 className="text-xs font-semibold mb-3" style={{ color: "var(--text-muted)", letterSpacing: "0.5px", textTransform: "uppercase" }}>Why It Was Flagged</h4>
            <div className="flex flex-col gap-2">
              {reasons.map((r: string, i: number) => (
                <div key={i} className="flex items-start gap-2 text-xs p-2 rounded-lg" style={{ background: "rgba(251,191,36,0.06)", border: "1px solid rgba(251,191,36,0.1)" }}>
                  <span style={{ color: "var(--accent-amber)", marginTop: "1px" }}>⚠</span>
                  <span style={{ color: "var(--text-secondary)" }}>{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SHAP Waterfall */}
        {shapDetails.length > 0 && (
          <div className="p-4 mx-4 mt-4 mb-4 rounded-xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
            <h4 className="text-xs font-semibold mb-3" style={{ color: "var(--text-muted)", letterSpacing: "0.5px", textTransform: "uppercase" }}>SHAP Feature Impact</h4>
            <div className="flex flex-col gap-3">
              {shapDetails.map((s: any, i: number) => {
                const pct = Math.abs(s.shap_value) / maxShap * 100;
                return (
                  <div key={i}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{s.display_name || s.feature}</span>
                      <span className="text-xs font-mono" style={{ color: s.shap_value > 0 ? "var(--accent-rose)" : "var(--accent-emerald)" }}>
                        {s.shap_value > 0 ? "+" : ""}{s.shap_value?.toFixed(3)}
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full" style={{ background: "rgba(255,255,255,0.04)" }}>
                      <div className={`shap-bar ${s.shap_value > 0 ? "shap-positive" : "shap-negative"}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                    </div>
                    <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>Value: {s.value?.toFixed?.(2) ?? s.value}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Rule Severity */}
        {detail.rule_severity && detail.rule_severity !== "none" && (
          <div className="p-4 mx-4 mb-4 rounded-xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
            <h4 className="text-xs font-semibold mb-2" style={{ color: "var(--text-muted)", letterSpacing: "0.5px", textTransform: "uppercase" }}>Rule Engine</h4>
            <div className="flex items-center gap-2">
              <span className={`badge ${detail.rule_severity === "critical" ? "badge-block" : "badge-review"}`}>{detail.rule_severity}</span>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{detail.rule_reasons}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
