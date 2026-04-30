"use client";
export default function SettingsPage() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 600 }}>
      <div className="card">
        <div className="card-header"><span className="card-title">Platform Settings</span></div>
        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Analyst Name</label>
            <input defaultValue="R. Patel" style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg-raised)", color: "var(--text-primary)", fontSize: 13, outline: "none" }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Review Threshold</label>
            <input type="number" defaultValue="0.40" step="0.05" min="0" max="1" style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg-raised)", color: "var(--text-primary)", fontSize: 13, outline: "none" }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Block Threshold</label>
            <input type="number" defaultValue="0.85" step="0.05" min="0" max="1" style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg-raised)", color: "var(--text-primary)", fontSize: 13, outline: "none" }} />
          </div>
          <button className="btn btn-primary" style={{ alignSelf: "flex-start" }}>Save Changes</button>
        </div>
      </div>
    </div>
  );
}
