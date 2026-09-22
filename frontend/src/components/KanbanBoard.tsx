import { useState } from "react";
import { Task, tasksApi, employeesApi } from "../api";

const COLUMNS = ["todo", "in_progress", "review", "done"] as const;
const LABELS: Record<string, string> = {
  todo: "To Do",
  in_progress: "In Progress",
  review: "Review",
  done: "Done",
};

interface Props {
  tasks: Task[];
  projectId: number;
  onUpdate: () => void;
}

export default function KanbanBoard({ tasks, projectId: _projectId, onUpdate }: Props) {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [employees, setEmployees] = useState<Array<{ id: number; full_name: string }>>([]);

  const moveTask = async (task: Task, status: string) => {
    await tasksApi.update(task.id, { status } as Partial<Task>);
    onUpdate();
  };

  const openAssign = async (task: Task) => {
    setSelectedTask(task);
    const emps = await employeesApi.list();
    setEmployees(emps.map((e) => ({ id: e.id, full_name: e.full_name })));
  };

  const assign = async (assigneeId: number) => {
    if (!selectedTask) return;
    await tasksApi.assign(selectedTask.id, assigneeId);
    setSelectedTask(null);
    onUpdate();
  };

  return (
    <div>
      <div className="kanban">
        {COLUMNS.map((col) => (
          <div key={col} className="kanban-col">
            <h3>{LABELS[col]}</h3>
            {tasks.filter((t) => t.status === col).map((task) => (
              <div key={task.id} className="kanban-card" onClick={() => openAssign(task)}>
                <strong>{task.task_id}</strong>
                <p style={{ fontSize: 13, marginTop: 4 }}>{task.name}</p>
                <span className={`badge badge-${task.priority}`}>{task.priority}</span>
                <div style={{ marginTop: 8, display: "flex", gap: 4, flexWrap: "wrap" }}>
                  {COLUMNS.filter((s) => s !== task.status).map((s) => (
                    <button
                      key={s}
                      className="btn-secondary"
                      style={{ fontSize: 11, padding: "2px 6px" }}
                      onClick={(e) => { e.stopPropagation(); moveTask(task, s); }}
                    >
                      → {LABELS[s]}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      {selectedTask && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3>Assign: {selectedTask.name}</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
            {employees.map((e) => (
              <button key={e.id} className="btn-secondary" onClick={() => assign(e.id)}>
                {e.full_name}
              </button>
            ))}
          </div>
          <button className="btn-secondary" style={{ marginTop: 12 }} onClick={() => setSelectedTask(null)}>Cancel</button>
        </div>
      )}
    </div>
  );
}
