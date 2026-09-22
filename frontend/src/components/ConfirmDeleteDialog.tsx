import { useEffect } from "react";
import { Trash2, TriangleAlert, X } from "lucide-react";

interface ConfirmDeleteDialogProps {
  projectName: string;
  context: "project" | "log";
  isDeleting: boolean;
  error?: string;
  onCancel: () => void;
  onConfirm: () => void;
}

export default function ConfirmDeleteDialog({
  projectName,
  context,
  isDeleting,
  error,
  onCancel,
  onConfirm,
}: ConfirmDeleteDialogProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isDeleting) onCancel();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isDeleting, onCancel]);

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !isDeleting) onCancel();
    }}>
      <section className="delete-dialog" role="alertdialog" aria-modal="true" aria-labelledby="delete-dialog-title" aria-describedby="delete-dialog-description">
        <button className="modal-close" type="button" onClick={onCancel} disabled={isDeleting} aria-label="Close confirmation"><X size={18} /></button>
        <span className="delete-dialog-icon"><TriangleAlert size={24} /></span>
        <span className="page-kicker">Permanent deletion</span>
        <h2 id="delete-dialog-title">Delete “{projectName}”?</h2>
        <p id="delete-dialog-description">
          {context === "log"
            ? "Deleting this memory also removes its complete project, analysis, tasks, documents, and related records."
            : "This removes the project, its analysis, tasks, documents, memory log, and all related records."}
          {" "}This action cannot be undone.
        </p>
        {error && <div className="delete-dialog-error" role="alert">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onCancel} disabled={isDeleting}>Keep project</button>
          <button type="button" className="btn-danger" onClick={onConfirm} disabled={isDeleting} autoFocus><Trash2 size={16} />{isDeleting ? "Deleting..." : "Delete permanently"}</button>
        </div>
      </section>
    </div>
  );
}
