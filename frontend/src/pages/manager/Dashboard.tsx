import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleAlert,
  Clock3,
  FolderKanban,
  ListTodo,
  Plus,
  RefreshCw,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { dashboardApi, projectsApi } from "../../api";
import { DistributionChart, MetricCard, Panel } from "../../components/DashboardWidgets";

export default function ManagerDashboard() {
  const navigate = useNavigate();

  const {
    data: stats,
    isLoading: isStatsLoading,
    isError: isStatsError,
    error: statsError,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ["dashboard"],
    queryFn: dashboardApi.stats,
    retry: 1,
  });

  const {
    data: projects,
    isLoading: isProjectsLoading,
    isError: isProjectsError,
    error: projectsError,
    refetch: refetchProjects,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: projectsApi.list,
    retry: 1,
  });

  const isLoading = isStatsLoading || isProjectsLoading;
  const isError = isStatsError || isProjectsError;

  const handleRetry = () => {
    refetchStats();
    refetchProjects();
  };

  const recentProjects = [...(projects || [])]
    .sort((a, b) => +new Date(b.updated_at) - +new Date(a.updated_at))
    .slice(0, 5);

  const activeProjects = stats?.active_projects ?? 0;
  const completedProjects = stats?.completed_projects ?? 0;
  const overdueProjects = stats?.overdue_projects ?? 0;
  const totalProjects = stats?.total_projects ?? 0;
  const pendingTasks = stats?.pending_tasks ?? 0;
  const overdueTasks = stats?.overdue_tasks ?? 0;
  const otherProjects = Math.max(0, totalProjects - activeProjects - completedProjects - overdueProjects);

  const chartData = [
    { name: "Active", value: activeProjects },
    { name: "Complete", value: completedProjects },
    { name: "Pending", value: pendingTasks },
    { name: "Overdue", value: overdueTasks + overdueProjects },
  ];

  const projectMixData = [
    { name: "Active", value: activeProjects },
    { name: "Completed", value: completedProjects },
    { name: "Overdue", value: overdueProjects },
    { name: "Other", value: otherProjects },
  ].filter((d) => d.value > 0 || d.name === "Active" || d.name === "Completed");

  const handleDeliveryPulseClick = (item: { name: string; value: number }) => {
    if (item.name === "Active") navigate("/manager/projects?status=active");
    else if (item.name === "Complete") navigate("/manager/projects?status=completed");
    else if (item.name === "Pending") navigate("/manager/projects?status=active");
    else if (item.name === "Overdue") navigate("/manager/projects?status=overdue");
    else navigate("/manager/projects");
  };

  const handleProjectMixClick = (item: { name: string; value: number }) => {
    if (item.name === "Active") navigate("/manager/projects?status=active");
    else if (item.name === "Completed") navigate("/manager/projects?status=completed");
    else if (item.name === "Overdue") navigate("/manager/projects?status=overdue");
    else navigate("/manager/projects");
  };

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <span className="page-kicker">Portfolio command center</span>
          <h1>Good to see you.</h1>
          <p>Here is how delivery is moving across your workspace.</p>
        </div>
        <Link to="/manager/projects/create" className="button btn-primary">
          <Plus size={17} />New project
        </Link>
      </div>

      {isError && (
        <div
          className="dashboard-error-banner card"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            background: "#fff1f2",
            border: "1px solid #fecdd3",
            borderRadius: 8,
            marginBottom: 20,
            gap: 16,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <AlertTriangle size={20} color="#e11d48" />
            <div>
              <strong style={{ color: "#9f1239", fontSize: 14 }}>
                Unable to load dashboard data.
              </strong>
              <p style={{ color: "#be123c", fontSize: 13, margin: 0 }}>
                {statsError instanceof Error
                  ? statsError.message
                  : projectsError instanceof Error
                  ? projectsError.message
                  : "A connection error occurred while retrieving your portfolio statistics."}
              </p>
            </div>
          </div>
          <button
            type="button"
            className="button"
            onClick={handleRetry}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              background: "#e11d48",
              color: "#fff",
              border: "none",
              padding: "8px 14px",
              borderRadius: 6,
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            <RefreshCw size={14} /> Retry
          </button>
        </div>
      )}

      {isLoading ? (
        <div
          className="dashboard-loading card"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "60px 20px",
            gap: 16,
            minHeight: 280,
          }}
        >
          <RefreshCw size={28} className="spinner" style={{ animation: "spin 1s linear infinite" }} />
          <span style={{ color: "var(--muted)", fontSize: 14, fontWeight: 600 }}>
            Loading dashboard data...
          </span>
        </div>
      ) : (
        <>
          <div className="metric-grid">
            <MetricCard
              label="Total projects"
              value={totalProjects}
              icon={<FolderKanban size={19} />}
              detail="Portfolio"
              onClick={() => navigate("/manager/projects")}
            />
            <MetricCard
              label="Active projects"
              value={activeProjects}
              icon={<Clock3 size={19} />}
              tone="positive"
              detail="In delivery"
              onClick={() => navigate("/manager/projects?status=active")}
            />
            <MetricCard
              label="Completed"
              value={completedProjects}
              icon={<CheckCircle2 size={19} />}
              tone="positive"
              detail="Delivered"
              onClick={() => navigate("/manager/projects?status=completed")}
            />
            <MetricCard
              label="Pending tasks"
              value={pendingTasks}
              icon={<ListTodo size={19} />}
              detail="Tasks remaining"
              onClick={() => navigate("/manager/projects?status=active")}
            />
            <MetricCard
              label="Overdue"
              value={overdueTasks + overdueProjects}
              icon={<CircleAlert size={19} />}
              tone={overdueTasks + overdueProjects > 0 ? "negative" : "positive"}
              detail="Needs focus"
              onClick={() => navigate("/manager/projects?status=overdue")}
            />
          </div>

          <div className="dashboard-grid">
            <Panel title="Delivery pulse" eyebrow="Live portfolio" className="distribution-panel">
              <DistributionChart
                centerLabel="delivery items"
                data={chartData}
                onSliceClick={handleDeliveryPulseClick}
              />
            </Panel>
            <Panel title="Project mix" eyebrow="Current state" className="distribution-panel">
              <DistributionChart
                centerLabel="projects"
                data={projectMixData}
                onSliceClick={handleProjectMixClick}
              />
            </Panel>
          </div>

          <Panel
            title="Recently updated"
            eyebrow="Projects"
            action={
              <Link className="text-link" to="/manager/projects">
                View all <ArrowRight size={14} />
              </Link>
            }
          >
            <div className="compact-list">
              {recentProjects.map((project) => (
                <Link
                  to={`/manager/projects/${project.id}`}
                  className="compact-row"
                  key={project.id}
                >
                  <span className="project-monogram">
                    {project.name.slice(0, 2).toUpperCase()}
                  </span>
                  <span className="row-main">
                    <strong>{project.name}</strong>
                    <small>
                      {project.classification} · Updated{" "}
                      {new Date(project.updated_at).toLocaleDateString()}
                    </small>
                  </span>
                  <span className={`status-pill status-${project.status}`}>
                    {project.status.replace(/_/g, " ")}
                  </span>
                  <ArrowRight size={16} />
                </Link>
              ))}
              {!recentProjects.length && (
                <div className="empty-state">
                  No projects yet. Create one to start building your portfolio.
                </div>
              )}
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
