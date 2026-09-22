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
      <div className="page-heading"><div><span className="page-kicker">Personal Workspace</span><h1>Employee Task Dashboard</h1><p>Track assigned tasks, monitor upcoming deadlines, and manage task execution in real time.</p></div></div>
      <div className="metric-grid metric-grid-four">
        <MetricCard label="Assigned Tasks" value={stats?.my_tasks ?? taskList.length} icon={<ClipboardList size={19} />} detail="Total Tasks" onClick={() => navigate("/employee/tasks")} />
        <MetricCard label="In Progress" value={count("in_progress")} icon={<Clock3 size={19} />} tone="positive" detail="Active Tasks" onClick={() => navigate("/employee/tasks")} />
        <MetricCard label="Completed Tasks" value={count("done")} icon={<CheckCircle2 size={19} />} tone="positive" detail="Delivered" onClick={() => navigate("/employee/tasks")} />
        <MetricCard label="High Priority" value={highPriority.length} icon={<AlertTriangle size={19} />} tone={highPriority.length ? "negative" : "positive"} detail="Requires Focus" onClick={() => navigate("/employee/tasks")} />
      </div>
      <div className="dashboard-grid">
        <Panel title="Task Momentum" eyebrow="Workload Distribution" className="distribution-panel"><DistributionChart centerLabel="Tasks" data={[{ name: "To Do", value: count("todo") }, { name: "In Progress", value: count("in_progress") }, { name: "Review", value: count("review") }, { name: "Done", value: count("done") }]} onSliceClick={() => navigate("/employee/tasks")} /></Panel>
        <Panel title="Status Mix" eyebrow="Task Assignments" className="distribution-panel"><DistributionChart centerLabel="Tasks" data={[{ name: "To Do", value: count("todo") }, { name: "In Progress", value: count("in_progress") }, { name: "Review", value: count("review") }, { name: "Done", value: count("done") }]} onSliceClick={() => navigate("/employee/tasks")} /></Panel>
      </div>
      <Panel title="Priority Queue" eyebrow="Next Actions"><div className="compact-list">{[...taskList].sort((a, b) => Number(["critical", "high"].includes(b.priority)) - Number(["critical", "high"].includes(a.priority))).slice(0, 6).map((task) => <div className="compact-row" key={task.id}><span className="task-id">{task.task_id}</span><span className="row-main"><strong>{task.name}</strong><small>{task.deadline ? `Due ${new Date(task.deadline).toLocaleDateString()}` : "No deadline set"}</small></span><span className={`badge badge-${task.priority}`}>{task.priority}</span><span className={`status-pill status-${task.status}`}>{task.status.replace(/_/g, " ")}</span></div>)}{!taskList.length && <div className="empty-state">You have no assigned tasks.</div>}</div></Panel>
    </div>
  );
}
