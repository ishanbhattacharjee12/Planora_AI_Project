import { useState } from "react";
import { Task, employeesApi, EmployeeRecommendation } from "../api";

interface Props {
  tasks: Task[];
}

export default function TeamRecommendations({ tasks }: Props) {
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [recommendations, setRecommendations] = useState<EmployeeRecommendation[]>([]);
  const [loading, setLoading] = useState(false);

  const loadRecommendations = async (taskId: number) => {
    setSelectedTaskId(taskId);
    setLoading(true);
    try {
      const recs = await employeesApi.recommendations(taskId);
      setRecommendations(recs);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3 style={{ marginBottom: 12 }}>Employee Recommendations</h3>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        {tasks.map((t) => (
          <button
            key={t.id}
            className={`btn-secondary ${selectedTaskId === t.id ? "btn-primary" : ""}`}
            onClick={() => loadRecommendations(t.id)}
          >
            {t.task_id}: {t.name}
          </button>
        ))}
      </div>
      {loading && <p>Loading recommendations...</p>}
      <table className="table">
        <thead>
          <tr><th>Employee</th><th>Skill Match</th><th>Workload</th><th>Recommendation</th><th>Gaps</th></tr>
        </thead>
        <tbody>
          {recommendations.map((r) => (
            <tr key={r.employee_id}>
              <td>{r.full_name}</td>
              <td>{r.skill_match_percent}%</td>
              <td>{r.workload_percent}%</td>
              <td><span className="badge badge-medium">{r.recommendation}</span></td>
              <td>{r.skill_gaps.map((g) => g.skill).join(", ") || "None"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {recommendations[0]?.narrative && (
        <div className="card" style={{ marginTop: 12 }}>
          <strong>AI Recommendation:</strong> {recommendations[0].narrative}
        </div>
      )}
    </div>
  );
}
