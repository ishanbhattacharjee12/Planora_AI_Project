import { useQuery } from "@tanstack/react-query";
import { adminApi } from "../../api";

export default function AuditLogs() {
  const { data: logs, isLoading } = useQuery({ queryKey: ["audit"], queryFn: adminApi.auditLogs });

  if (isLoading) return <div className="loading">Loading...</div>;

  return (
    <div className="page-shell">
      <div className="page-toolbar"><div><span className="page-kicker">Governance</span><h1 className="page-title">Audit logs</h1><p>A chronological record of sensitive platform activity.</p></div></div>
      <div className="table-wrap"><table className="table">
        <thead>
          <tr><th>Time</th><th>User</th><th>Action</th><th>Resource</th></tr>
        </thead>
        <tbody>
          {(logs || []).map((l) => (
            <tr key={l.id}>
              <td>{new Date(l.created_at).toLocaleString()}</td>
              <td>{l.user_id}</td>
              <td>{l.action}</td>
              <td>{l.resource_type}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
    </div>
  );
}
