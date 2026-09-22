import { useEffect, useState } from "react";
import { Project, projectsApi } from "../api";

const DEFAULT_HOW_TO_READ =
  "This document is written as a practical starting point rather than a final technical specification. " +
  "The screens shown in the document are reference designs to help the team agree on what the system should provide. " +
  "The numbers and names visible in the mock-ups are examples and should be replaced with actual data during implementation.";

interface DocumentOverviewFormProps {
  project: Project;
  onSaved: () => void;
}

export default function DocumentOverviewForm({ project, onSaved }: DocumentOverviewFormProps) {
  const [organization, setOrganization] = useState(project.organization || "");
  const [documentType, setDocumentType] = useState(project.document_type || "Functional Documentation");
  const [primaryUsers, setPrimaryUsers] = useState(project.primary_users || "");
  const [purpose, setPurpose] = useState(project.business_objective || "");
  const [howToRead, setHowToRead] = useState(project.how_to_read || "");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setOrganization(project.organization || "");
    setDocumentType(project.document_type || "Functional Documentation");
    setPrimaryUsers(project.primary_users || "");
    setPurpose(project.business_objective || "");
    setHowToRead(project.how_to_read || "");
  }, [project]);

  const handleSave = async () => {
    setSaving(true);
    setSaveError("");
    setSaved(false);
    try {
      await projectsApi.update(project.id, {
        organization: organization || null,
        document_type: documentType || "Functional Documentation",
        primary_users: primaryUsers || null,
        business_objective: purpose || null,
        how_to_read: howToRead || null,
      });
      setSaved(true);
      onSaved();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save document overview");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <h3>Document Overview</h3>
      <p style={{ color: "#a5a5a5", marginTop: 4, marginBottom: 16 }}>
        These fields appear on page 1 of the PDF report.
      </p>

      <div className="form-group">
        <label>Project</label>
        <input value={project.name} readOnly disabled />
      </div>
      <div className="form-group">
        <label>Organization</label>
        <input
          value={organization}
          onChange={(e) => setOrganization(e.target.value)}
          placeholder="e.g. Random Trees"
        />
      </div>
      <div className="form-group">
        <label>Document Type</label>
        <input
          value={documentType}
          onChange={(e) => setDocumentType(e.target.value)}
          placeholder="Functional Documentation"
        />
      </div>
      <div className="form-group">
        <label>Primary Users</label>
        <textarea
          value={primaryUsers}
          onChange={(e) => setPrimaryUsers(e.target.value)}
          rows={2}
          placeholder="e.g. DE Leadership, Delivery Leads, Project Managers"
        />
      </div>
      <div className="form-group">
        <label>Purpose</label>
        <textarea
          value={purpose}
          onChange={(e) => setPurpose(e.target.value)}
          rows={3}
          placeholder="What this document is for"
        />
      </div>
      <div className="form-group">
        <label>Status</label>
        <input value={project.status} readOnly disabled />
      </div>
      <div className="form-group">
        <label>How to read this document</label>
        <textarea
          value={howToRead}
          onChange={(e) => setHowToRead(e.target.value)}
          rows={5}
          placeholder={DEFAULT_HOW_TO_READ}
        />
      </div>

      {saveError && <div className="error">{saveError}</div>}
      {saved && <div style={{ color: "#2f855a", marginBottom: 8 }}>Document overview saved.</div>}

      <button className="btn-primary" onClick={handleSave} disabled={saving}>
        {saving ? "Saving..." : "Save Document Overview"}
      </button>
    </div>
  );
}

