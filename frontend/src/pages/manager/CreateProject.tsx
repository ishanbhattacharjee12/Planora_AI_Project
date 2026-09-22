import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  Check,
  ExternalLink,
  Layers3,
  Sparkles,
  Target,
  UsersRound,
  X,
} from "lucide-react";
import { logsApi, projectsApi, ProjectCreateInput, SimilarProject } from "../../api";
import { BACKEND_OPTIONS, DATABASE_OPTIONS, FRONTEND_OPTIONS } from "../../constants/techStack";

const ANALYSIS_SECTIONS = [
  "Product Blueprint",
  "Solution Architecture",
  "Delivery Plan",
  "Team & Operations",
  "Launch & Growth",
];

export default function CreateProject() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [idea, setIdea] = useState("");
  const [description, setDescription] = useState("");
  const [businessObjective, setBusinessObjective] = useState("");
  const [primaryUsers, setPrimaryUsers] = useState("");
  const [organization, setOrganization] = useState("");
  const [projectType, setProjectType] = useState("");
  const [priority, setPriority] = useState<ProjectCreateInput["priority"]>("medium");
  const [classification, setClassification] = useState<ProjectCreateInput["classification"]>("internal");
  const [expectedDeadline, setExpectedDeadline] = useState("");
  const [businessConstraints, setBusinessConstraints] = useState("");
  const [technicalConstraints, setTechnicalConstraints] = useState("");
  const [frontendTechnology, setFrontendTechnology] = useState("");
  const [backendTechnology, setBackendTechnology] = useState("");
  const [databaseTechnology, setDatabaseTechnology] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [similarProjects, setSimilarProjects] = useState<SimilarProject[]>([]);

  const projectPayload = (): ProjectCreateInput => ({
    name: name.trim(),
    idea: idea.trim(),
    description: description.trim() || undefined,
    business_objective: businessObjective.trim() || undefined,
    primary_users: primaryUsers.trim() || undefined,
    organization: organization.trim() || undefined,
    project_type: projectType.trim() || undefined,
    priority,
    classification,
    expected_deadline: expectedDeadline ? `${expectedDeadline}T23:59:59` : undefined,
    frontend_technology: frontendTechnology,
    backend_technology: backendTechnology,
    database_technology: databaseTechnology,
    business_constraints: businessConstraints.trim() || undefined,
    technical_constraints: technicalConstraints.trim() || undefined,
  });

  const contextSignals = [
    name, idea, businessObjective, primaryUsers,
    frontendTechnology, backendTechnology, databaseTechnology,
    description || businessConstraints || technicalConstraints,
  ];
  const briefCompletion = Math.round((contextSignals.filter((value) => value.trim()).length / contextSignals.length) * 100);
  const selectedStack = [frontendTechnology, backendTechnology, databaseTechnology].filter(Boolean);

  const createProject = async () => {
    setLoading(true);
    setError("");
    try {
      const project = await projectsApi.create(projectPayload());
      navigate(`/manager/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const matches = await logsApi.findSimilar(projectPayload());
      if (matches.length) {
        setSimilarProjects(matches);
        return;
      }
      await createProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to check project memory");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-shell create-project-page">
      <div className="create-project-hero">
        <div>
          <span className="page-kicker">New initiative</span>
          <h1>Turn the idea into a build-ready brief.</h1>
          <p>Capture the decisions that matter. Planora AI turns them into five focused analysis sections.</p>
        </div>
        <div className="focused-analysis-badge"><Sparkles size={17} /> 5-section analysis</div>
      </div>

      <div className="create-project-layout">
        <form className="create-project-form" onSubmit={handleSubmit}>
          <section className="create-form-section">
            <div className="create-form-heading">
              <span><Layers3 size={18} /></span>
              <div><h2>Project essentials</h2><p>Name the initiative and explain what should be built.</p></div>
            </div>
            <div className="form-grid">
              <div className="form-group form-span">
                <label htmlFor="project-name">Project name</label>
                <input id="project-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Customer support knowledge hub" required />
              </div>
              <div className="form-group form-span">
                <div className="field-label-row"><label htmlFor="project-idea">Project idea</label><small>{idea.length} characters</small></div>
                <textarea id="project-idea" value={idea} onChange={(e) => setIdea(e.target.value)} rows={5} placeholder="Describe the problem, the intended solution, and what a successful experience looks like." required />
                <small className="field-help">Specific workflows and outcomes produce a more grounded analysis.</small>
              </div>
              <div className="form-group form-span">
                <label htmlFor="project-description">Supporting context <span>Optional</span></label>
                <textarea id="project-description" value={description} onChange={(e) => setDescription(e.target.value)} rows={3} placeholder="Existing process, background, or other context the analysis should consider." />
              </div>
            </div>
          </section>

          <section className="create-form-section">
            <div className="create-form-heading">
              <span><Target size={18} /></span>
              <div><h2>Outcome and audience</h2><p>Anchor recommendations to real goals and users.</p></div>
            </div>
            <div className="form-grid">
              <div className="form-group form-span"><label htmlFor="business-objective">Business objective</label><input id="business-objective" value={businessObjective} onChange={(e) => setBusinessObjective(e.target.value)} placeholder="What measurable outcome should this project improve?" /></div>
              <div className="form-group"><label htmlFor="primary-users">Primary users</label><input id="primary-users" value={primaryUsers} onChange={(e) => setPrimaryUsers(e.target.value)} placeholder="Teams, roles, or customer groups" /></div>
              <div className="form-group"><label htmlFor="organization">Organization</label><input id="organization" value={organization} onChange={(e) => setOrganization(e.target.value)} placeholder="Business or client name" /></div>
              <div className="form-group"><label htmlFor="project-type">Project type</label><input id="project-type" value={projectType} onChange={(e) => setProjectType(e.target.value)} placeholder="Web app, internal tool, platform…" /></div>
              <div className="form-group"><label htmlFor="deadline">Expected deadline <span>Optional</span></label><input id="deadline" type="date" value={expectedDeadline} onChange={(e) => setExpectedDeadline(e.target.value)} /></div>
              <div className="form-group"><label htmlFor="priority">Priority</label><select id="priority" value={priority} onChange={(e) => setPriority(e.target.value as ProjectCreateInput["priority"])}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></div>
              <div className="form-group"><label htmlFor="classification">Data classification</label><select id="classification" value={classification} onChange={(e) => setClassification(e.target.value as ProjectCreateInput["classification"])}><option value="public">Public</option><option value="internal">Internal</option><option value="confidential">Confidential</option><option value="highly_confidential">Highly confidential</option></select></div>
            </div>
          </section>

          <section className="create-form-section">
            <div className="create-form-heading">
              <span><UsersRound size={18} /></span>
              <div><h2>Technology and guardrails</h2><p>Keep architecture and delivery recommendations within your boundaries.</p></div>
            </div>
            <div className="form-grid form-grid-three">
              <div className="form-group"><label htmlFor="frontend-tech">Frontend</label><select id="frontend-tech" value={frontendTechnology} onChange={(e) => setFrontendTechnology(e.target.value)} required>{FRONTEND_OPTIONS.map((opt) => <option key={opt.value || "empty"} value={opt.value}>{opt.label}</option>)}</select></div>
              <div className="form-group"><label htmlFor="backend-tech">Backend</label><select id="backend-tech" value={backendTechnology} onChange={(e) => setBackendTechnology(e.target.value)} required>{BACKEND_OPTIONS.map((opt) => <option key={opt.value || "empty"} value={opt.value}>{opt.label}</option>)}</select></div>
              <div className="form-group"><label htmlFor="database-tech">Database</label><select id="database-tech" value={databaseTechnology} onChange={(e) => setDatabaseTechnology(e.target.value)} required>{DATABASE_OPTIONS.map((opt) => <option key={opt.value || "empty"} value={opt.value}>{opt.label}</option>)}</select></div>
              <div className="form-group"><label htmlFor="business-constraints">Business constraints <span>Optional</span></label><textarea id="business-constraints" value={businessConstraints} onChange={(e) => setBusinessConstraints(e.target.value)} rows={3} placeholder="Budget, timing, policy, staffing, or process limits" /></div>
              <div className="form-group"><label htmlFor="technical-constraints">Technical constraints <span>Optional</span></label><textarea id="technical-constraints" value={technicalConstraints} onChange={(e) => setTechnicalConstraints(e.target.value)} rows={3} placeholder="Hosting, integrations, compliance, or legacy systems" /></div>
            </div>
          </section>

          {error && <div className="error create-form-error" role="alert">{error}</div>}
          <div className="create-form-actions">
            <span>Required fields are marked by the browser.</span>
            <button type="submit" className="btn-primary" disabled={loading}>{loading ? "Checking project memory…" : <>Create project workspace <ArrowRight size={17} /></>}</button>
          </div>
        </form>

        <aside className="project-brief-panel">
          <span className="page-kicker">Brief quality</span>
          <div className="brief-score-row"><strong>{briefCompletion}%</strong><span>context supplied</span></div>
          <div className="brief-progress"><span style={{ width: `${briefCompletion}%` }} /></div>
          <p>More project-specific context helps reduce assumptions in the analysis.</p>

          <div className="brief-panel-block">
            <h3>Your selected stack</h3>
            <div className="stack-chip-list">
              {selectedStack.length ? selectedStack.map((item) => <span key={item}>{item}</span>) : <small>Select the three core technologies.</small>}
            </div>
          </div>

          <div className="brief-panel-block">
            <h3>What AI will produce</h3>
            <ol className="analysis-output-list">
              {ANALYSIS_SECTIONS.map((section, index) => <li key={section}><span>{index + 1}</span><div><strong>{section}</strong><small>{index < 4 ? "Focused project decisions" : "Launch and build handoff"}</small></div><Check size={15} /></li>)}
            </ol>
          </div>
        </aside>
      </div>

      {similarProjects.length > 0 && (
        <div className="modal-backdrop" role="presentation">
          <section className="similar-project-modal" role="dialog" aria-modal="true" aria-labelledby="similar-project-title">
            <button className="modal-close" type="button" onClick={() => setSimilarProjects([])} aria-label="Close"><X size={18} /></button>
            <div className="similar-modal-heading"><span className="warning-icon"><AlertTriangle size={22} /></span><div><span className="page-kicker">Project memory match</span><h2 id="similar-project-title">We already have a similar project. Please check.</h2><p>Review the existing work before creating another project. This can save analysis time and AI tokens.</p></div></div>
            <div className="similar-project-list">
              {similarProjects.map((match) => <article className="similar-project-item" key={match.project_id}><div className="similar-project-title-row"><h3>{match.project_name}</h3><span className="similarity-score">{Math.round(match.similarity * 100)}% match</span></div><p>{match.summary}</p><small>{match.architecture}</small><Link to={`/manager/projects/${match.project_id}`} className="text-link">View existing project <ExternalLink size={13} /></Link></article>)}
            </div>
            <div className="modal-actions"><button type="button" className="btn-secondary" onClick={() => setSimilarProjects([])}>Go back</button><button type="button" className="btn-primary" disabled={loading} onClick={createProject}>{loading ? "Creating…" : "Create anyway"}</button></div>
          </section>
        </div>
      )}
    </div>
  );
}
