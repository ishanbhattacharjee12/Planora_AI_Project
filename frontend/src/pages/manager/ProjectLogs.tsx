import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronLeft, ChevronRight, Database, ExternalLink, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { logsApi, ProjectMemoryLog } from "../../api";
import ConfirmDeleteDialog from "../../components/ConfirmDeleteDialog";

const LOGS_PER_PAGE = 4;

const STOP_WORDS = new Set([
  "about", "application", "based", "build", "data", "from", "into", "project",
  "system", "that", "their", "this", "using", "with", "will", "workspace",
]);

function memoryKeywords(log: ProjectMemoryLog): string[] {
  const source = `${log.architecture || ""} ${log.snippet || ""} ${log.summary || ""}`;
  const phrases = source
    .split(/\s*[|;,•\n]\s*/)
    .map((part) => part.trim().replace(/^(frontend|backend|database|architecture|stack):\s*/i, ""))
    .filter((part) => part.length >= 2 && part.length <= 32);
  const words = source.match(/[A-Za-z][A-Za-z0-9.+#/-]{2,}/g) || [];
  const seen = new Set<string>();
  const keywords: string[] = [];

  for (const candidate of [...phrases, ...words]) {
    const cleaned = candidate.replace(/[.()]+$/g, "").trim();
    const key = cleaned.toLowerCase();
    if (!cleaned || STOP_WORDS.has(key) || seen.has(key)) continue;
    seen.add(key);
    keywords.push(cleaned);
    if (keywords.length === 8) break;
  }
  return keywords;
}

export default function ProjectLogs() {
  const queryClient = useQueryClient();
  const [deleteTarget, setDeleteTarget] = useState<ProjectMemoryLog | null>(null);
  const [page, setPage] = useState(1);
  const { data: logs, isLoading } = useQuery({
    queryKey: ["project-memory-logs"],
    queryFn: logsApi.list,
  });
  const deleteMutation = useMutation({
    mutationFn: logsApi.removeProject,
    onSuccess: async () => {
      setDeleteTarget(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["project-memory-logs"] }),
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });

  const requestDelete = (log: ProjectMemoryLog) => {
    deleteMutation.reset();
    setDeleteTarget(log);
  };

  const cancelDelete = () => {
    if (deleteMutation.isPending) return;
    deleteMutation.reset();
    setDeleteTarget(null);
  };

  const pagination = useMemo(() => {
    const allLogs = logs || [];
    const totalPages = Math.max(1, Math.ceil(allLogs.length / LOGS_PER_PAGE));
    const currentPage = Math.min(page, totalPages);
    const startIndex = (currentPage - 1) * LOGS_PER_PAGE;
    return {
      allLogs,
      currentPage,
      totalPages,
      startIndex,
      visibleLogs: allLogs.slice(startIndex, startIndex + LOGS_PER_PAGE),
    };
  }, [logs, page]);

  if (isLoading) return <div className="loading">Loading project memory...</div>;

  return (
    <div className="page-shell logs-page">
      <div className="page-toolbar">
        <div>
          <span className="page-kicker">Semantic memory</span>
          <h1 className="page-title">Logs</h1>
          <p>Keyword summaries for quick scanning. Expand a record only when you need its full context.</p>
        </div>
        {!!logs?.length && <span className="logs-count">{logs.length} project memories</span>}
      </div>

      <div className="memory-grid compact-memory-grid">
        {pagination.visibleLogs.map((log) => {
          const keywords = memoryKeywords(log);
          return (
            <article className="card memory-card memory-card-compact" key={log.id}>
              <div className="memory-card-header">
                <span className="memory-icon"><Database size={17} /></span>
                <div>
                  <Link className="project-name-link" to={`/manager/projects/${log.project_id}`}>{log.project_name}</Link>
                  <span>Saved {new Date(log.updated_at).toLocaleDateString()}</span>
                </div>
                <div className="memory-card-actions">
                  <span className={`memory-status ${log.index_status}`}>{log.index_status}</span>
                  <button className="memory-delete-button" type="button" onClick={() => requestDelete(log)} aria-label={`Delete ${log.project_name}`} title={`Delete ${log.project_name}`}><Trash2 size={15} /></button>
                </div>
              </div>

              <div className="memory-keywords" aria-label={`${log.project_name} keywords`}>
                {keywords.length ? keywords.map((keyword) => <span key={keyword}>{keyword}</span>) : <span>Project memory</span>}
              </div>

              <details className="memory-details">
                <summary>View memory details <ChevronDown size={15} /></summary>
                <div className="memory-details-content">
                  <div className="memory-section"><strong>Snippet</strong><p>{log.snippet}</p></div>
                  <div className="memory-section"><strong>Summary</strong><p>{log.summary}</p></div>
                  <div className="memory-architecture">{log.architecture}</div>
                </div>
              </details>

              <Link className="text-link memory-open-link" to={`/manager/projects/${log.project_id}`}>Open project <ExternalLink size={13} /></Link>
            </article>
          );
        })}
        {!logs?.length && (
          <div className="card memory-empty">
            <Database size={24} />
            <h2>No project memories yet</h2>
            <p>New projects will automatically add a compact semantic record here.</p>
          </div>
        )}
      </div>
      {pagination.allLogs.length > LOGS_PER_PAGE && (
        <nav className="table-pagination logs-pagination" aria-label="Logs pagination">
          <span>Showing {pagination.startIndex + 1}–{Math.min(pagination.startIndex + LOGS_PER_PAGE, pagination.allLogs.length)} of {pagination.allLogs.length}</span>
          <div>
            <button className="pagination-button pagination-nav" onClick={() => setPage((value) => Math.max(1, value - 1))} disabled={pagination.currentPage === 1} aria-label="Previous logs page"><ChevronLeft size={16} />Previous</button>
            {Array.from({ length: pagination.totalPages }, (_, index) => index + 1).map((pageNumber) => (
              <button
                key={pageNumber}
                className={`pagination-button pagination-number ${pagination.currentPage === pageNumber ? "active" : ""}`}
                onClick={() => setPage(pageNumber)}
                aria-label={`Logs page ${pageNumber}`}
                aria-current={pagination.currentPage === pageNumber ? "page" : undefined}
              >
                {pageNumber}
              </button>
            ))}
            <button className="pagination-button pagination-nav" onClick={() => setPage((value) => Math.min(pagination.totalPages, value + 1))} disabled={pagination.currentPage === pagination.totalPages} aria-label="Next logs page">Next<ChevronRight size={16} /></button>
          </div>
        </nav>
      )}
      {deleteTarget && (
        <ConfirmDeleteDialog
          projectName={deleteTarget.project_name}
          context="log"
          isDeleting={deleteMutation.isPending}
          error={deleteMutation.error instanceof Error ? deleteMutation.error.message : undefined}
          onCancel={cancelDelete}
          onConfirm={() => deleteMutation.mutate(deleteTarget.project_id)}
        />
      )}
    </div>
  );
}
