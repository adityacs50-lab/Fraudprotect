"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

function MetricRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
      <span style={{ fontSize: 13, color: "var(--text-muted)" }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 600, color: color || "var(--text-primary)", fontFamily: "monospace" }}>{value}</span>
    </div>
  );
}

export default function ModelHealthPage() {
  const [model, setModel] = useState<any>(null);
  const [importance, setImportance] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getModelMetrics(), api.getFeatureImportance()])
      .then(([m, imp]) => { setModel(m); setImportance(imp.feature_importance); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="skeleton" style={{ height: 300, borderRadius: 12 }} />;
  if (!model) return <div className="card card-body" style={{ textAlign: "center", color: "var(--text-muted)", padding: 48 }}>No model data. Initialize the platform first.</div>;

  const impData = importance
    ? Object.entries(importance).slice(0, 12).map(([k, v]) => ({ name: k.replace(/_/g, " "), value: Number(((v as number) * 100).toFixed(1)) }))
    : [];

  const cm = [
    ["", "Pred Legit", "Pred Fraud"],
    ["Actual Legit", model.true_negatives, model.false_positives],
    ["Actual Fraud", model.false_negatives, model.true_positives],
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* KPI strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12 }}>
        {[
          { label: "Precision", value: model.precision?.toFixed(4), color: "var(--accent)" },
          { label: "Recall", value: model.recall?.toFixed(4), color: "var(--warning)" },
          { label: "F1 Score", value: model.f1_score?.toFixed(4), color: "var(--info)" },
          { label: "AUC-ROC", value: model.auc_roc?.toFixed(4), color: "var(--success)" },
          { label: "False Positive Rate", value: model.false_positive_rate?.toFixed(4), color: "var(--danger)" },
        ].map((m, i) => (
          <div key={i} className="card kpi">
            <div className="kpi-label">{m.label}</div>
            <div className="kpi-value" style={{ color: m.color, fontSize: 24 }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Confusion Matrix */}
        <div className="card">
          <div className="card-header"><span className="card-title">Confusion Matrix</span></div>
          <div className="card-body">
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                {cm.map((row, ri) => (
                  <tr key={ri}>
                    {row.map((cell, ci) => (
                      <td key={ci} style={{
                        padding: "12px 16px",
                        textAlign: "center",
                        fontSize: ri === 0 || ci === 0 ? 11 : 18,
                        fontWeight: ri === 0 || ci === 0 ? 600 : 700,
                        color: ri === 0 || ci === 0 ? "var(--text-muted)" : "var(--text-primary)",
                        background: ri > 0 && ci > 0 ? (
                          (ri === 1 && ci === 1) || (ri === 2 && ci === 2) ? "var(--success-muted)" : "var(--danger-muted)"
                        ) : "transparent",
                        borderRadius: ri > 0 && ci > 0 ? 8 : 0,
                        textTransform: ri === 0 || ci === 0 ? "uppercase" : "none",
                        letterSpacing: ri === 0 || ci === 0 ? "0.5px" : undefined,
                      }}>
                        {typeof cell === "number" ? cell.toLocaleString() : cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ marginTop: 16 }}>
              <MetricRow label="Test Set Size" value={model.test_size?.toLocaleString()} />
              <MetricRow label="Train Fraud Rate" value={`${(model.fraud_rate_train * 100).toFixed(2)}%`} />
              <MetricRow label="Test Fraud Rate" value={`${(model.fraud_rate_test * 100).toFixed(2)}%`} />
            </div>
          </div>
        </div>

        {/* Feature Importance */}
        <div className="card">
          <div className="card-header"><span className="card-title">Global Feature Importance (SHAP)</span></div>
          <div className="card-body" style={{ height: 360 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={impData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <XAxis type="number" tick={{ fontSize: 10, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11, fill: "var(--text-secondary)" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} formatter={(v: any) => `${v}%`} />
                <Bar dataKey="value" fill="var(--accent)" radius={[0, 4, 4, 0]} barSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
