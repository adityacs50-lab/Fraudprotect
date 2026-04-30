"use client";
import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { Activity, Zap, Shield, AlertTriangle, CheckCircle, Clock } from "lucide-react";

export default function LiveMonitorPage() {
  const [stream, setStream] = useState<any[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [stats, setStats] = useState({ total: 0, flagged: 0, blocked: 0 });
  const scrollRef = useRef<HTMLDivElement>(null);

  const triggerStream = async () => {
    setIsStreaming(true);
    try {
      const res = await api.streamTransactions(10);
      // Fetch the actual transactions that were just generated
      const latestRes = await api.getTransactions(10);
      const latest = latestRes.transactions || [];
      
      setStream(prev => [...latest, ...prev].slice(0, 50));
      setStats(prev => ({
        total: prev.total + res.total,
        flagged: prev.flagged + (res.decisions.REVIEW || 0),
        blocked: prev.blocked + (res.decisions.BLOCK || 0)
      }));
    } catch (err) {
      console.error("Streaming error:", err);
    }
    setIsStreaming(false);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [stream]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, height: "calc(100vh - 120px)" }}>
      {/* Control Bar */}
      <div className="card" style={{ padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", gap: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div className="live-dot" style={{ width: 10, height: 10 }} />
            <span style={{ fontWeight: 600 }}>Live Scoring Engine</span>
          </div>
          <div style={{ display: "flex", gap: 16 }}>
            <div style={{ fontSize: 13 }}><span style={{ color: "var(--text-muted)" }}>Total Scored:</span> <span style={{ fontWeight: 600 }}>{stats.total}</span></div>
            <div style={{ fontSize: 13 }}><span style={{ color: "var(--text-muted)" }}>Flagged:</span> <span style={{ fontWeight: 600, color: "var(--warning)" }}>{stats.flagged}</span></div>
            <div style={{ fontSize: 13 }}><span style={{ color: "var(--text-muted)" }}>Blocked:</span> <span style={{ fontWeight: 600, color: "var(--danger)" }}>{stats.blocked}</span></div>
          </div>
        </div>
        <button 
          className="btn btn-primary" 
          onClick={triggerStream} 
          disabled={isStreaming}
          style={{ padding: "8px 20px" }}
        >
          <Zap size={15} fill="currentColor" /> {isStreaming ? "Scoring..." : "Simulate Incoming Stream"}
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20, flex: 1, overflow: "hidden" }}>
        {/* Stream List */}
        <div className="card" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div className="card-header">
            <span className="card-title">Real-Time Transaction Feed</span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Showing latest 50 events</span>
          </div>
          <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>User ID</th>
                  <th>Amount</th>
                  <th>Merchant</th>
                  <th>Risk Score</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                {stream.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                      <Activity size={32} style={{ marginBottom: 12, opacity: 0.2 }} />
                      <p>Click "Simulate Incoming Stream" to start monitoring</p>
                    </td>
                  </tr>
                )}
                {stream.map((tx, i) => (
                  <tr key={tx.transaction_id + i} className={tx.decision === "BLOCK" ? "row-block" : tx.decision === "REVIEW" ? "row-review" : ""}>
                    <td className="mono" style={{ fontSize: 11 }}>{new Date(tx.timestamp).toLocaleTimeString()}</td>
                    <td className="mono" style={{ fontSize: 11 }}>{tx.user_id}</td>
                    <td style={{ fontWeight: 600 }}>₹{tx.amount?.toLocaleString()}</td>
                    <td>{tx.merchant_category}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div className="score-bar-track">
                          <div 
                            className="score-bar-fill" 
                            style={{ 
                              width: `${(tx.combined_score || 0) * 100}%`,
                              background: tx.combined_score > 0.7 ? "var(--danger)" : tx.combined_score > 0.4 ? "var(--warning)" : "var(--accent)"
                            }} 
                          />
                        </div>
                        <span className="mono" style={{ fontSize: 11 }}>{((tx.combined_score || 0) * 100).toFixed(0)}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${tx.decision === "BLOCK" ? "badge-block" : tx.decision === "REVIEW" ? "badge-review" : "badge-approve"}`}>
                        {tx.decision}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Logs / Stats */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card">
            <div className="card-header"><span className="card-title">Decision Latency</span></div>
            <div className="card-body">
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {[
                  { label: "Rules Engine", val: "12ms", status: "success" },
                  { label: "Anomaly Detection", val: "28ms", status: "success" },
                  { label: "ML Classifier", val: "45ms", status: "success" },
                  { label: "SHAP Generation", val: "120ms", status: "warning" },
                ].map((item, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{item.label}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span className="mono" style={{ fontSize: 12, fontWeight: 600 }}>{item.val}</span>
                      <div style={{ width: 6, height: 6, borderRadius: "50%", background: `var(--${item.status})` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Risk Distribution</span></div>
            <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                <span>High Risk (70+)</span>
                <span style={{ fontWeight: 600 }}>{((stats.blocked / (stats.total || 1)) * 100).toFixed(1)}%</span>
              </div>
              <div style={{ width: "100%", height: 8, background: "var(--bg-raised)", borderRadius: 4, overflow: "hidden", display: "flex" }}>
                <div style={{ width: `${(stats.blocked / (stats.total || 1)) * 100}%`, background: "var(--danger)" }} />
                <div style={{ width: `${(stats.flagged / (stats.total || 1)) * 100}%`, background: "var(--warning)" }} />
                <div style={{ flex: 1, background: "var(--success)" }} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div className="badge badge-block" style={{ justifyContent: "center" }}>BLOCK</div>
                <div className="badge badge-review" style={{ justifyContent: "center" }}>REVIEW</div>
              </div>
            </div>
          </div>

          <div className="card" style={{ flex: 1 }}>
            <div className="card-header"><span className="card-title">Decision Logs</span></div>
            <div className="card-body" style={{ padding: 0 }}>
              <div style={{ display: "flex", flexDirection: "column" }}>
                {stream.filter(t => t.decision !== "APPROVE").slice(0, 5).map((t, i) => (
                  <div key={i} style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)", display: "flex", gap: 10 }}>
                    <AlertTriangle size={14} style={{ color: "var(--warning)", marginTop: 2 }} />
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600 }}>{t.decision} triggered for {t.user_id}</div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{JSON.parse(t.reason_codes || "[]")[0] || "Multiple risk factors"}</div>
                    </div>
                  </div>
                ))}
                {stream.length === 0 && <div style={{ padding: 24, textAlign: "center", fontSize: 12, color: "var(--text-muted)" }}>No high-risk events yet</div>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
