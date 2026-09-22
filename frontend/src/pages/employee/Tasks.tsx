import { useQuery, useQueryClient } from "@tanstack/react-query";
import { tasksApi } from "../../api";

const STATUSES = ["todo", "in_progress", "review", "done"];

export default function EmployeeTasks() {
  const queryClient = useQueryClient();
  const { data: tasks, isLoading } = useQuery({ queryKey: ["my-tasks"], queryFn: tasksApi.my });

  const updateStatus = async (id: number, status: string) => {
    await tasksApi.update(id, { status } as { status: string });
    queryClient.invalidateQueries({ queryKey: ["my-tasks"] });
  };

  if (isLoading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-shell">
      <div className="page-toolbar"><div><span className="page-kicker">Delivery queue</span><h1 className="page-title">My tasks</h1><p>Update progress as work moves through delivery.</p></div></div>
      <div className="table-wrap"><table className="table">
        <thead>
          <tr><th>Task</th><th>Priority</th><th>Status</th><th>Update Status</th></tr>
        </thead>
        <tbody>
          {(tasks || []).map((t) => (
            <tr key={t.id}>
              <td><strong>{t.task_id}</strong> {t.name}</td>
              <td><span className={`badge badge-${t.priority}`}>{t.priority}</span></td>
              <td>{t.status}</td>
              <td>
                <select value={t.status} onChange={(e) => updateStatus(t.id, e.target.value)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table></div>
    </div>
  );
}
