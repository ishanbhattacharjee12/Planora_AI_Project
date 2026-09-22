import { ListTodo, Users, Sparkles, FileClock } from "lucide-react";

interface EnhancementItem {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  icon: typeof ListTodo;
  badge: string;
}

const ENHANCEMENTS: EnhancementItem[] = [
  {
    id: "tasks",
    title: "Tasks & Workflow",
    subtitle: "Task Management",
    description: "Automated task breakdown, priority scheduling, dependency tracking, and Kanban boards.",
    icon: ListTodo,
    badge: "In Development",
  },
  {
    id: "team",
    title: "Team & Staffing",
    subtitle: "Team Collaboration",
    description: "Smart capacity allocation, skill matching, role recommendations, and workload distribution.",
    icon: Users,
    badge: "In Development",
  },
  {
    id: "assistant",
    title: "AI Assistant",
    subtitle: "AI Assistance",
    description: "Context-aware AI workspace chat for technical architecture Q&A, refactoring, and guidance.",
    icon: Sparkles,
    badge: "In Development",
  },
  {
    id: "versions",
    title: "Version History",
    subtitle: "Version Control",
    description: "Track iteration changes, audit logs, rollback capabilities, and historical blueprint versions.",
    icon: FileClock,
    badge: "In Development",
  },
];

export default function FutureEnhancements() {
  return (
    <div className="future-enhancements-section card" style={{ marginTop: 28 }}>
      <div className="panel-header" style={{ marginBottom: 16 }}>
        <div>
          <span className="panel-eyebrow">Roadmap & Capabilities</span>
          <h2 style={{ fontSize: 20, fontWeight: 750 }}>Future Enhancements</h2>
          <p style={{ color: "var(--muted)", fontSize: 14, marginTop: 4 }}>
            More capabilities are currently in development. These modules will expand the Planora AI project workspace.
          </p>
        </div>
      </div>

      <div
        className="future-enhancements-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: 16,
          marginTop: 16,
        }}
      >
        {ENHANCEMENTS.map((item) => {
          const IconComponent = item.icon;
          return (
            <div
              key={item.id}
              className="enhancement-card"
              style={{
                background: "#fafcfd",
                border: "1px solid var(--line)",
                borderRadius: 8,
                padding: 18,
                display: "flex",
                flexDirection: "column",
                gap: 12,
                position: "relative",
                transition: "border-color 0.2s ease",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 8,
                    background: "rgba(242, 200, 17, 0.15)",
                    color: "#806a00",
                    display: "grid",
                    placeItems: "center",
                  }}
                >
                  <IconComponent size={20} />
                </div>
                <span
                  className="status-pill"
                  style={{
                    background: "#f0f4f8",
                    color: "#475569",
                    fontSize: 11,
                    fontWeight: 700,
                    border: "1px solid #cbd5e1",
                  }}
                >
                  {item.badge}
                </span>
              </div>

              <div>
                <h4 style={{ fontSize: 15, fontWeight: 700, color: "var(--ink)" }}>
                  {item.title}
                </h4>
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 650,
                    color: "var(--muted)",
                    display: "block",
                    marginTop: 2,
                  }}
                >
                  {item.subtitle}
                </span>
                <p
                  style={{
                    fontSize: 13,
                    color: "#4b5563",
                    marginTop: 8,
                    lineHeight: 1.5,
                  }}
                >
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
