import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, CircleAlert, Clock3, FolderKanban, ListTodo, Plus } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { dashboardApi, projectsApi } from "../../api";
import { DistributionChart, MetricCard, Panel } from "../../components/DashboardWidgets";

export default function ManagerDashboard() {
  const { data: stats } = useQuery({ queryKey: ["dashboard"], queryFn: dashboardApi.stats });
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: projectsApi.list });
  const navigate = useNavigate();
  const recentProjects = [...(projects || [])].sort((a, b) => +new Date(b.updated_at) - +new Date(a.updated_at)).slice(0, 5);
  const chartData = [
    { name: "Active", value: stats?.active_projects ?? 0 },
    { name: "Complete", value: stats?.completed_projects ?? 0 },
    { name: "Pending", value: stats?.pending_tasks ?? 0 },
    { name: "Overdue", value: stats?.overdue_tasks ?? 0 },
  ];

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div><span className="page-kicker">Portfolio command center</span><h1>Good to see you.</h1><p>Here is how delivery is moving across your workspace.</p></div>
        <Link to="/manager/projects/create" className="button btn-primary"><Plus size={17} />New project</Link>
      </div>
      <div className="metric-grid">
        <MetricCard label="Total projects" value={stats?.total_projects ?? 0} icon={<FolderKanban size={19} />} detail="Portfolio" onClick={() => navigate("/manager/projects")} />
        <MetricCard label="Active projects" value={stats?.active_projects ?? 0} icon={<Clock3 size={19} />} tone="positive" detail="In delivery" onClick={() => navigate("/manager/projects")} />
        <MetricCard label="Completed" value={stats?.completed_projects ?? 0} icon={<CheckCircle2 size={19} />} tone="positive" detail="Delivered" onClick={() => navigate("/manager/projects")} />
        <MetricCard label="Pending tasks" value={stats?.pending_tasks ?? 0} icon={<ListTodo size={19} />} detail="To action" onClick={() => navigate("/manager/projects")} />
        <MetricCard label="Overdue" value={stats?.overdue_tasks ?? 0} icon={<CircleAlert size={19} />} tone={stats?.overdue_tasks ? "negative" : "positive"} detail="Needs focus" onClick={() => navigate("/manager/projects")} />
      </div>
      <div className="dashboard-grid">
        <Panel title="Delivery pulse" eyebrow="Live portfolio" className="distribution-panel"><DistributionChart centerLabel="delivery items" data={chartData} onSliceClick={() => navigate("/manager/projects")} /></Panel>
        <Panel title="Project mix" eyebrow="Current state" className="distribution-panel"><DistributionChart centerLabel="projects" data={[{ name: "Active", value: stats?.active_projects ?? 0 }, { name: "Completed", value: stats?.completed_projects ?? 0 }, { name: "Other", value: Math.max(0, (stats?.total_projects ?? 0) - (stats?.active_projects ?? 0) - (stats?.completed_projects ?? 0)) }]} onSliceClick={() => navigate("/manager/projects")} /></Panel>
      </div>
      <Panel title="Recently updated" eyebrow="Projects" action={<Link className="text-link" to="/manager/projects">View all <ArrowRight size={14} /></Link>}>
        <div className="compact-list">
          {recentProjects.map((project) => <Link to={`/manager/projects/${project.id}`} className="compact-row" key={project.id}><span className="project-monogram">{project.name.slice(0, 2).toUpperCase()}</span><span className="row-main"><strong>{project.name}</strong><small>{project.classification} · Updated {new Date(project.updated_at).toLocaleDateString()}</small></span><span className={`status-pill status-${project.status}`}>{project.status.replace(/_/g, " ")}</span><ArrowRight size={16} /></Link>)}
          {!recentProjects.length && <div className="empty-state">No projects yet. Create one to start building your portfolio.</div>}
        </div>
      </Panel>
    </div>
  );
}
