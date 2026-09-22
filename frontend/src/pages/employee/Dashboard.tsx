import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ClipboardList, Clock3 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { dashboardApi, tasksApi } from "../../api";
import { DistributionChart, MetricCard, Panel } from "../../components/DashboardWidgets";

export default function EmployeeDashboard() {
  const { data: stats } = useQuery({ queryKey: ["dashboard"], queryFn: dashboardApi.stats });
  const { data: tasks } = useQuery({ queryKey: ["my-tasks"], queryFn: tasksApi.my });
  const navigate = useNavigate();
  const taskList = tasks || [];
  const highPriority = taskList.filter((task) => task.priority === "high" || task.priority === "critical");
  const count = (status: string) => taskList.filter((task) => task.status === status).length;
  return (
    <div className="page-shell">
      <div className="page-heading"><div><span className="page-kicker">Personal workspace</span><h1>Your work, clearly framed.</h1><p>Priorities, progress, and deadlines in one focused view.</p></div></div>
      <div className="metric-grid metric-grid-four">
        <MetricCard label="Assigned tasks" value={stats?.my_tasks ?? taskList.length} icon={<ClipboardList size={19} />} detail="Total" onClick={() => navigate("/employee/tasks")} />
        <MetricCard label="In progress" value={count("in_progress")} icon={<Clock3 size={19} />} tone="positive" detail="Active" onClick={() => navigate("/employee/tasks")} />
        <MetricCard label="Completed" value={count("done")} icon={<CheckCircle2 size={19} />} tone="positive" detail="Done" onClick={() => navigate("/employee/tasks")} />
        <MetricCard label="High priority" value={highPriority.length} icon={<AlertTriangle size={19} />} tone={highPriority.length ? "negative" : "positive"} detail="Focus" onClick={() => navigate("/employee/tasks")} />
      </div>
      <div className="dashboard-grid">
        <Panel title="Task momentum" eyebrow="Workload" className="distribution-panel"><DistributionChart centerLabel="tasks" data={[{ name: "To do", value: count("todo") }, { name: "In progress", value: count("in_progress") }, { name: "Review", value: count("review") }, { name: "Done", value: count("done") }]} onSliceClick={() => navigate("/employee/tasks")} /></Panel>
        <Panel title="Status mix" eyebrow="My assignments" className="distribution-panel"><DistributionChart centerLabel="tasks" data={[{ name: "To do", value: count("todo") }, { name: "In progress", value: count("in_progress") }, { name: "Review", value: count("review") }, { name: "Done", value: count("done") }]} onSliceClick={() => navigate("/employee/tasks")} /></Panel>
      </div>
      <Panel title="Priority queue" eyebrow="Next actions"><div className="compact-list">{[...taskList].sort((a, b) => Number(["critical", "high"].includes(b.priority)) - Number(["critical", "high"].includes(a.priority))).slice(0, 6).map((task) => <div className="compact-row" key={task.id}><span className="task-id">{task.task_id}</span><span className="row-main"><strong>{task.name}</strong><small>{task.deadline ? `Due ${new Date(task.deadline).toLocaleDateString()}` : "No deadline set"}</small></span><span className={`badge badge-${task.priority}`}>{task.priority}</span><span className={`status-pill status-${task.status}`}>{task.status.replace(/_/g, " ")}</span></div>)}{!taskList.length && <div className="empty-state">You have no assigned tasks.</div>}</div></Panel>
    </div>
  );
}
