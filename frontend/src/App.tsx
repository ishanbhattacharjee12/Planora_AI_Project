import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import Layout from "./components/Layout";
import ManagerDashboard from "./pages/manager/Dashboard";
import ProjectsList from "./pages/manager/ProjectsList";
import CreateProject from "./pages/manager/CreateProject";
import ProjectDetail from "./pages/manager/ProjectDetail";
import ProjectLogs from "./pages/manager/ProjectLogs";
import EmployeeDashboard from "./pages/employee/Dashboard";
import EmployeeTasks from "./pages/employee/Tasks";
import AdminDashboard from "./pages/admin/Dashboard";
import AuditLogs from "./pages/admin/AuditLogs";
import AdminUsers from "./pages/admin/Users";

const queryClient = new QueryClient();

function RoleRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="workspace-startup"><span className="startup-spinner" /><strong>Opening Planora AI</strong><p>Preparing your workspace...</p></div>;
  if (!user) {
    return <div className="workspace-startup workspace-startup-error"><strong>Workspace unavailable</strong><p>Planora AI could not establish a session. Check that the backend is running, then refresh.</p><button className="btn-primary" onClick={() => window.location.reload()}>Try again</button></div>;
  }
  return <Navigate to={`/${user.role}/dashboard`} replace />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<RoleRedirect />} />
            <Route path="/login" element={<Navigate to="/" replace />} />

            <Route element={<ProtectedRoute roles={["manager"]} />}>
              <Route element={<Layout />}>
                <Route path="/manager/dashboard" element={<ManagerDashboard />} />
                <Route path="/manager/projects" element={<ProjectsList />} />
                <Route path="/manager/projects/create" element={<CreateProject />} />
                <Route path="/manager/projects/:id" element={<ProjectDetail />} />
                <Route path="/manager/logs" element={<ProjectLogs />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute roles={["employee"]} />}>
              <Route element={<Layout />}>
                <Route path="/employee/dashboard" element={<EmployeeDashboard />} />
                <Route path="/employee/tasks" element={<EmployeeTasks />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute roles={["admin"]} />}>
              <Route element={<Layout />}>
                <Route path="/admin/dashboard" element={<AdminDashboard />} />
                <Route path="/admin/users" element={<AdminUsers />} />
                <Route path="/admin/audit" element={<AuditLogs />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
