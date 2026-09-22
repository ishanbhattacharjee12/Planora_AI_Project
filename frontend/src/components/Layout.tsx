import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { Activity, BriefcaseBusiness, ChevronRight, ClipboardList, FileClock, LayoutDashboard, Menu, Plus, Users, X } from "lucide-react";
import { useAuth } from "../auth/AuthContext";

const NAV: Record<string, Array<{ to: string; label: string; icon: typeof Activity }>> = {
  admin: [
    { to: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/admin/users", label: "Users", icon: Users },
    { to: "/admin/audit", label: "Audit Logs", icon: FileClock },
  ],
  manager: [
    { to: "/manager/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/manager/projects", label: "Projects", icon: BriefcaseBusiness },
    { to: "/manager/logs", label: "Logs", icon: FileClock },
    { to: "/manager/projects/create", label: "Create Project", icon: Plus },
  ],
  employee: [
    { to: "/employee/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/employee/tasks", label: "My Tasks", icon: ClipboardList },
  ],
};

const PAGE_NAMES: Record<string, string> = {
  dashboard: "Dashboard",
  projects: "Projects",
  create: "Create Project",
  tasks: "My Tasks",
  users: "User Management",
  audit: "Audit Logs",
  logs: "Project Memory Logs",
};

export default function Layout() {
  const { user } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const links = NAV[user?.role || "employee"] || [];
  const currentSegment = location.pathname.split("/").filter(Boolean).pop() || "dashboard";
  const currentPage = /^\d+$/.test(currentSegment) ? "Project Details" : (PAGE_NAMES[currentSegment] || "Workspace");
  const isActiveLink = (to: string) => {
    if (to.endsWith("/projects/create")) return location.pathname === to;
    if (to.endsWith("/projects")) return location.pathname === to || /^\/manager\/projects\/\d+$/.test(location.pathname);
    return location.pathname === to;
  };

  useEffect(() => {
    document.title = `${currentPage} · Planora AI`;
  }, [currentPage]);

  return (
    <div className="layout">
      <button className="mobile-menu-button" aria-label="Open navigation" onClick={() => setSidebarOpen(true)}><Menu size={20} /></button>
      {sidebarOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <img src="/rt-logo.png" alt="RandomTrees" />
          <button className="sidebar-close" aria-label="Close navigation" onClick={() => setSidebarOpen(false)}><X size={18} /></button>
        </div>
        <div className="product-name">
          <img className="product-icon" src="/planora-icon.svg" alt="" />
          <div><span>Planora AI</span><strong>Plan · Analyze · Deliver</strong></div>
        </div>
        <p className="nav-label">Workspace</p>
        <nav className="sidebar-nav">
        {links.map((l) => (
          <Link key={l.to} to={l.to} onClick={() => setSidebarOpen(false)} className={isActiveLink(l.to) ? "active" : ""}>
            <l.icon size={18} strokeWidth={1.8} /> <span>{l.label}</span><ChevronRight className="nav-chevron" size={14} />
          </Link>
        ))}
        </nav>
      </aside>
      <div className="app-frame">
        <header className="topbar">
          <div><span className="topbar-eyebrow">{user?.role} Workspace</span><strong>{currentPage}</strong></div>
          <div className="topbar-status"><span className="status-dot" />System Operational</div>
        </header>
        <main className="main"><Outlet /></main>
      </div>
    </div>
  );
}
