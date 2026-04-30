"use client";

const RULES = [
  { name: "High Amount + New Device", category: "Account Takeover", severity: "critical", description: "New device with amount >3x user baseline", threshold: "amount_ratio > 3 AND is_new_device = 1" },
  { name: "Impossible Travel", category: "Geo Anomaly", severity: "critical", description: "Location changed faster than physically possible", threshold: "speed > 800 km/h AND distance > 300 km" },
  { name: "Velocity Spike", category: "Velocity", severity: "high", description: "Unusually high transaction frequency", threshold: "tx_count_1h >= 5" },
  { name: "Night + High-Risk Merchant", category: "Behavioral", severity: "high", description: "Night-time transaction at high-risk merchant", threshold: "hour in [0-5] AND merchant_risk >= 0.35" },
  { name: "Amount Spike", category: "Amount Anomaly", severity: "high", description: "Transaction amount significantly above user baseline", threshold: "z_score > 3 AND ratio > 3x" },
  { name: "New Device + High-Risk Merchant", category: "Device", severity: "high", description: "First-time device at risky merchant category", threshold: "is_new_device = 1 AND merchant_risk >= 0.3" },
  { name: "Multiple Devices", category: "Device", severity: "medium", description: "User has more devices than typical", threshold: "device_count > 4" },
  { name: "High Merchant Risk + Large Amount", category: "Merchant", severity: "medium", description: "Large amount at high-risk merchant", threshold: "merchant_risk >= 0.4 AND amount > ₹5,000" },
];

export default function RulesPage() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12 }}>
        <div className="card kpi"><div className="kpi-label">Active Rules</div><div className="kpi-value" style={{ color: "var(--accent)", fontSize: 24 }}>{RULES.length}</div></div>
        <div className="card kpi"><div className="kpi-label">Critical</div><div className="kpi-value" style={{ color: "var(--danger)", fontSize: 24 }}>{RULES.filter(r => r.severity === "critical").length}</div></div>
        <div className="card kpi"><div className="kpi-label">High</div><div className="kpi-value" style={{ color: "var(--warning)", fontSize: 24 }}>{RULES.filter(r => r.severity === "high").length}</div></div>
        <div className="card kpi"><div className="kpi-label">Medium</div><div className="kpi-value" style={{ color: "var(--text-muted)", fontSize: 24 }}>{RULES.filter(r => r.severity === "medium").length}</div></div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Rules Engine Configuration</span></div>
        <table className="data-table">
          <thead><tr><th>Rule Name</th><th>Category</th><th>Severity</th><th>Description</th><th>Threshold</th><th>Status</th></tr></thead>
          <tbody>
            {RULES.map((r, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{r.name}</td>
                <td><span className="badge badge-info">{r.category}</span></td>
                <td><span className={`badge ${r.severity === "critical" ? "badge-block" : r.severity === "high" ? "badge-review" : "badge-info"}`}>{r.severity}</span></td>
                <td style={{ fontSize: 12 }}>{r.description}</td>
                <td className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>{r.threshold}</td>
                <td><span className="badge badge-approve">active</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
