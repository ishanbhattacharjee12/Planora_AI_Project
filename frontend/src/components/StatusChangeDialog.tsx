import { useEffect } from "react";
import { AlertTriangle, CheckCircle2, X } from "lucide-react";

interface StatusChangeDialogProps {
  projectName: string;
  targetStatus: "completed" | "overdue" | "in_progress" | string;
  isUpdating: boolean;
  error?: string;
  onCancel: () => void;
  onConfirm: () => void;
}

export default function StatusChangeDialog({
  projectName,
  targetStatus,
  isUpdating,
  error,
  onCancel,
  onConfirm,
}: StatusChangeDialogProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isUpdating) onCancel();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isUpdating, onCancel]);

  const isCompleted = targetStatus === "completed";
  const isOverdue = targetStatus === "overdue";
  const label = targetStatus.replace(/_/g, " ");

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isUpdating) onCancel();
      }}
    >
      <section
        className="delete-dialog status-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="status-dialog-title"
        aria-describedby="status-dialog-description"
      >
        <button
          className="modal-close"
          type="button"
          onClick={onCancel}
          disabled={isUpdating}
          aria-label="Close dialog"
        >
          <X size={18} />
        </button>
        <span
          className="delete-dialog-icon"
          style={
            isCompleted
              ? { color: "#256c42", background: "#e5f4eb" }
              : isOverdue
              ? { color: "#a82e29", background: "#fde9e7" }
              : { color: "#171717", background: "#f4f3ef" }
          }
        >
          {isCompleted ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}
        </span>
        <span className="page-kicker">Project lifecycle</span>
        <h2 id="status-dialog-title">
          {isCompleted
            ? `Mark "${projectName}" as completed?`
            : isOverdue
            ? `Mark "${projectName}" as overdue?`
            : `Change status to ${label}?`}
        </h2>
        <p id="status-dialog-description">
          {isCompleted
            ? "This updates the project lifecycle status to Completed and marks it as delivered in the portfolio dashboard."
            : isOverdue
            ? "This marks the project as Overdue to highlight delivery risk across your workspace and dashboard metrics."
            : `This will update the project lifecycle status to "${label}".`}
        </p>
        {error && <div className="delete-dialog-error" role="alert">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onCancel} disabled={isUpdating}>
            Cancel
          </button>
          <button
            type="button"
            className={isOverdue ? "button btn-primary" : "button btn-primary"}
            onClick={onConfirm}
            disabled={isUpdating}
            autoFocus
          >
            {isUpdating
              ? "Updating..."
              : isCompleted
              ? "Mark as Completed"
              : isOverdue
              ? "Mark as Overdue"
              : "Confirm"}
          </button>
        </div>
      </section>
    </div>
  );
}
