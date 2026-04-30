"use client";

interface Transaction {
  transaction_id: string;
  user_id: string;
  amount: number;
  merchant_category: string;
  city: string;
  payment_method: string;
  timestamp: string;
  decision?: string;
  risk_level?: string;
  combined_score?: number;
  fraud_probability?: number;
  anomaly_score?: number;
}

interface Props {
  transactions: Transaction[];
  onSelect: (id: string) => void;
}

function DecisionBadge({ decision }: { decision?: string }) {
  const cls = decision === "BLOCK" ? "badge-block" : decision === "REVIEW" ? "badge-review" : "badge-approve";
  return <span className={`badge ${cls}`}>{decision || "—"}</span>;
}

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
        <div className="h-full rounded-full" style={{ width: `${Math.min(value * 100, 100)}%`, background: color, transition: "width 0.4s ease" }} />
      </div>
      <span className="text-xs" style={{ color: "var(--text-muted)" }}>{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

export function TransactionTable({ transactions, onSelect }: Props) {
  return (
    <div className="glass-card overflow-hidden">
      <div className="p-4 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Live Transaction Feed</h3>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full pulse-live" style={{ background: "var(--accent-emerald)" }} />
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>{transactions.length} transactions</span>
        </div>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Transaction ID</th>
              <th>User</th>
              <th>Amount</th>
              <th>Merchant</th>
              <th>City</th>
              <th>Payment</th>
              <th>Fraud Prob</th>
              <th>Decision</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr
                key={tx.transaction_id}
                className={tx.decision === "BLOCK" ? "row-block" : tx.decision === "REVIEW" ? "row-review" : ""}
                onClick={() => onSelect(tx.transaction_id)}
                style={{ cursor: "pointer" }}
              >
                <td className="font-mono text-xs" style={{ color: "var(--accent-indigo)" }}>{tx.transaction_id}</td>
                <td className="font-mono text-xs">{tx.user_id}</td>
                <td className="font-semibold" style={{ color: "var(--text-primary)" }}>₹{tx.amount?.toLocaleString()}</td>
                <td>{tx.merchant_category}</td>
                <td>{tx.city}</td>
                <td><span className="badge" style={{ background: "rgba(99,102,241,0.1)", color: "var(--accent-indigo)", border: "1px solid var(--border-subtle)", fontSize: "11px", padding: "2px 8px" }}>{tx.payment_method}</span></td>
                <td><ScoreBar value={tx.fraud_probability || 0} color={tx.fraud_probability && tx.fraud_probability > 0.5 ? "var(--accent-rose)" : "var(--accent-emerald)"} /></td>
                <td><DecisionBadge decision={tx.decision} /></td>
                <td className="text-xs" style={{ color: "var(--text-muted)" }}>{tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
