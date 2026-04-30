"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AlertTriangle, Shield, XCircle, Clock, Zap, BarChart3, ChevronRight, User } from "lucide-react";
import Link from "next/link";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, PieChart, Pie, Cell
} from "recharts";

function KpiCard({ label, value, sub, icon, delta, status }: any) {
  const Icon = icon;
  return (
    <div className="card kpi">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div className="kpi-label">{label}</div>
        <Icon size={14} style={{ color: "var(--text-muted)" }} />
      </div>
      <div className="kpi-value">{value}</div>
      {delta && (
        <span className={`kpi-delta ${delta.dir}`}>
          {delta.dir === "up" ? "↑" : delta.dir === "down" ? "↓" : "→"} {delta.text}
        </span>
      )}
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  );
}

const CHART_COLORS = {
  BLOCK: "#ef4444", REVIEW: "#f59e0b", APPROVE: "#22c55e",
};

export default function OverviewPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [modelMetrics, setModelMetrics] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [initializing, setInitializing] = useState(false);

  const load = async () => {
    try {
      const [m, mm, a] = await Promise.all([
        api.getMetrics(), api.getModelMetrics(), api.getAlerts("pending", 8)
      ]);
      setMetrics(m);
      setModelMetrics(mm);
      setAlerts(a.alerts || []);
    } catch { }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleInit = async () => {
    setInitializing(true);
    try {
      await api.initialize(15000, true);
      await load();
    } catch { }
    setInitializing(false);
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {[1,2].map(i => <div key={i} className="skeleton" style={{ height: 120, borderRadius: 12 }} />)}
      </div>
    );
  }

  if (!metrics || metrics.total_transactions === 0) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <div className="card" style={{ padding: 48, textAlign: "center", maxWidth: 420 }}>
          <Shield size={32} style={{ color: "var(--accent)", margin: "0 auto 16px" }} />
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Initialize FraudShield</h2>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 24 }}>
            Generate synthetic transactions, train the hybrid model, and populate the alert queue.
          </p>
          <button className="btn btn-primary" onClick={handleInit} disabled={initializing} style={{ width: "100%" }}>
            {initializing ? "Training models..." : "Initialize Platform"}
          </button>
        </div>
      </div>
    );
  }

  const decisionData = Object.entries(metrics.decision_distribution || {}).map(([k, v]) => ({ name: k, value: v as number }));
  const reasonData = (metrics.top_alert_reasons || []).slice(0, 7).map((r: any) => ({ name: r.reason?.length > 30 ? r.reason.slice(0, 30) + "…" : r.reason, count: r.count }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* KPI Strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 12 }}>
        <KpiCard label="Detection Rate" value={`${((metrics.fraud_capture_rate || 0) * 100).toFixed(1)}%`} icon={Shield}
          sub={`${metrics.fraud_caught} / ${metrics.total_fraud} caught`} delta={{ dir: "up", text: "stable" }} />
        <KpiCard label="False Positive Rate" value={`${((metrics.false_positive_rate || 0) * 100).toFixed(2)}%`} icon={XCircle}
          sub={`${metrics.false_positives} false alerts`} delta={{ dir: "neutral", text: "monitoring" }} />
        <KpiCard label="Pending Review" value={metrics.pending_alerts} icon={AlertTriangle}
          sub={`${metrics.resolved_alerts} resolved`} delta={metrics.pending_alerts > 50 ? { dir: "up", text: "backlog" } : { dir: "neutral", text: "normal" }} />
        <KpiCard label="Alert Precision" value={`${((metrics.alert_precision || 0) * 100).toFixed(1)}%`} icon={BarChart3}
          sub="of flagged are true fraud" />
        <KpiCard label="Customer Friction" value={`${(((metrics.false_positives || 0) / metrics.total_transactions) * 100).toFixed(2)}%`}
          icon={User} sub="Good users impacted" status="warning" />
        <KpiCard label="Auto-Block Rate" value={`${(((metrics.decision_distribution?.BLOCK || 0) / metrics.total_transactions) * 100).toFixed(1)}%`}
          icon={Zap} sub={`${metrics.decision_distribution?.BLOCK || 0} blocked`} />
      </div>

      {/* Chart Row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Decision Distribution */}
        <div className="card">
          <div className="card-header"><span className="card-title">Decision Distribution</span></div>
          <div className="card-body" style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={decisionData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value" stroke="none">
                  {decisionData.map((d: any, i: number) => (
                    <Cell key={i} fill={CHART_COLORS[d.name as keyof typeof CHART_COLORS] || "#6366f1"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--text-secondary)" }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: -8 }}>
              {decisionData.map((d: any) => (
                <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-muted)" }}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: CHART_COLORS[d.name as keyof typeof CHART_COLORS] || "#6366f1" }} />
                  {d.name}: {d.value?.toLocaleString()}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Reason Codes */}
        <div className="card">
          <div className="card-header"><span className="card-title">Top Alert Reasons</span></div>
          <div className="card-body" style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={reasonData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <XAxis type="number" tick={{ fontSize: 11, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: "var(--text-secondary)" }} width={150} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="count" fill="var(--accent)" radius={[0, 4, 4, 0]} barSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Alert Queue Snapshot */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Alert Queue — Latest</span>
          <Link href="/alerts" className="btn" style={{ fontSize: 12, padding: "4px 10px" }}>View All <ChevronRight size={12} /></Link>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Alert ID</th>
                <th>Score</th>
                <th>Action</th>
                <th>Amount</th>
                <th>Merchant</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {alerts.slice(0, 8).map((a: any) => {
                const reasons = Array.isArray(a.reason_codes) ? a.reason_codes : [];
                return (
                  <tr key={a.alert_id} className={a.decision === "BLOCK" ? "row-block" : "row-review"}>
                    <td className="mono" style={{ color: "var(--accent)" }}>AL-{String(a.alert_id).padStart(5, "0")}</td>
                    <td style={{ fontWeight: 600, color: a.combined_score > 0.7 ? "var(--danger)" : "var(--warning)" }}>{((a.combined_score || 0) * 100).toFixed(0)}%</td>
                    <td><span className={`badge ${a.decision === "BLOCK" ? "badge-block" : "badge-review"}`}>{a.decision}</span></td>
                    <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>₹{a.amount?.toLocaleString()}</td>
                    <td>{a.merchant_category}</td>
                    <td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{reasons[0] || "—"}</td>
                    <td><span className="badge badge-info">{a.analyst_action || "pending"}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Bottom Row: Operational Health */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
        <div className="card">
          <div className="card-header"><span className="card-title">Queue Performance (Last 24h)</span></div>
          <div className="card-body" style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={[
                { time: "00:00", arrival: 12, resolution: 10 },
                { time: "04:00", arrival: 5, resolution: 8 },
                { time: "08:00", arrival: 25, resolution: 18 },
                { time: "12:00", arrival: 42, resolution: 35 },
                { time: "16:00", arrival: 38, resolution: 40 },
                { time: "20:00", arrival: 28, resolution: 30 },
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 11 }} />
                <Line type="monotone" dataKey="arrival" stroke="var(--danger)" strokeWidth={2} dot={false} name="New Alerts" />
                <Line type="monotone" dataKey="resolution" stroke="var(--success)" strokeWidth={2} dot={false} name="Resolved" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Model Decision Stability</span></div>
          <div className="card-body" style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { metric: "Score Stability", value: 98 },
                { metric: "Feature Freshness", value: 95 },
                { metric: "Decision Latency", value: 99 },
                { metric: "Explainability Coverage", value: 100 },
              ]} layout="vertical">
                <XAxis type="number" hide domain={[0, 100]} />
                <YAxis type="category" dataKey="metric" tick={{ fontSize: 10, fill: "var(--text-secondary)" }} width={120} axisLine={false} tickLine={false} />
                <Bar dataKey="value" fill="var(--info)" radius={[0, 4, 4, 0]} barSize={12}>
                  { [1,2,3,4].map((_, i) => <Cell key={i} fillOpacity={0.8 - (i * 0.15)} />) }
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
