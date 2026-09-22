import { ShieldCheck, UsersRound } from "lucide-react";

export default function AdminUsers() {
  return (
    <div className="page-shell">
      <div className="page-toolbar"><div><span className="page-kicker">Access control</span><h1 className="page-title">Users</h1><p>People and permissions across the Planora AI workspace.</p></div></div>
      <div className="dashboard-grid">
        <div className="card"><div className="metric-icon"><UsersRound size={20} /></div><h2 style={{ marginTop: 18, fontSize: 17 }}>User directory</h2><p className="analysis-muted" style={{ marginTop: 8 }}>User creation is currently managed through the secured admin API. Existing seeded accounts remain available for each role.</p></div>
        <div className="card"><div className="metric-icon"><ShieldCheck size={20} /></div><h2 style={{ marginTop: 18, fontSize: 17 }}>Role-based access</h2><p className="analysis-muted" style={{ marginTop: 8 }}>Admin, manager, and employee workspaces are isolated through the existing authorization rules.</p></div>
      </div>
    </div>
  );
}

