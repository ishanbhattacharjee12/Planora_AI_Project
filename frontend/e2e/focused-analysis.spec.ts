import { expect, test } from "@playwright/test";

const user = {
  id: 1,
  email: "manager1@planora.local",
  full_name: "Morgan Lee",
  role: "manager",
  department_id: 1,
  is_active: true,
  capacity_percent: 100,
};

const project = {
  id: 15,
  name: "Study Planner",
  idea: "Create an end-to-end study planner",
  description: "A focused planning workspace",
  business_objective: "Improve planning consistency",
  frontend_technology: "react",
  backend_technology: "python_fastapi",
  database_technology: "mysql",
  known_technologies: null,
  organization: "University",
  document_type: "Functional Documentation",
  primary_users: "Engineering students",
  how_to_read: null,
  status: "review",
  priority: "medium",
  classification: "internal",
  current_version: 1,
  created_by_id: 1,
  created_at: "2026-09-18T09:00:00Z",
  updated_at: "2026-09-18T09:00:00Z",
};

const analysis = [
  { id: 1, step: "product_blueprint", confidence: "high", status: "draft", version_number: 1, payload: { overview: "A focused workspace for students to organize courses and study plans.", problem_statement: "Study work is fragmented across tools.", business_objectives: ["Improve planning consistency"], primary_users: [{ role: "Student", need: "Plan study time" }], scope_in: ["Course planning"], scope_out: ["University administration"], user_journeys: [{ journey: "Plan week", outcome: "Prioritized schedule" }], functional: [{ req_id: "FR-1", description: "Create a weekly plan", priority: "high", acceptance_criteria: ["Plan is saved"] }], non_functional: [{ req_id: "NFR-1", description: "Responsive interface", priority: "medium", acceptance_criteria: ["Works on mobile"] }], success_metrics: [{ kpi: "Plan completion", definition: "Completed plans", target: "80%", data_source: "Application events" }], assumptions: ["Students have accounts"] } },
  { id: 2, step: "solution_architecture", confidence: "high", status: "draft", version_number: 1, payload: { overview: "A modular web application.", architecture_style: "Modular monolith", components: [{ name: "Planner", responsibility: "Schedules" }], stack: [{ category: "Frontend", name: "React", rationale: "Selected stack" }], entities: [{ Student: "id, name, email" }, { Course: "id, code, title" }, { Plan: "id, student_id, week" }, { StudyBlock: "id, plan_id, start_time" }], relationships: [{ from: "Plan", to: "Course", relation: "belongs to" }], api_integrations: [], security_controls: ["Role-based access"], quality_attributes: [{ attribute: "Performance", target: "Fast interactions" }], deployment_topology: ["Web client and API"] } },
  { id: 3, step: "delivery_plan", confidence: "medium", status: "draft", version_number: 1, payload: { overview: "Deliver the core planning loop first.", phases: [{ phase: "Foundation", outcome: "Working application shell" }], milestones: [{ milestone: "Planner MVP", exit_criteria: "Core journey passes" }], tasks: [{ task_id: "T-1", name: "Build planner", description: "Implement weekly planning", priority: "high", estimated_effort_days: 4, difficulty: "medium", required_skills: { React: "advanced" }, dependencies: [], acceptance_criteria: ["Journey passes"] }], dependencies: [{ item: "Authentication", dependency: "User model" }], risks: [{ risk: "Scope growth", mitigation: "Protect MVP boundary" }], estimates: [{ phase: "MVP", duration: "2 weeks" }] } },
  { id: 4, step: "team_operations", confidence: "medium", status: "draft", version_number: 1, payload: { overview: "A compact cross-functional team.", delivery_roles: [{ role: "Full-stack engineer", responsibility: "Build product" }], required_skills: [{ skill: "React", required_level: "advanced", importance: "high" }], team_structure: [{ unit: "Product team", purpose: "Own delivery" }], ways_of_working: ["Weekly planning"], quality_strategy: ["Automated tests"], environments: [{ environment: "Staging", purpose: "Validation" }], observability: ["Error monitoring"], governance: ["Release review"] } },
  { id: 5, step: "launch_growth", confidence: "medium", status: "draft", version_number: 1, payload: { overview: "Pilot with a small student cohort.", launch_checklist: ["Complete accessibility review"], success_metrics: [{ kpi: "Weekly active plans", definition: "Plans updated weekly", target: "70%", data_source: "Events" }], analytics_reports: [{ report: "Engagement", audience: "Product team" }], future_enhancements: [{ enhancement: "Smart reminders", priority: "next" }], first_deliverables: ["Planner MVP"], recommended_next_decision: "Approve the MVP scope.", frontend_development_prompt: { framework: "React" }, backend_development_prompt: "Build the FastAPI modules." } },
];

test.beforeEach(async ({ page }) => {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/me") return route.fulfill({ json: user });
    if (path === "/api/projects/15") return route.fulfill({ json: project });
    if (path === "/api/projects/15/analysis") return route.fulfill({ json: analysis });
    if (path === "/api/projects/15/analysis/usage") return route.fulfill({ json: { project_id: 15, version_number: 1, input_tokens: 4300, output_tokens: 6200, total_tokens: 10500, request_count: 5, last_run_at: "2026-09-18T09:00:00Z" } });
    if (path === "/api/tasks/project/15") return route.fulfill({ json: [] });
    if (path === "/api/logs") return route.fulfill({ json: [
      { id: 1, project_id: 15, project_name: "Study Planner", snippet: "Weekly course planning for engineering students", summary: "A responsive student planning workspace with schedules and progress tracking.", architecture: "Frontend: React | Backend: FastAPI | Database: MySQL", semantic_summary: "Study planning", index_status: "indexed", created_at: "2026-09-18T09:00:00Z", updated_at: "2026-09-18T09:00:00Z" },
      { id: 2, project_id: 16, project_name: "Inventory Hub", snippet: "Inventory visibility and low stock alerts", summary: "Tracks inventory and operational alerts.", architecture: "Frontend: React | Backend: FastAPI | Database: PostgreSQL", semantic_summary: "Inventory", index_status: "indexed", created_at: "2026-09-18T09:00:00Z", updated_at: "2026-09-18T09:00:00Z" },
    ] });
    return route.fulfill({ json: [] });
  });
  await page.addInitScript((storedUser) => {
    localStorage.setItem("access_token", "visual-test-token");
    localStorage.setItem("user", JSON.stringify(storedUser));
  }, user);
});

test("five-section analysis uses the full workspace", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/manager/projects/15");
  await page.getByRole("button", { name: "Analysis", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Five decisions. One build-ready plan." })).toBeVisible();
  await expect(page.locator(".analysis-nav-card")).toHaveCount(5);
  await expect(page.getByRole("heading", { name: "1. Product Blueprint" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "5. Launch & Growth" })).toHaveCount(0);
  await page.locator(".analysis-nav-card").filter({ hasText: "Solution Architecture" }).click();
  await expect(page.locator(".analysis-sparse-grid")).toBeVisible();
  await expect(page.locator(".analysis-data-card")).toHaveCount(4);
  await expect(page.getByText("Student", { exact: true })).toBeVisible();
  await page.locator(".analysis-nav-card").filter({ hasText: "Launch & Growth" }).click();
  await expect(page.getByRole("heading", { name: "5. Launch & Growth" })).toBeVisible();
  await expect(page.getByText("5 / 5")).toBeVisible();
  await expect(page.getByRole("button", { name: /Next/ })).toBeDisabled();
  await expect(page.getByText("10,500")).toBeVisible();
  await expect(page).toHaveTitle(/Planora AI/);
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute("href", "/planora-icon.svg");
  const hasHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(hasHorizontalOverflow).toBe(false);
});

test("project logs stay compact until details are requested", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/manager/logs");
  await expect(page.locator(".memory-card-compact")).toHaveCount(2);
  await expect(page.locator(".memory-details").first()).not.toHaveAttribute("open", "");
  await expect(page.locator(".memory-keywords").first().getByText("React")).toBeVisible();
  await page.locator(".memory-details summary").first().click();
  await expect(page.locator(".memory-details-content").first()).toBeVisible();
  const hasHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(hasHorizontalOverflow).toBe(false);
});

test("new project form is guided and responsive", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/manager/projects/create");
  await expect(page.getByRole("heading", { name: "Turn the idea into a build-ready brief." })).toBeVisible();
  await expect(page.getByText("What AI will produce")).toBeVisible();
  await expect(page.locator(".analysis-output-list li")).toHaveCount(5);
  await page.getByLabel("Project name").fill("Study Planner");
  await page.getByLabel("Project idea").fill("Help students organize courses and weekly study tasks.");
  await expect(page.locator(".brief-score-row")).toContainText("25%context supplied");
  const hasHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(hasHorizontalOverflow).toBe(false);
});
