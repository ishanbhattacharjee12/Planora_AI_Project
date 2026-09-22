import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function ProtectedRoute({ roles }: { roles?: string[] }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="workspace-startup"><span className="startup-spinner" /><strong>Opening Planora AI</strong><p>Preparing your workspace...</p></div>;
  if (!user) return <Navigate to="/" replace />;
  if (roles && user.role !== "admin" && !roles.includes(user.role)) {
    return <Navigate to={`/${user.role}/dashboard`} replace />;
  }
  return <Outlet />;
}
