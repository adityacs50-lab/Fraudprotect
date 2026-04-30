"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, AlertTriangle, ArrowLeftRight, Shield,
  Activity, MessageSquare, Settings, Search, Bell, Zap
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/live-monitor", label: "Live Monitor", icon: Zap },
  { href: "/alerts", label: "Alert Queue", icon: AlertTriangle, badgeKey: "pending_alerts" },
  { href: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/rules", label: "Rules", icon: Shield },
  { href: "/model-health", label: "Model Health", icon: Activity },
  { href: "/feedback", label: "Feedback", icon: MessageSquare },
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    api.getMetrics().then(setMetrics).catch(() => {});
  }, []);

  return (
    <div className="shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-dot" />
          <span className="sidebar-brand-text">FraudShield</span>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            const badge = item.badgeKey && metrics ? metrics[item.badgeKey] : null;
            return (
              <Link key={item.href} href={item.href} className={`nav-item ${isActive ? "active" : ""}`}>
                <Icon size={16} />
                {item.label}
                {badge != null && badge > 0 && <span className="nav-badge">{badge}</span>}
              </Link>
            );
          })}
          <div style={{ flex: 1 }} />
          <Link href="/settings" className={`nav-item ${pathname === "/settings" ? "active" : ""}`}>
            <Settings size={16} /> Settings
          </Link>
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-status">
            <div className="live-dot" />
            <span>Live scoring active</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: "var(--text-muted)" }}>Analyst: R. Patel</div>
        </div>
      </aside>

      {/* Topbar */}
      <header className="topbar">
        <div>
          <span style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>
            {NAV_ITEMS.find(n => n.href === pathname || (n.href !== "/" && pathname.startsWith(n.href)))?.label || "FraudShield"}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ position: "relative" }}>
            <Search size={15} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              placeholder="Search alerts, transactions..."
              style={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 12px 6px 32px", fontSize: 13, color: "var(--text-secondary)", outline: "none", width: 260 }}
            />
          </div>
          <button className="btn" style={{ padding: "6px 8px", position: "relative" }}>
            <Bell size={15} />
            {metrics?.pending_alerts > 0 && (
              <span style={{ position: "absolute", top: -2, right: -2, width: 7, height: 7, borderRadius: "50%", background: "var(--danger)" }} />
            )}
          </button>
          <div style={{ width: 30, height: 30, borderRadius: 8, background: "var(--accent-muted)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: "var(--accent)" }}>RP</div>
        </div>
      </header>

      {/* Main content */}
      <main className="main">{children}</main>
    </div>
  );
}
