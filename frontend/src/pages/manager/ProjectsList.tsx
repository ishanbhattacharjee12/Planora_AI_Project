import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Plus, Search, Trash2 } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import { Project, projectsApi } from "../../api";
import ConfirmDeleteDialog from "../../components/ConfirmDeleteDialog";

const PROJECTS_PER_PAGE = 9;

export default function ProjectsList() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get("status") || "all";

  const { data: projects, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: projectsApi.list,
  });

  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);

  const deleteMutation = useMutation({
    mutationFn: projectsApi.remove,
    onSuccess: async () => {
      setDeleteTarget(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
        queryClient.invalidateQueries({ queryKey: ["project-memory-logs"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });

  const requestDelete = (project: Project) => {
    deleteMutation.reset();
    setDeleteTarget(project);
  };

  const cancelDelete = () => {
    if (deleteMutation.isPending) return;
    deleteMutation.reset();
    setDeleteTarget(null);
  };

  const setFilter = (status: string) => {
    const nextParams = new URLSearchParams(searchParams);
    if (status === "all") {
      nextParams.delete("status");
    } else {
      nextParams.set("status", status);
    }
    setSearchParams(nextParams);
    setPage(1);
  };

  const allProjects = projects || [];
  const activeCount = allProjects.filter((p) =>
    ["in_progress", "approved", "review"].includes(p.status)
  ).length;
  const completedCount = allProjects.filter((p) => p.status === "completed").length;
  const overdueCount = allProjects.filter((p) => p.status === "overdue").length;

  const filteredProjects = useMemo(() => {
    let list = allProjects;

    if (statusFilter === "active") {
      list = list.filter((p) =>
        ["in_progress", "approved", "review"].includes(p.status)
      );
    } else if (statusFilter === "completed") {
      list = list.filter((p) => p.status === "completed");
    } else if (statusFilter === "overdue") {
      list = list.filter((p) => p.status === "overdue");
    }

    const query = search.trim().toLowerCase();
    if (!query) return list;

    return list.filter((project) =>
      [project.name, project.status, project.priority, project.classification]
        .some((value) => String(value || "").toLowerCase().includes(query))
    );
  }, [allProjects, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredProjects.length / PROJECTS_PER_PAGE));
  const currentPage = Math.min(page, totalPages);
  const visibleProjects = filteredProjects.slice(
    (currentPage - 1) * PROJECTS_PER_PAGE,
    currentPage * PROJECTS_PER_PAGE
  );

  if (isLoading) return <div className="loading">Loading projects...</div>;

  return (
    <div className="page-shell projects-page">
      <div className="page-toolbar">
        <div>
          <span className="page-kicker">Project Portfolio</span>
          <h1 className="page-title">Project Directory</h1>
          <p>Monitor project delivery status, track active milestones, and manage project lifecycles.</p>
        </div>
        <Link to="/manager/projects/create" className="button btn-primary">
          <Plus size={17} />New Project
        </Link>
      </div>

      <div
        className="project-status-filter-tabs"
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 16,
          flexWrap: "wrap",
        }}
      >
        <button
          type="button"
          className={`filter-chip ${statusFilter === "all" ? "active" : ""}`}
          onClick={() => setFilter("all")}
          style={{
            padding: "6px 14px",
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 600,
            border: "1px solid",
            borderColor: statusFilter === "all" ? "var(--ink)" : "var(--line)",
            background: statusFilter === "all" ? "var(--ink)" : "var(--paper)",
            color: statusFilter === "all" ? "#fff" : "var(--ink)",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          All ({allProjects.length})
        </button>
        <button
          type="button"
          className={`filter-chip ${statusFilter === "active" ? "active" : ""}`}
          onClick={() => setFilter("active")}
          style={{
            padding: "6px 14px",
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 600,
            border: "1px solid",
            borderColor: statusFilter === "active" ? "#0284c7" : "var(--line)",
            background: statusFilter === "active" ? "#0284c7" : "var(--paper)",
            color: statusFilter === "active" ? "#fff" : "#0369a1",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          Active ({activeCount})
        </button>
        <button
          type="button"
          className={`filter-chip ${statusFilter === "completed" ? "active" : ""}`}
          onClick={() => setFilter("completed")}
          style={{
            padding: "6px 14px",
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 600,
            border: "1px solid",
            borderColor: statusFilter === "completed" ? "#16a34a" : "var(--line)",
            background: statusFilter === "completed" ? "#16a34a" : "var(--paper)",
            color: statusFilter === "completed" ? "#fff" : "#15803d",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          Completed ({completedCount})
        </button>
        <button
          type="button"
          className={`filter-chip ${statusFilter === "overdue" ? "active" : ""}`}
          onClick={() => setFilter("overdue")}
          style={{
            padding: "6px 14px",
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 600,
            border: "1px solid",
            borderColor: statusFilter === "overdue" ? "#e11d48" : "var(--line)",
            background: statusFilter === "overdue" ? "#e11d48" : "var(--paper)",
            color: statusFilter === "overdue" ? "#fff" : "#be123c",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          Overdue ({overdueCount})
        </button>
      </div>

      <div className="list-controls">
        <label className="project-search">
          <Search size={17} aria-hidden="true" />
          <input
            type="search"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder="Search projects"
            aria-label="Search projects"
          />
        </label>
        <span className="result-count">
          {filteredProjects.length} {filteredProjects.length === 1 ? "project" : "projects"}
        </span>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Classification</th>
              <th>Updated</th>
              <th className="table-action-heading">Actions</th>
            </tr>
          </thead>
          <tbody>
            {visibleProjects.map((p) => (
              <tr key={p.id}>
                <td>
                  <Link className="project-name-link" to={`/manager/projects/${p.id}`}>
                    {p.name}
                  </Link>
                </td>
                <td>
                  <span className={`status-pill status-${p.status}`}>
                    {p.status.replace(/_/g, " ")}
                  </span>
                </td>
                <td>
                  <span className={`badge badge-${p.priority}`}>{p.priority}</span>
                </td>
                <td>{p.classification}</td>
                <td>{new Date(p.updated_at).toLocaleDateString()}</td>
                <td className="table-action-cell">
                  <button
                    className="row-delete-button"
                    type="button"
                    onClick={() => requestDelete(p)}
                    aria-label={`Delete ${p.name}`}
                    title={`Delete ${p.name}`}
                  >
                    <Trash2 size={16} />
                    <span>Delete</span>
                  </button>
                </td>
              </tr>
            ))}
            {!visibleProjects.length && (
              <tr>
                <td colSpan={6} className="table-empty">
                  No projects match your {statusFilter !== "all" ? `${statusFilter} status filter or ` : ""}search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {filteredProjects.length > PROJECTS_PER_PAGE && (
          <div className="table-pagination">
            <span>
              Showing {(currentPage - 1) * PROJECTS_PER_PAGE + 1}–
              {Math.min(currentPage * PROJECTS_PER_PAGE, filteredProjects.length)} of{" "}
              {filteredProjects.length}
            </span>
            <div>
              <button
                className="pagination-button pagination-nav"
                onClick={() => setPage((value) => Math.max(1, value - 1))}
                disabled={currentPage === 1}
                aria-label="Previous page"
              >
                <ChevronLeft size={16} />Previous
              </button>
              {Array.from({ length: totalPages }, (_, index) => index + 1).map((pageNumber) => (
                <button
                  key={pageNumber}
                  className={`pagination-button pagination-number ${
                    currentPage === pageNumber ? "active" : ""
                  }`}
                  onClick={() => setPage(pageNumber)}
                  aria-label={`Page ${pageNumber}`}
                  aria-current={currentPage === pageNumber ? "page" : undefined}
                >
                  {pageNumber}
                </button>
              ))}
              <button
                className="pagination-button pagination-nav"
                onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
                disabled={currentPage === totalPages}
                aria-label="Next page"
              >
                Next<ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
      {deleteTarget && (
        <ConfirmDeleteDialog
          projectName={deleteTarget.name}
          context="project"
          isDeleting={deleteMutation.isPending}
          error={deleteMutation.error instanceof Error ? deleteMutation.error.message : undefined}
          onCancel={cancelDelete}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
        />
      )}
    </div>
  );
}
