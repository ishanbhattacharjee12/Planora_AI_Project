import { useQuery } from "@tanstack/react-query";
import { Activity, CheckCircle2, FolderKanban, ListTodo } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { adminApi, dashboardApi } from "../../api";
import { DistributionChart, MetricCard, Panel } from "../../components/DashboardWidgets";

export default function AdminDashboard() {
  const { data: stats } = useQuery({ queryKey: ["dashboard"], queryFn: dashboardApi.stats });
  const navigate = useNavigate();
  const { data: logs } = useQuery({ queryKey: ["audit"], queryFn: adminApi.auditLogs });
  const recentLogs = (logs || []).slice(0, 6);
  return (
    <div className="page-shell">
      <div className="page-heading"><div><span className="page-kicker">System Overview</span><h1>Administrative Console</h1><p>Monitor platform operations, system activities, and governance logs across the organization.</p></div></div>
      <div className="metric-grid metric-grid-four">
        <MetricCard label="Total Projects" value={stats?.total_projects ?? 0} icon={<FolderKanban size={19} />} detail="All Time" onClick={() => navigate("/admin/audit")} />
        <MetricCard label="Active Projects" value={stats?.active_projects ?? 0} icon={<Activity size={19} />} tone="positive" detail="In Delivery" onClick={() => navigate("/admin/audit")} />
        <MetricCard label="Completed Projects" value={stats?.completed_projects ?? 0} icon={<CheckCircle2 size={19} />} tone="positive" detail="Delivered" onClick={() => navigate("/admin/audit")} />
        <MetricCard label="Pending Tasks" value={stats?.pending_tasks ?? 0} icon={<ListTodo size={19} />} detail="Open Tasks" onClick={() => navigate("/admin/audit")} />
      </div>
      <div className="dashboard-grid">
        <Panel title="Delivery Health" eyebrow="Platform Activity" className="distribution-panel"><DistributionChart centerLabel="Activity Items" data={[{ name: "Active", value: stats?.active_projects ?? 0 }, { name: "Completed", value: stats?.completed_projects ?? 0 }, { name: "Pending", value: stats?.pending_tasks ?? 0 }, { name: "Overdue", value: stats?.overdue_tasks ?? 0 }]} onSliceClick={() => navigate("/admin/audit")} /></Panel>
        <Panel title="Project Distribution" eyebrow="Portfolio State" className="distribution-panel"><DistributionChart centerLabel="Projects" data={[{ name: "Active", value: stats?.active_projects ?? 0 }, { name: "Completed", value: stats?.completed_projects ?? 0 }, { name: "Other", value: Math.max(0, (stats?.total_projects ?? 0) - (stats?.active_projects ?? 0) - (stats?.completed_projects ?? 0)) }]} onSliceClick={() => navigate("/admin/audit")} /></Panel>
      </div>
      <Panel title="Recent Audit Activity" eyebrow="Audit Trail"><div className="compact-list">{recentLogs.map((log) => <div className="compact-row" key={log.id}><span className="activity-mark"><Activity size={15} /></span><span className="row-main"><strong>{log.action.replace(/_/g, " ")}</strong><small>{log.resource_type || "System"} · User {log.user_id ?? "System"}</small></span><time>{new Date(log.created_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}</time></div>)}{!recentLogs.length && <div className="empty-state">No audit activity recorded yet.</div>}</div></Panel>
    </div>
  );
}
