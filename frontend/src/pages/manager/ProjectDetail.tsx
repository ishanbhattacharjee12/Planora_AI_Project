import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AnalysisTokenUsage, projectsApi, tasksApi } from "../../api";
import {
  BACKEND_OPTIONS,
  DATABASE_OPTIONS,
  FRONTEND_OPTIONS,
  techLabel,
} from "../../constants/techStack";
import { AnalysisOverview } from "../../components/AnalysisDisplay";
import DocumentOverviewForm from "../../components/DocumentOverviewForm";
import { AnalysisTokenBar, useAnalysisUsagePoll } from "../../components/AnalysisTokenBar";
import FutureEnhancements from "../../components/FutureEnhancements";
import ProjectStatusControl from "../../components/ProjectStatusControl";

const TABS = ["Overview", "Analysis"];

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const [tab, setTab] = useState("Overview");
  const [analyzing, setAnalyzing] = useState(false);
  const [generatingTasks, setGeneratingTasks] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [error, setError] = useState("");
  const [tokenUsage, setTokenUsage] = useState<AnalysisTokenUsage | null>(null);
  const [analysisRunSince, setAnalysisRunSince] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.get(projectId),
  });
  const { data: analysis } = useQuery({
    queryKey: ["analysis", projectId],
    queryFn: () => projectsApi.getAnalysis(projectId),
    enabled: !!projectId,
  });
  const { data: tasks } = useQuery({
    queryKey: ["tasks", projectId],
    queryFn: () => tasksApi.byProject(projectId),
    enabled: !!projectId,
  });
  const { data: persistedUsage } = useQuery({
    queryKey: ["analysis-usage", projectId, project?.current_version],
    queryFn: () => projectsApi.getAnalysisUsage(projectId),
    enabled: !!projectId && !!project,
  });

  const displayUsage = analyzing ? tokenUsage : (tokenUsage ?? persistedUsage ?? null);

  useAnalysisUsagePoll(projectId, analyzing, analysisRunSince, (usage) => {
    setTokenUsage(usage);
  });

  const runAnalysis = async () => {
    const runStartedAt = new Date().toISOString();
    setAnalyzing(true);
    setError("");
    setAnalysisRunSince(runStartedAt);
    setTokenUsage({
      project_id: projectId,
      version_number: project?.current_version || 1,
      input_tokens: 0,
      output_tokens: 0,
      total_tokens: 0,
      request_count: 0,
      last_run_at: null,
    });
    try {
      const result = await projectsApi.analyze(projectId);
      setTokenUsage(result.token_usage);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["analysis", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["project", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["analysis-usage", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
      setTab("Analysis");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
      setAnalysisRunSince(null);
    }
  };

  const approve = async () => {
    setError("");
    try {
      await projectsApi.approve(projectId);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["project", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    }
  };

  const generateTasks = async () => {
    setGeneratingTasks(true);
    setError("");
    try {
      await projectsApi.generateTasks(projectId);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["tasks", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["project", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Task generation failed");
    } finally {
      setGeneratingTasks(false);
    }
  };

  const downloadPdf = async () => {
    setDownloadingPdf(true);
    setError("");
    try {
      const fallback = `${project?.name || "project"}-analysis-v${project?.current_version || 1}.pdf`;
      await projectsApi.downloadAnalysisPdf(projectId, fallback);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF download failed");
    } finally {
      setDownloadingPdf(false);
    }
  };

  const hasAnalysis = (analysis?.length || 0) > 0;
  const tasksCount = tasks?.length || 0;

  return (
    <div className="page-shell">
      <div className="page-toolbar">
        <div>
          <span className="page-kicker">Project workspace</span>
          <h1 className="page-title">{project?.name || "Project"}</h1>
        </div>
      </div>
      <div className="project-meta">
        {project ? (
          <ProjectStatusControl project={project} />
        ) : (
          <span className="status-pill">Loading...</span>
        )}
        <span>Priority: <strong>{project?.priority}</strong></span>
        <span>Version {project?.current_version}</span>
      </div>

      <div className="project-action-panel card">
        <div className="actions project-action-buttons">
          <button
            className="btn-primary"
            onClick={runAnalysis}
            disabled={analyzing}
          >
            {analyzing
              ? "Analyzing…"
              : hasAnalysis
              ? "Re-run AI Analysis"
              : "Run AI Analysis"}
          </button>

          {project?.status === "review" && (
            <button
              className="button"
              onClick={approve}
              disabled={analyzing}
            >
              Approve Plan
            </button>
          )}

          <button
            className="btn-primary"
            onClick={generateTasks}
            disabled={!hasAnalysis || analyzing || generatingTasks}
            title={!hasAnalysis ? "Run AI analysis first to generate tasks" : undefined}
          >
            {generatingTasks
              ? "Generating Tasks…"
              : tasksCount > 0
              ? `Generate Tasks (${tasksCount})`
              : "Generate Tasks"}
          </button>

          <button
            className="btn-primary"
            onClick={downloadPdf}
            disabled={!hasAnalysis || downloadingPdf}
            title={!hasAnalysis ? "Generate AI analysis first to download PDF report" : undefined}
          >
            {downloadingPdf ? "Preparing PDF..." : "Download PDF Report"}
          </button>
        </div>
        <AnalysisTokenBar
          usage={displayUsage}
          analyzing={analyzing}
          requestCount={displayUsage?.request_count}
        />
      </div>
      {error && <div className="error">{error}</div>}

      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? "active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview" && (
        <>
          <div className="card">
            <h3>Project Idea</h3>
            <p style={{ marginTop: 8, lineHeight: 1.6 }}>{project?.idea}</p>
            {project?.description && (
              <>
                <h3 style={{ marginTop: 16 }}>Description</h3>
                <p style={{ lineHeight: 1.6 }}>{project.description}</p>
              </>
            )}
            {(project?.frontend_technology ||
              project?.backend_technology ||
              project?.database_technology) && (
              <>
                <h3 style={{ marginTop: 16 }}>Tech Stack</h3>
                <ul style={{ marginTop: 8, lineHeight: 1.8 }}>
                  {project.frontend_technology && (
                    <li>
                      <strong>Frontend:</strong>{" "}
                      {techLabel(project.frontend_technology, FRONTEND_OPTIONS)}
                    </li>
                  )}
                  {project.backend_technology && (
                    <li>
                      <strong>Backend:</strong>{" "}
                      {techLabel(project.backend_technology, BACKEND_OPTIONS)}
                    </li>
                  )}
                  {project.database_technology && (
                    <li>
                      <strong>Database:</strong>{" "}
                      {techLabel(project.database_technology, DATABASE_OPTIONS)}
                    </li>
                  )}
                </ul>
              </>
            )}
          </div>
          {project && (
            <DocumentOverviewForm
              project={project}
              onSaved={() => queryClient.invalidateQueries({ queryKey: ["project", projectId] })}
            />
          )}
        </>
      )}

      {tab === "Analysis" && <AnalysisOverview analysis={analysis || []} />}

      <FutureEnhancements />
    </div>
  );
}
