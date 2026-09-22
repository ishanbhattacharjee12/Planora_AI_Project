import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronDown, Clock3, CheckCircle2, AlertTriangle, FileText, CheckCheck } from "lucide-react";
import { Project, projectsApi } from "../api";
import StatusChangeDialog from "./StatusChangeDialog";

interface ProjectStatusControlProps {
  project: Project;
}

const STATUS_OPTIONS: Array<{ value: string; label: string; description: string }> = [
  { value: "in_progress", label: "In Progress", description: "Project is currently in active delivery." },
  { value: "completed", label: "Completed", description: "Project deliverables are finished and delivered." },
  { value: "overdue", label: "Overdue", description: "Project has missed its deadline or delivery target." },
  { value: "review", label: "Review", description: "Project plan is ready for review." },
  { value: "approved", label: "Approved", description: "Project plan approved, ready for task generation." },
  { value: "draft", label: "Draft", description: "Initial project draft." },
];

export default function ProjectStatusControl({ project }: ProjectStatusControlProps) {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (newStatus: string) =>
      projectsApi.update(project.id, { status: newStatus }),
    onSuccess: async () => {
      setPendingStatus(null);
      setIsOpen(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["project", project.id] }),
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });

  // Include current status if not already present
  const options = [...STATUS_OPTIONS];
  if (!options.some((o) => o.value === project.status)) {
    options.unshift({
      value: project.status,
      label: project.status.replace(/_/g, " "),
      description: "Current project state.",
    });
  }

  const handleSelect = (statusValue: string) => {
    setIsOpen(false);
    if (statusValue === project.status) return;

    // For completed and overdue, require lightweight confirmation dialog
    if (statusValue === "completed" || statusValue === "overdue") {
      setPendingStatus(statusValue);
    } else {
      mutation.mutate(statusValue);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
      case "done":
        return <CheckCircle2 size={14} className="status-icon" />;
      case "overdue":
        return <AlertTriangle size={14} className="status-icon" />;
      case "in_progress":
      case "active":
        return <Clock3 size={14} className="status-icon" />;
      case "approved":
        return <CheckCheck size={14} className="status-icon" />;
      default:
        return <FileText size={14} className="status-icon" />;
    }
  };

  return (
    <div className="project-status-control-container">
      <div className="status-dropdown-wrapper">
        <label className="status-control-label" htmlFor="project-status-trigger">
          Status:
        </label>
        <div className="status-selector-relative">
          <button
            id="project-status-trigger"
            type="button"
            className={`status-pill status-pill-interactive status-${project.status}`}
            onClick={() => setIsOpen((prev) => !prev)}
            aria-haspopup="listbox"
            aria-expanded={isOpen}
            disabled={mutation.isPending}
          >
            {getStatusIcon(project.status)}
            <span>{project.status.replace(/_/g, " ")}</span>
            <ChevronDown size={14} className={`dropdown-chevron ${isOpen ? "open" : ""}`} />
          </button>

          {isOpen && (
            <>
              <div
                className="status-dropdown-scrim"
                onClick={() => setIsOpen(false)}
                aria-hidden="true"
              />
              <div
                className="status-dropdown-menu"
                role="listbox"
                aria-label="Change project status"
              >
                <div className="status-dropdown-header">
                  <span>Change project status</span>
                </div>
                {options.map((opt) => {
                  const isSelected = opt.value === project.status;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      className={`status-dropdown-item ${isSelected ? "selected" : ""}`}
                      onClick={() => handleSelect(opt.value)}
                    >
                      <div className="status-item-content">
                        <div className="status-item-title-row">
                          <span className={`status-pill status-${opt.value}`}>
                            {getStatusIcon(opt.value)}
                            <span>{opt.label}</span>
                          </span>
                          {isSelected && <Check size={14} className="status-check" />}
                        </div>
                        <p className="status-item-desc">{opt.description}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>

      {pendingStatus && (
        <StatusChangeDialog
          projectName={project.name}
          targetStatus={pendingStatus}
          isUpdating={mutation.isPending}
          error={mutation.error instanceof Error ? mutation.error.message : undefined}
          onCancel={() => {
            mutation.reset();
            setPendingStatus(null);
          }}
          onConfirm={() => mutation.mutate(pendingStatus)}
        />
      )}
    </div>
  );
}
