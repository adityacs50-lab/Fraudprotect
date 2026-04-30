"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RefreshCw } from "lucide-react";

export default function TransactionsPage() {
  const [txns, setTxns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [streaming, setStreaming] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getTransactions(200);
      setTxns(data.transactions || []);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleStream = async () => {
    setStreaming(true);
    try {
      await api.streamTransactions(50);
      await load();
    } catch {}
    setStreaming(false);
  };

  const filtered = filter === "all" ? txns : txns.filter((t: any) => t.decision === filter.toUpperCase());

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div className="card">
        <div className="filter-bar">
          {["all", "approve", "review", "block"].map(f => (
            <button key={f} className={`filter-btn ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
          <div style={{ flex: 1 }} />
          <button className="btn btn-primary" onClick={handleStream} disabled={streaming} style={{ fontSize: 12 }}>
            <RefreshCw size={12} className={streaming ? "animate-spin" : ""} />
            {streaming ? "Scoring..." : "Stream New Batch"}
          </button>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{filtered.length} transactions</span>
        </div>
        <div style={{ overflowX: "auto", maxHeight: "calc(100vh - 180px)", overflowY: "auto" }}>
          {loading ? (
            <div style={{ padding: 32 }}>{[1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{ height: 38, marginBottom: 6, borderRadius: 6 }} />)}</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Transaction ID</th>
                  <th>User</th>
                  <th>Amount</th>
                  <th>Merchant</th>
                  <th>City</th>
                  <th>Payment</th>
                  <th>Fraud Score</th>
                  <th>Decision</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((tx: any) => (
                  <tr key={tx.transaction_id} className={tx.decision === "BLOCK" ? "row-block" : tx.decision === "REVIEW" ? "row-review" : ""}>
                    <td className="mono" style={{ color: "var(--accent)", fontSize: 11 }}>{tx.transaction_id}</td>
                    <td className="mono" style={{ fontSize: 11 }}>{tx.user_id}</td>
                    <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>₹{tx.amount?.toLocaleString()}</td>
                    <td>{tx.merchant_category}</td>
                    <td>{tx.city}</td>
                    <td><span className="badge badge-info" style={{ fontSize: 10 }}>{tx.payment_method}</span></td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <div className="score-bar-track">
                          <div className="score-bar-fill" style={{
                            width: `${(tx.fraud_probability || 0) * 100}%`,
                            background: tx.fraud_probability > 0.5 ? "var(--danger)" : tx.fraud_probability > 0.2 ? "var(--warning)" : "var(--success)"
                          }} />
                        </div>
                        <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>{((tx.fraud_probability || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td><span className={`badge ${tx.decision === "BLOCK" ? "badge-block" : tx.decision === "REVIEW" ? "badge-review" : "badge-approve"}`}>{tx.decision || "—"}</span></td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
