"use client";
import { Shield, Activity, AlertTriangle, CheckCircle, XCircle, TrendingUp } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

export function MetricCard({ label, value, icon, color, subtitle }: MetricCardProps) {
  return (
    <div className="glass-card p-5 animate-fade-in">
      <div className="flex items-start justify-between mb-3">
        <span style={{ color }} className="opacity-80">{icon}</span>
        {subtitle && <span className="text-xs" style={{ color: "var(--text-muted)" }}>{subtitle}</span>}
      </div>
      <div className="metric-value text-2xl mb-1">{value}</div>
      <div className="text-xs" style={{ color: "var(--text-muted)", letterSpacing: "0.5px" }}>{label}</div>
    </div>
  );
}

interface MetricsPanelProps {
  metrics: any;
  modelMetrics: any;
}

export function MetricsPanel({ metrics, modelMetrics }: MetricsPanelProps) {
  if (!metrics) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <MetricCard
        label="Total Transactions"
        value={metrics.total_transactions?.toLocaleString() || 0}
        icon={<Activity size={20} />}
        color="var(--accent-indigo)"
      />
      <MetricCard
        label="Active Alerts"
        value={metrics.pending_alerts || 0}
        icon={<AlertTriangle size={20} />}
        color="var(--accent-amber)"
        subtitle="pending"
      />
      <MetricCard
        label="Fraud Captured"
        value={`${((metrics.fraud_capture_rate || 0) * 100).toFixed(1)}%`}
        icon={<Shield size={20} />}
        color="var(--accent-emerald)"
        subtitle={`${metrics.fraud_caught || 0} / ${metrics.total_fraud || 0}`}
      />
      <MetricCard
        label="False Positive Rate"
        value={`${((metrics.false_positive_rate || 0) * 100).toFixed(2)}%`}
        icon={<XCircle size={20} />}
        color="var(--accent-rose)"
        subtitle={`${metrics.false_positives || 0} false alerts`}
      />
      <MetricCard
        label="Alert Precision"
        value={`${((metrics.alert_precision || 0) * 100).toFixed(1)}%`}
        icon={<CheckCircle size={20} />}
        color="var(--accent-cyan)"
      />
      <MetricCard
        label="Model AUC-ROC"
        value={modelMetrics?.auc_roc?.toFixed(4) || "—"}
        icon={<TrendingUp size={20} />}
        color="var(--accent-violet)"
        subtitle={`F1: ${modelMetrics?.f1_score?.toFixed(3) || "—"}`}
      />
    </div>
  );
}
