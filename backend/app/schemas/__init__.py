from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import (
    AnalysisStatus,
    ClassificationLevel,
    ProjectStatus,
    SkillLevel,
    TaskPriority,
    TaskStatus,
    UserRole,
)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    department_id: int | None
    is_active: bool
    capacity_percent: int

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.EMPLOYEE
    department_id: int | None = None


class ProjectCreate(BaseModel):
    name: str
    idea: str
    description: str | None = None
    business_objective: str | None = None
    department_id: int | None = None
    project_type: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    expected_deadline: datetime | None = None
    classification: ClassificationLevel = ClassificationLevel.INTERNAL
    frontend_technology: str | None = None
    backend_technology: str | None = None
    database_technology: str | None = None
    known_technologies: str | None = None
    business_constraints: str | None = None
    technical_constraints: str | None = None
    organization: str | None = None
    document_type: str = "Functional Documentation"
    primary_users: str | None = None
    how_to_read: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    idea: str | None = None
    business_objective: str | None = None
    status: ProjectStatus | None = None
    priority: TaskPriority | None = None
    frontend_technology: str | None = None
    backend_technology: str | None = None
    database_technology: str | None = None
    known_technologies: str | None = None
    organization: str | None = None
    document_type: str | None = None
    primary_users: str | None = None
    how_to_read: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    idea: str
    business_objective: str | None
    frontend_technology: str | None
    backend_technology: str | None
    database_technology: str | None
    known_technologies: str | None
    organization: str | None
    document_type: str
    primary_users: str | None
    how_to_read: str | None
    status: ProjectStatus
    priority: TaskPriority
    classification: ClassificationLevel
    current_version: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectSimilarityRequest(BaseModel):
    name: str
    idea: str
    description: str | None = None
    business_objective: str | None = None
    project_type: str | None = None
    primary_users: str | None = None
    frontend_technology: str | None = None
    backend_technology: str | None = None
    database_technology: str | None = None


class SimilarProjectResponse(BaseModel):
    project_id: int
    project_name: str
    snippet: str
    summary: str
    architecture: str
    similarity: float
    created_at: datetime


class ProjectMemoryLogResponse(BaseModel):
    id: int
    project_id: int
    project_name: str
    snippet: str
    summary: str
    architecture: str
    semantic_summary: str
    index_status: str
    created_at: datetime
    updated_at: datetime


class AnalysisStepResponse(BaseModel):
    id: int
    step: str
    payload: dict[str, Any]
    confidence: str | None
    status: AnalysisStatus
    version_number: int

    model_config = {"from_attributes": True}


class AnalysisTokenUsageResponse(BaseModel):
    project_id: int
    version_number: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int
    last_run_at: str | None = None


class AnalyzeProjectResponse(BaseModel):
    steps: list[AnalysisStepResponse]
    token_usage: AnalysisTokenUsageResponse


class AnalysisUpdate(BaseModel):
    step: str
    payload: dict[str, Any]


class RequirementResponse(BaseModel):
    id: int
    req_id: str
    req_type: str
    description: str
    priority: TaskPriority
    acceptance_criteria: str | None

    model_config = {"from_attributes": True}


class TechnologyResponse(BaseModel):
    id: int
    category: str
    name: str
    rationale: str | None
    alternatives: dict | None

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_effort_days: float | None = None
    required_skills: dict | None = None
    acceptance_criteria: str | None = None
    deadline: datetime | None = None


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = None
    deadline: datetime | None = None


class TaskResponse(BaseModel):
    id: int
    project_id: int
    task_id: str
    name: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    estimated_effort_days: float | None
    required_skills: dict | None
    assignee_id: int | None
    deadline: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskAssignRequest(BaseModel):
    assignee_id: int
    deadline: datetime | None = None


class EmployeeSkillResponse(BaseModel):
    skill_id: int
    skill_name: str
    level: SkillLevel
    years_experience: float | None

    model_config = {"from_attributes": True}


class EmployeeResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    department_id: int | None
    capacity_percent: int
    skills: list[EmployeeSkillResponse] = []

    model_config = {"from_attributes": True}


class WorkloadResponse(BaseModel):
    employee_id: int
    full_name: str
    active_tasks: int
    total_effort_days: float
    workload_percent: float
    capacity_percent: int


class EmployeeRecommendation(BaseModel):
    employee_id: int
    full_name: str
    skill_match_percent: float
    workload_percent: float
    recommendation: str
    skill_gaps: list[dict[str, str]] = []
    narrative: str | None = None


class SkillGapResponse(BaseModel):
    skill_name: str
    required_level: str
    current_level: str | None
    gap: bool


class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    project_id: int | None
    classification: ClassificationLevel
    is_company_wide: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AssistantChatRequest(BaseModel):
    message: str


class AssistantMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    resource_type: str | None
    resource_id: int | None
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    my_tasks: int = 0


class ProjectVersionResponse(BaseModel):
    id: int
    version_number: int
    change_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VersionDiffResponse(BaseModel):
    version_a: int
    version_b: int
    changes: dict[str, Any]
