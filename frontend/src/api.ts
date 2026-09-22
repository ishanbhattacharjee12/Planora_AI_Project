const API_BASE = "/api";

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = err.detail;
    let message = "Request failed";
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(", ");
    } else if (detail) {
      message = JSON.stringify(detail);
    } else if (response.statusText) {
      message = response.statusText;
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

function filenameFromDisposition(header: string | null, fallback: string): string {
  if (!header) return fallback;
  const match = /filename="?([^"]+)"?/i.exec(header);
  return match?.[1] || fallback;
}

export async function downloadFile(path: string, fallbackFilename: string): Promise<void> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { headers });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = err.detail;
    throw new Error(typeof detail === "string" ? detail : "Download failed");
  }

  const blob = await response.blob();
  const filename = filenameFromDisposition(response.headers.get("Content-Disposition"), fallbackFilename);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "admin" | "manager" | "employee";
  department_id: number | null;
  is_active: boolean;
  capacity_percent: number;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  idea: string;
  business_objective: string | null;
  frontend_technology: string | null;
  backend_technology: string | null;
  database_technology: string | null;
  known_technologies: string | null;
  organization: string | null;
  document_type: string;
  primary_users: string | null;
  how_to_read: string | null;
  status: string;
  priority: string;
  classification: string;
  current_version: number;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  name: string;
  idea: string;
  description?: string;
  business_objective?: string;
  project_type?: string;
  priority?: "low" | "medium" | "high" | "critical";
  expected_deadline?: string;
  classification?: "public" | "internal" | "confidential" | "highly_confidential";
  frontend_technology?: string;
  backend_technology?: string;
  database_technology?: string;
  business_constraints?: string;
  technical_constraints?: string;
  organization?: string;
  primary_users?: string;
}

export interface SimilarProject {
  project_id: number;
  project_name: string;
  snippet: string;
  summary: string;
  architecture: string;
  similarity: number;
  created_at: string;
}

export interface ProjectMemoryLog {
  id: number;
  project_id: number;
  project_name: string;
  snippet: string;
  summary: string;
  architecture: string;
  semantic_summary: string;
  index_status: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  project_id: number;
  task_id: string;
  name: string;
  description: string | null;
  priority: string;
  status: string;
  estimated_effort_days: number | null;
  required_skills: Record<string, string> | null;
  assignee_id: number | null;
  deadline: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisStep {
  id: number;
  step: string;
  payload: Record<string, unknown>;
  confidence: string | null;
  status: string;
  version_number: number;
}

export interface AnalysisTokenUsage {
  project_id: number;
  version_number: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  request_count: number;
  last_run_at: string | null;
}

export interface AnalyzeProjectResult {
  steps: AnalysisStep[];
  token_usage: AnalysisTokenUsage;
}

export interface DashboardStats {
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  pending_tasks: number;
  overdue_tasks: number;
  my_tasks: number;
}

export interface EmployeeRecommendation {
  employee_id: number;
  full_name: string;
  skill_match_percent: number;
  workload_percent: number;
  recommendation: string;
  skill_gaps: Array<{ skill: string; required_level: string; current_level: string }>;
  narrative: string | null;
}

export const authApi = {
  login: (email: string, password: string) =>
    api<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => api<User>("/auth/me"),
};

export const dashboardApi = {
  stats: () => api<DashboardStats>("/dashboard/stats"),
};

export const projectsApi = {
  list: () => api<Project[]>("/projects"),
  get: (id: number) => api<Project>(`/projects/${id}`),
  remove: (id: number) => api<void>(`/projects/${id}`, { method: "DELETE" }),
  create: (data: ProjectCreateInput) =>
    api<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Project>) =>
    api<Project>(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  analyze: (id: number) =>
    api<AnalyzeProjectResult>(`/projects/${id}/analyze`, { method: "POST" }),
  getAnalysis: (id: number) => api<AnalysisStep[]>(`/projects/${id}/analysis`),
  getAnalysisUsage: (id: number, since?: string) => {
    const query = since ? `?since=${encodeURIComponent(since)}` : "";
    return api<AnalysisTokenUsage>(`/projects/${id}/analysis/usage${query}`);
  },
  downloadAnalysisPdf: (id: number, fallbackFilename = "project-analysis.pdf") =>
    downloadFile(`/projects/${id}/analysis/pdf`, fallbackFilename),
  updateAnalysis: (id: number, step: string, payload: Record<string, unknown>) =>
    api<AnalysisStep>(`/projects/${id}/analysis`, {
      method: "PATCH",
      body: JSON.stringify({ step, payload }),
    }),
  approve: (id: number) => api<Project>(`/projects/${id}/approve`, { method: "POST" }),
  generateTasks: (id: number) =>
    api<{ created: number }>(`/projects/${id}/generate-tasks`, { method: "POST" }),
  versions: (id: number) => api<Array<{ id: number; version_number: number; change_summary: string | null; created_at: string }>>(`/projects/${id}/versions`),
};

export const logsApi = {
  list: () => api<ProjectMemoryLog[]>("/logs"),
  removeProject: (projectId: number) => api<void>(`/projects/${projectId}`, { method: "DELETE" }),
  findSimilar: (data: ProjectCreateInput) =>
    api<SimilarProject[]>("/logs/similar", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const tasksApi = {
  byProject: (projectId: number) => api<Task[]>(`/tasks/project/${projectId}`),
  my: () => api<Task[]>("/tasks/my"),
  update: (id: number, data: Partial<Task>) =>
    api<Task>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  assign: (id: number, assigneeId: number) =>
    api<Task>(`/tasks/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ assignee_id: assigneeId }),
    }),
};

export const employeesApi = {
  list: () => api<User[]>("/employees"),
  recommendations: (taskId: number) => api<EmployeeRecommendation[]>(`/employees/tasks/${taskId}/recommendations`),
  workload: (id: number) => api<{ workload_percent: number; active_tasks: number }>(`/employees/${id}/workload`),
};

export const assistantApi = {
  chat: (projectId: number, message: string) =>
    api<{ id: number; role: string; content: string; created_at: string }>(
      `/projects/${projectId}/assistant/chat`,
      { method: "POST", body: JSON.stringify({ message }) }
    ),
  messages: (projectId: number) =>
    api<Array<{ id: number; role: string; content: string; created_at: string }>>(
      `/projects/${projectId}/assistant/messages`
    ),
};

export const adminApi = {
  auditLogs: () => api<Array<{ id: number; action: string; user_id: number | null; created_at: string; resource_type: string | null }>>("/admin/audit-logs"),
};
