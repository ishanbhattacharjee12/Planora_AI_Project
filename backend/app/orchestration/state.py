from pydantic import BaseModel, Field


class RequirementItem(BaseModel):
    req_id: str
    description: str
    priority: str = "medium"
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)


class TaskItem(BaseModel):
    task_id: str
    name: str
    description: str
    priority: str = "medium"
    estimated_effort_days: float
    difficulty: str = "medium"
    required_skills: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)


class StaffingSkillItem(BaseModel):
    skill: str
    required_level: str
    importance: str = "high"


class SuccessMeasureItem(BaseModel):
    kpi: str
    definition: str
    target: str
    data_source: str


class FrontendDevelopmentPrompt(BaseModel):
    product_context: str
    user_roles: list[str] = Field(default_factory=list, max_length=6)
    screens_routes: list[dict[str, str]] = Field(default_factory=list, max_length=10)
    components: list[dict[str, str]] = Field(default_factory=list, max_length=12)
    navigation: list[str] = Field(default_factory=list, max_length=8)
    state_and_data: list[str] = Field(default_factory=list, max_length=8)
    api_integrations: list[str] = Field(default_factory=list, max_length=10)
    validation: list[str] = Field(default_factory=list, max_length=8)
    accessibility: list[str] = Field(default_factory=list, max_length=8)
    responsive_behavior: list[str] = Field(default_factory=list, max_length=8)
    testing: list[str] = Field(default_factory=list, max_length=8)
    acceptance_criteria: list[str] = Field(default_factory=list, max_length=10)
    build_instructions: str


# Five focused outputs replace the former 17 overlapping report sections.
class ProductBlueprintOutput(BaseModel):
    overview: str
    problem_statement: str
    business_objectives: list[str] = Field(default_factory=list, max_length=5)
    primary_users: list[dict[str, str]] = Field(default_factory=list, max_length=4)
    scope_in: list[str] = Field(default_factory=list, max_length=6)
    scope_out: list[str] = Field(default_factory=list, max_length=5)
    user_journeys: list[dict[str, str]] = Field(default_factory=list, max_length=6)
    functional: list[RequirementItem] = Field(default_factory=list, max_length=8)
    non_functional: list[RequirementItem] = Field(default_factory=list, max_length=6)
    success_metrics: list[SuccessMeasureItem] = Field(default_factory=list, max_length=5)
    assumptions: list[str] = Field(default_factory=list, max_length=5)
    confidence: str = "medium"


class SolutionArchitectureOutput(BaseModel):
    overview: str
    architecture_style: str
    components: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    stack: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    entities: list[dict[str, str]] = Field(default_factory=list, max_length=10)
    relationships: list[dict[str, str]] = Field(default_factory=list, max_length=10)
    api_integrations: list[dict[str, str]] = Field(default_factory=list, max_length=6)
    security_controls: list[str] = Field(default_factory=list, max_length=8)
    quality_attributes: list[dict[str, str]] = Field(default_factory=list, max_length=6)
    deployment_topology: list[str] = Field(default_factory=list, max_length=5)
    confidence: str = "medium"


class DeliveryPlanOutput(BaseModel):
    overview: str
    phases: list[dict[str, str]] = Field(default_factory=list, max_length=5)
    milestones: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    tasks: list[TaskItem] = Field(default_factory=list, max_length=12)
    dependencies: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    risks: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    estimates: list[dict[str, str]] = Field(default_factory=list, max_length=5)
    confidence: str = "medium"


class TeamOperationsOutput(BaseModel):
    overview: str
    delivery_roles: list[dict[str, str]] = Field(default_factory=list, max_length=8)
    required_skills: list[StaffingSkillItem] = Field(default_factory=list, max_length=10)
    team_structure: list[dict[str, str]] = Field(default_factory=list, max_length=6)
    ways_of_working: list[str] = Field(default_factory=list, max_length=8)
    quality_strategy: list[str] = Field(default_factory=list, max_length=8)
    environments: list[dict[str, str]] = Field(default_factory=list, max_length=4)
    observability: list[str] = Field(default_factory=list, max_length=8)
    governance: list[str] = Field(default_factory=list, max_length=8)
    confidence: str = "medium"


class LaunchGrowthOutput(BaseModel):
    overview: str
    launch_checklist: list[str] = Field(default_factory=list, max_length=8)
    success_metrics: list[SuccessMeasureItem] = Field(default_factory=list, max_length=5)
    analytics_reports: list[dict[str, str]] = Field(default_factory=list, max_length=6)
    future_enhancements: list[dict[str, str]] = Field(default_factory=list, max_length=6)
    first_deliverables: list[str] = Field(default_factory=list, max_length=5)
    recommended_next_decision: str
    frontend_development_prompt: FrontendDevelopmentPrompt
    backend_development_prompt: str = Field(max_length=6000)
    confidence: str = "medium"


WORKFLOW_STEPS: list[tuple[str, type[BaseModel], str]] = [
    (
        "product_blueprint",
        ProductBlueprintOutput,
        "Create a concise product blueprint for THIS application. Define the problem, measurable business "
        "objectives, users, boundaries, essential journeys, functional and non-functional requirements, "
        "success metrics, and explicit assumptions. Include only details that affect implementation.",
    ),
    (
        "solution_architecture",
        SolutionArchitectureOutput,
        "Design the solution architecture for THIS application. Cover architecture style, components, selected "
        "technology stack with rationale, data entities and relationships, integrations, security controls, "
        "quality attributes, and deployment topology. Use the user's selected stack as the primary stack.",
    ),
    (
        "delivery_plan",
        DeliveryPlanOutput,
        "Create an actionable delivery plan for THIS application. Include phases, milestones, implementation "
        "tasks, dependencies, risks with mitigations, and realistic estimates. Tasks must include task_id, name, "
        "description, priority, estimated_effort_days, difficulty, required_skills, dependencies, and acceptance criteria.",
    ),
    (
        "team_operations",
        TeamOperationsOutput,
        "Define the lean team and operating model needed to deliver THIS application. Include delivery roles, "
        "required skills and levels, team structure, ways of working, quality strategy, environments, observability, "
        "and governance. Keep recommendations proportional to the project scope.",
    ),
    (
        "launch_growth",
        LaunchGrowthOutput,
        "Create the launch, measurement, and growth plan for THIS application. Include a launch checklist, "
        "success metrics, analytics/reporting needs, prioritized future enhancements, first deliverables, and "
        "the recommended next decision. Then create an implementation handoff using the previous four sections. "
        "Include two artifacts: (1) frontend_development_prompt, a valid JSON object containing product context, "
        "roles, screens/routes, components, navigation, state/data needs, API needs, validation, accessibility, "
        "responsive behavior, tests, acceptance criteria, and instructions for a frontend-building LLM; and "
        "(2) backend_development_prompt, a detailed standalone prompt covering architecture, modules, data model, "
        "API endpoints, authorization, AI/RAG needs, validation, security, background work, tests, deployment, and "
        "acceptance criteria. Keep each handoff compact (roughly 1,200 words or less), project-specific, reuse the "
        "selected stack, avoid repetition, and invent no facts.",
    ),
]

STEP_SCHEMAS: dict[str, type[BaseModel]] = {name: schema for name, schema, _ in WORKFLOW_STEPS}
STEP_ORDER: list[str] = [name for name, _, _ in WORKFLOW_STEPS]
