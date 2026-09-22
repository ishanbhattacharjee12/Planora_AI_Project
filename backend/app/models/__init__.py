import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Use JSON for cross-database compatibility (PostgreSQL JSONB in production via migration)
JsonType = JSON


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class ClassificationLevel(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    REVIEW = "review"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AnalysisStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="department")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    capacity_percent: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    department: Mapped[Department | None] = relationship(back_populates="users")
    employee_skills: Mapped[list["EmployeeSkill"]] = relationship(back_populates="user")
    project_memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user")
    assigned_tasks: Mapped[list["Task"]] = relationship(back_populates="assignee")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    employee_skills: Mapped[list["EmployeeSkill"]] = relationship(back_populates="skill")


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    level: Mapped[SkillLevel] = mapped_column(Enum(SkillLevel), default=SkillLevel.INTERMEDIATE)
    years_experience: Mapped[float | None] = mapped_column(Float)
    certifications: Mapped[str | None] = mapped_column(Text)
    manager_rating: Mapped[float | None] = mapped_column(Float)
    self_assessment: Mapped[SkillLevel | None] = mapped_column(Enum(SkillLevel))
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="employee_skills")
    skill: Mapped[Skill] = relationship(back_populates="employee_skills")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    idea: Mapped[str] = mapped_column(Text, nullable=False)
    business_objective: Mapped[str | None] = mapped_column(Text)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    project_type: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    expected_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    classification: Mapped[ClassificationLevel] = mapped_column(
        Enum(ClassificationLevel), default=ClassificationLevel.INTERNAL
    )
    known_technologies: Mapped[str | None] = mapped_column(Text)
    frontend_technology: Mapped[str | None] = mapped_column(String(100))
    backend_technology: Mapped[str | None] = mapped_column(String(100))
    database_technology: Mapped[str | None] = mapped_column(String(100))
    business_constraints: Mapped[str | None] = mapped_column(Text)
    technical_constraints: Mapped[str | None] = mapped_column(Text)
    organization: Mapped[str | None] = mapped_column(String(200))
    document_type: Mapped[str] = mapped_column(String(100), default="Functional Documentation")
    primary_users: Mapped[str | None] = mapped_column(Text)
    how_to_read: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    creator: Mapped[User] = relationship(foreign_keys=[created_by_id])
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project")
    analyses: Mapped[list["ProjectAnalysis"]] = relationship(back_populates="project")
    requirements: Mapped[list["Requirement"]] = relationship(back_populates="project")
    technologies: Mapped[list["Technology"]] = relationship(back_populates="project")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")
    versions: Mapped[list["ProjectVersion"]] = relationship(back_populates="project")
    documents: Mapped[list["Document"]] = relationship(back_populates="project")
    memory_log: Mapped["ProjectMemoryLog | None"] = relationship(
        back_populates="project", uselist=False
    )


class ProjectMemoryLog(Base):
    __tablename__ = "project_memory_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False, unique=True, index=True
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    snippet: Mapped[str] = mapped_column(String(320), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    architecture: Mapped[str] = mapped_column(Text, nullable=False)
    semantic_summary: Mapped[str] = mapped_column(Text, nullable=False)
    chroma_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    index_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    index_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="memory_log")
    owner: Mapped[User] = relationship(foreign_keys=[owner_id])


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member")

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="project_memberships")


class ProjectVersion(Base):
    __tablename__ = "project_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JsonType, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="versions")


class ProjectAnalysis(Base):
    __tablename__ = "project_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    step: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JsonType, nullable=False)
    confidence: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[AnalysisStatus] = mapped_column(Enum(AnalysisStatus), default=AnalysisStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="analyses")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    req_id: Mapped[str] = mapped_column(String(20), nullable=False)
    req_type: Mapped[str] = mapped_column(String(20), default="functional")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    dependencies: Mapped[str | None] = mapped_column(Text)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text)
    version_number: Mapped[int] = mapped_column(Integer, default=1)

    project: Mapped[Project] = relationship(back_populates="requirements")


class Technology(Base):
    __tablename__ = "technologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    alternatives: Mapped[dict | None] = mapped_column(JsonType)
    version_number: Mapped[int] = mapped_column(Integer, default=1)

    project: Mapped[Project] = relationship(back_populates="technologies")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    estimated_effort_days: Mapped[float | None] = mapped_column(Float)
    difficulty: Mapped[str | None] = mapped_column(String(50))
    required_skills: Mapped[dict | None] = mapped_column(JsonType)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="tasks")
    assignee: Mapped[User | None] = relationship(back_populates="assigned_tasks")
  # dependencies where this task is the dependent
    dependencies: Mapped[list["TaskDependency"]] = relationship(
        foreign_keys="TaskDependency.task_id", back_populates="task"
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dep"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    depends_on_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)

    task: Mapped[Task] = relationship(foreign_keys=[task_id], back_populates="dependencies")
    depends_on: Mapped[Task] = relationship(foreign_keys=[depends_on_task_id])


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    classification: Mapped[ClassificationLevel] = mapped_column(
        Enum(ClassificationLevel), default=ClassificationLevel.INTERNAL
    )
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_company_wide: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project | None] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JsonType)

    document: Mapped[Document] = relationship(back_populates="chunks")


class AIRequest(Base):
    __tablename__ = "ai_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    request_type: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    response: Mapped["AIResponse | None"] = relationship(back_populates="request", uselist=False)


class AIResponse(Base):
    __tablename__ = "ai_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("ai_requests.id"), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JsonType)

    request: Mapped[AIRequest] = relationship(back_populates="response")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict | None] = mapped_column(JsonType)
    ip_address: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrchestrationRun(Base):
    __tablename__ = "orchestration_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), default="workflow")
    status: Mapped[str] = mapped_column(String(50), default="running")
    state_json: Mapped[dict | None] = mapped_column(JsonType)
    current_step: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
