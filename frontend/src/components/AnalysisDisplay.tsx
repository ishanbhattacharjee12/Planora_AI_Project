import { ReactNode, useEffect, useRef, useState } from "react";
import { AnalysisStep } from "../api";

export const ANALYSIS_STEP_ORDER = [
  "product_blueprint",
  "solution_architecture",
  "delivery_plan",
  "team_operations",
  "launch_growth",
  // Legacy sections remain renderable for existing project versions.
  "executive_dashboard",
  "projects",
  "resources",
  "staffing",
  "people_development",
  "business",
  "analytics",
  "reports",
  "administration",
  "quick_links",
  "cross_module_workflows",
  "data_structure",
  "implementation_approach",
  "success_measures",
  "challenges",
  "future_enhancements",
  "closing_note",
] as const;

const STEP_LABELS: Record<string, string> = {
  product_blueprint: "1. Product Blueprint",
  solution_architecture: "2. Solution Architecture",
  delivery_plan: "3. Delivery Plan",
  team_operations: "4. Team & Operations",
  launch_growth: "5. Launch & Growth",
  executive_dashboard: "1. Executive Dashboard",
  projects: "2. Projects",
  resources: "3. Resources",
  staffing: "4. Staffing",
  people_development: "5. People Development",
  business: "6. Business",
  analytics: "7. Analytics",
  reports: "8. Reports",
  administration: "9. Administration",
  quick_links: "10. Quick Links",
  cross_module_workflows: "11. Cross-module Workflows",
  data_structure: "12. High-Level Data Structure",
  implementation_approach: "13. Suggested Implementation Approach",
  success_measures: "14. Key Success Measures",
  challenges: "15. Challenges & Considerations",
  future_enhancements: "16. Future Enhancements",
  closing_note: "17. Closing Note",
};

const STEP_PURPOSES: Record<string, string> = {
  product_blueprint: "Problem, outcomes, users, scope, journeys, and requirements",
  solution_architecture: "System design, data, integrations, security, and deployment",
  delivery_plan: "Phases, milestones, tasks, dependencies, estimates, and risks",
  team_operations: "Roles, skills, quality practices, environments, and governance",
  launch_growth: "Launch readiness, measurement, roadmap, and implementation handoff",
};

function titleCase(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value ?? "");
  }
}

function confidenceBadge(confidence?: string | null) {
  if (!confidence) return null;
  const level = confidence.toLowerCase();
  const cls =
    level === "high" ? "badge-high" : level === "low" ? "badge-low" : "badge-medium";
  return <span className={`badge ${cls}`}>{confidence} confidence</span>;
}

function priorityBadge(priority?: string) {
  if (!priority) return null;
  const level = priority.toLowerCase();
  const cls =
    level === "high" || level === "critical"
      ? "badge-high"
      : level === "low"
        ? "badge-low"
        : "badge-medium";
  return <span className={`badge ${cls}`}>{priority}</span>;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="analysis-section">
      <h4>{title}</h4>
      {children}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  if (!items?.length) return <p className="analysis-muted">None listed.</p>;
  return (
    <ul className="analysis-list">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function KpiCards({ cards }: { cards: Array<Record<string, unknown>> }) {
  if (!cards?.length) return <p className="analysis-muted">None listed.</p>;
  return (
    <div className="stats-grid">
      {cards.map((card, i) => (
        <div key={i} className="stat-card">
          <div className="label">{String(card.name || card.title || `KPI ${i + 1}`)}</div>
          <div className="value" style={{ fontSize: 18 }}>
            {String(card.metric || card.value || "—")}
          </div>
          {card.description != null && String(card.description) !== "" && (
            <p className="analysis-muted" style={{ marginTop: 8, fontSize: 13 }}>
              {String(card.description)}
            </p>
          )}
          {card.target != null && String(card.target) !== "" && (
            <p className="analysis-muted" style={{ fontSize: 12 }}>
              Target: {String(card.target)}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function DictTable({ items, title }: { items: Array<Record<string, unknown>>; title?: string }) {
  if (!items?.length) return <p className="analysis-muted">None listed.</p>;
  const keys = Array.from(new Set(items.flatMap((row) => Object.keys(row))));
  const meaningfulEntries = (row: Record<string, unknown>) => Object.entries(row).filter(([, value]) => value != null && value !== "" && value !== "—");
  const averagePopulatedCells = items.reduce((total, row) => total + meaningfulEntries(row).length, 0) / items.length;
  const isSparseMatrix = keys.length >= 4 && averagePopulatedCells <= 2;

  if (isSparseMatrix) {
    return (
      <div className="analysis-sparse-grid">
        {items.map((row, index) => {
          const entries = meaningfulEntries(row);
          const primary = entries[0];
          return (
            <article className="analysis-data-card" key={index}>
              <div className="analysis-data-card-index">{String(index + 1).padStart(2, "0")}</div>
              {primary ? (
                <div className="analysis-data-card-content">
                  <strong>{titleCase(primary[0])}</strong>
                  <p>{String(primary[1])}</p>
                  {entries.slice(1).map(([key, value]) => (
                    <small key={key}><b>{titleCase(key)}:</b> {String(value)}</small>
                  ))}
                </div>
              ) : <p className="analysis-muted">No details listed.</p>}
            </article>
          );
        })}
      </div>
    );
  }

  return (
    <div className="analysis-table-scroll">
    <table className="table analysis-table">
      {title && (
        <caption style={{ captionSide: "top", textAlign: "left", marginBottom: 8 }}>
          {title}
        </caption>
      )}
      <thead>
        <tr>
          {keys.map((k) => (
            <th key={k}>{titleCase(k)}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {items.map((row, i) => (
          <tr key={i}>
            {keys.map((k) => (
              <td key={k}>{String(row[k] ?? "—")}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  );
}

function DictCards({ items }: { items: Array<Record<string, unknown>> }) {
  if (!items?.length) return <p className="analysis-muted">None listed.</p>;
  return (
    <div className="analysis-cards">
      {items.map((item, i) => (
        <div key={i} className="analysis-item-card">
          {Object.entries(item).map(([k, v]) => (
            <p key={k}>
              <span className="analysis-kv-label">{titleCase(k)}:</span> {String(v)}
            </p>
          ))}
        </div>
      ))}
    </div>
  );
}

function RequirementCards({ items, label }: { items: Array<Record<string, unknown>>; label: string }) {
  if (!items?.length) return null;
  return (
    <Section title={`${label} (${items.length})`}>
      <div className="analysis-cards">
        {items.map((req) => (
          <div key={String(req.req_id)} className="analysis-item-card">
            <div className="analysis-item-header">
              <strong>{String(req.req_id)}</strong>
              {priorityBadge(String(req.priority))}
            </div>
            <p>{String(req.description)}</p>
            {(req.acceptance_criteria as string[])?.length > 0 && (
              <>
                <p className="analysis-subtitle">Acceptance criteria</p>
                <BulletList items={req.acceptance_criteria as string[]} />
              </>
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}

function ImplementationTasks({ tasks }: { tasks: Array<Record<string, unknown>> }) {
  if (!tasks?.length) return <p className="analysis-muted">None listed.</p>;
  return (
    <div className="analysis-cards">
      {tasks.map((t) => (
        <div key={String(t.task_id)} className="analysis-item-card">
          <div className="analysis-item-header">
            <strong>
              {String(t.task_id)} — {String(t.name)}
            </strong>
            {priorityBadge(String(t.priority))}
          </div>
          <p className="analysis-text">{String(t.description)}</p>
          <div className="analysis-meta">
            <span>Effort: {String(t.estimated_effort_days)} days</span>
            <span>Difficulty: {String(t.difficulty)}</span>
          </div>
          {Object.keys((t.required_skills as object) || {}).length > 0 && (
            <p className="analysis-muted">
              Skills:{" "}
              {Object.entries((t.required_skills as Record<string, string>) || {})
                .map(([k, v]) => `${k} (${v})`)
                .join(", ")}
            </p>
          )}
          {(t.dependencies as string[])?.length > 0 && (
            <p className="analysis-muted">Depends on: {(t.dependencies as string[]).join(", ")}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function renderFieldValue(key: string, value: unknown): ReactNode {
  if (value == null || value === "") return <p className="analysis-muted">None listed.</p>;
  if (typeof value === "string") return <p className="analysis-text">{value}</p>;
  if (Array.isArray(value)) {
    if (value.length === 0) return <p className="analysis-muted">None listed.</p>;
    if (typeof value[0] === "string") return <BulletList items={value as string[]} />;
    if (typeof value[0] === "object") {
      if (key.includes("kpi") || key === "kpi_cards") return <KpiCards cards={value as Array<Record<string, unknown>>} />;
      if (key === "tasks") return <ImplementationTasks tasks={value as Array<Record<string, unknown>>} />;
      return <DictTable items={value as Array<Record<string, unknown>>} />;
    }
  }
  if (typeof value === "object") {
    return <pre className="json-view">{JSON.stringify(value, null, 2)}</pre>;
  }
  return <p className="analysis-text">{String(value)}</p>;
}

function renderGenericPayload(payload: Record<string, unknown>, skipKeys = new Set(["confidence"])) {
  const entries = Object.entries(payload).filter(([k]) => !skipKeys.has(k));
  if (!entries.length) return <p className="analysis-muted">No content.</p>;
  return (
    <>
      {entries.map(([key, value]) => (
        <Section key={key} title={titleCase(key)}>
          {renderFieldValue(key, value)}
        </Section>
      ))}
    </>
  );
}

function EmptyState({ step }: { step: string }) {
  return (
    <p className="analysis-muted">
      No {STEP_LABELS[step] || titleCase(step)} data yet. Run AI Analysis to generate.
    </p>
  );
}

function renderPayload(step: string, payload: Record<string, unknown>) {
  if (!payload || Object.keys(payload).length === 0) {
    return <EmptyState step={step} />;
  }

  switch (step) {
    case "product_blueprint":
      return (
        <>
          <div className="analysis-lead-grid">
            <Section title="Overview"><p className="analysis-text">{String(payload.overview || "")}</p></Section>
            <Section title="Problem to Solve"><p className="analysis-text">{String(payload.problem_statement || "")}</p></Section>
          </div>
          <div className="analysis-two-column">
            <Section title="Business Objectives"><BulletList items={(payload.business_objectives as string[]) || []} /></Section>
            <Section title="Primary Users"><DictCards items={(payload.primary_users as Array<Record<string, unknown>>) || []} /></Section>
            <Section title="In Scope"><BulletList items={(payload.scope_in as string[]) || []} /></Section>
            <Section title="Out of Scope"><BulletList items={(payload.scope_out as string[]) || []} /></Section>
          </div>
          <Section title="Key User Journeys"><DictTable items={(payload.user_journeys as Array<Record<string, unknown>>) || []} /></Section>
          <RequirementCards items={(payload.functional as Array<Record<string, unknown>>) || []} label="Functional Requirements" />
          <RequirementCards items={(payload.non_functional as Array<Record<string, unknown>>) || []} label="Non-Functional Requirements" />
          <Section title="Success Metrics"><DictTable items={(payload.success_metrics as Array<Record<string, unknown>>) || []} /></Section>
          <Section title="Assumptions"><BulletList items={(payload.assumptions as string[]) || []} /></Section>
        </>
      );

    case "solution_architecture":
      return (
        <>
          <div className="analysis-lead-grid">
            <Section title="Architecture Overview"><p className="analysis-text">{String(payload.overview || "")}</p></Section>
            <Section title="Architecture Style"><p className="analysis-text">{String(payload.architecture_style || "")}</p></Section>
          </div>
          <div className="analysis-two-column">
            <Section title="Components"><DictCards items={(payload.components as Array<Record<string, unknown>>) || []} /></Section>
            <Section title="Technology Stack"><DictCards items={(payload.stack as Array<Record<string, unknown>>) || []} /></Section>
          </div>
          <Section title="Core Data Entities"><DictTable items={(payload.entities as Array<Record<string, unknown>>) || []} /></Section>
          <Section title="Relationships"><DictTable items={(payload.relationships as Array<Record<string, unknown>>) || []} /></Section>
          <Section title="API & Integrations"><DictTable items={(payload.api_integrations as Array<Record<string, unknown>>) || []} /></Section>
          <div className="analysis-two-column">
            <Section title="Security Controls"><BulletList items={(payload.security_controls as string[]) || []} /></Section>
            <Section title="Deployment Topology"><BulletList items={(payload.deployment_topology as string[]) || []} /></Section>
          </div>
          <Section title="Quality Attributes"><DictTable items={(payload.quality_attributes as Array<Record<string, unknown>>) || []} /></Section>
        </>
      );

    case "delivery_plan":
      return (
        <>
          <Section title="Delivery Overview"><p className="analysis-text">{String(payload.overview || "")}</p></Section>
          <div className="analysis-two-column">
            <Section title="Phases"><DictCards items={(payload.phases as Array<Record<string, unknown>>) || []} /></Section>
            <Section title="Milestones"><DictCards items={(payload.milestones as Array<Record<string, unknown>>) || []} /></Section>
          </div>
          <Section title={`Implementation Tasks (${((payload.tasks as unknown[]) || []).length})`}>
            <ImplementationTasks tasks={(payload.tasks as Array<Record<string, unknown>>) || []} />
          </Section>
          <div className="analysis-two-column">
            <Section title="Dependencies"><DictTable items={(payload.dependencies as Array<Record<string, unknown>>) || []} /></Section>
            <Section title="Risks & Mitigations"><DictTable items={(payload.risks as Array<Record<string, unknown>>) || []} /></Section>
          </div>
          <Section title="Estimates"><DictTable items={(payload.estimates as Array<Record<string, unknown>>) || []} /></Section>
        </>
      );

    case "team_operations":
      return (
        <>
          <Section title="Operating Model"><p className="analysis-text">{String(payload.overview || "")}</p></Section>
          <div className="analysis-two-column">
            <Section title="Delivery Roles"><DictCards items={(payload.delivery_roles as Array<Record<string, unknown>>) || []} /></Section>
            <Section title="Required Skills"><DictTable items={(payload.required_skills as Array<Record<string, unknown>>) || []} /></Section>
          </div>
          <Section title="Team Structure"><DictTable items={(payload.team_structure as Array<Record<string, unknown>>) || []} /></Section>
          <div className="analysis-two-column">
            <Section title="Ways of Working"><BulletList items={(payload.ways_of_working as string[]) || []} /></Section>
            <Section title="Quality Strategy"><BulletList items={(payload.quality_strategy as string[]) || []} /></Section>
            <Section title="Observability"><BulletList items={(payload.observability as string[]) || []} /></Section>
            <Section title="Governance"><BulletList items={(payload.governance as string[]) || []} /></Section>
          </div>
          <Section title="Environments"><DictTable items={(payload.environments as Array<Record<string, unknown>>) || []} /></Section>
        </>
      );

    case "launch_growth":
      return (
        <>
          <Section title="Launch Overview"><p className="analysis-text">{String(payload.overview || "")}</p></Section>
          <div className="analysis-two-column">
            <Section title="Launch Checklist"><BulletList items={(payload.launch_checklist as string[]) || []} /></Section>
            <Section title="First Deliverables"><BulletList items={(payload.first_deliverables as string[]) || []} /></Section>
          </div>
          <Section title="Success Metrics"><DictTable items={(payload.success_metrics as Array<Record<string, unknown>>) || []} /></Section>
          <div className="analysis-two-column">
            <Section title="Analytics & Reports"><DictCards items={(payload.analytics_reports as Array<Record<string, unknown>>) || []} /></Section>
            <Section title="Future Enhancements"><DictCards items={(payload.future_enhancements as Array<Record<string, unknown>>) || []} /></Section>
          </div>
          <div className="analysis-decision-callout">
            <span>Recommended next decision</span>
            <strong>{String(payload.recommended_next_decision || "")}</strong>
          </div>
          {payload.frontend_development_prompt && (
            <Section title="Frontend Development Prompt (JSON)"><pre className="json-view">{prettyJson(payload.frontend_development_prompt)}</pre></Section>
          )}
          {payload.backend_development_prompt && (
            <Section title="Backend Development Prompt"><pre className="json-view">{String(payload.backend_development_prompt)}</pre></Section>
          )}
        </>
      );

    case "executive_dashboard":
      return (
        <>
          {payload.overview && (
            <Section title="Overview">
              <p className="analysis-text">{String(payload.overview)}</p>
            </Section>
          )}
          <Section title="KPI Cards">
            <KpiCards cards={(payload.kpi_cards as Array<Record<string, unknown>>) || []} />
          </Section>
          <Section title="Drill-downs">
            <BulletList items={(payload.drill_downs as string[]) || []} />
          </Section>
          <Section title="Filters">
            <BulletList items={(payload.filters as string[]) || []} />
          </Section>
          <Section title="Recommended Widgets">
            <BulletList items={(payload.recommended_widgets as string[]) || []} />
          </Section>
        </>
      );

    case "projects":
      return (
        <>
          {payload.overview && (
            <Section title="Overview">
              <p className="analysis-text">{String(payload.overview)}</p>
            </Section>
          )}
          <Section title="Project Master">
            <DictTable items={(payload.project_master as Array<Record<string, unknown>>) || []} />
          </Section>
          <Section title="Health / Schedule / Budget">
            <DictTable items={(payload.health_schedule_budget as Array<Record<string, unknown>>) || []} />
          </Section>
          <Section title="Milestones">
            <DictCards items={(payload.milestones as Array<Record<string, unknown>>) || []} />
          </Section>
          <Section title="Risks & Escalations">
            <DictCards items={(payload.risks_escalations as Array<Record<string, unknown>>) || []} />
          </Section>
          <Section title="Team & Skills">
            <DictTable items={(payload.team_and_skills as Array<Record<string, unknown>>) || []} />
          </Section>
          <Section title="Project Reports">
            <BulletList items={(payload.project_reports as string[]) || []} />
          </Section>
          <RequirementCards
            items={(payload.functional as Array<Record<string, unknown>>) || []}
            label="Functional Requirements"
          />
          <RequirementCards
            items={(payload.non_functional as Array<Record<string, unknown>>) || []}
            label="Non-Functional Requirements"
          />
          {(payload.stack as Array<Record<string, unknown>>)?.length > 0 && (
            <Section title="Technology Stack">
              <DictTable items={payload.stack as Array<Record<string, unknown>>} />
            </Section>
          )}
        </>
      );

    case "implementation_approach":
      return (
        <>
          {payload.overview && (
            <Section title="Overview">
              <p className="analysis-text">{String(payload.overview)}</p>
            </Section>
          )}
          <Section title="Phases">
            <DictCards items={(payload.phases as Array<Record<string, unknown>>) || []} />
          </Section>
          <Section title="Sprint Focus">
            <BulletList items={(payload.sprint_focus as string[]) || []} />
          </Section>
          <Section title={`Implementation Tasks (${((payload.tasks as unknown[]) || []).length})`}>
            <ImplementationTasks tasks={(payload.tasks as Array<Record<string, unknown>>) || []} />
          </Section>
        </>
      );

    case "cross_module_workflows":
      return (
        <>
          {payload.overview && (
            <Section title="Overview">
              <p className="analysis-text">{String(payload.overview)}</p>
            </Section>
          )}
          <Section title="Demand → Staffing">
            <BulletList items={(payload.demand_to_staffing as string[]) || []} />
          </Section>
          <Section title="Demand → People Development">
            <BulletList items={(payload.demand_to_development as string[]) || []} />
          </Section>
          <Section title="Bench Workflows">
            <BulletList items={(payload.bench_workflows as string[]) || []} />
          </Section>
          <Section title="Opportunity → Workforce">
            <BulletList items={(payload.opportunity_to_workforce as string[]) || []} />
          </Section>
          <Section title="Project Governance">
            <BulletList items={(payload.project_governance as string[]) || []} />
          </Section>
        </>
      );

    case "data_structure":
      return (
        <>
          {payload.overview && (
            <Section title="Overview">
              <p className="analysis-text">{String(payload.overview)}</p>
            </Section>
          )}
          <Section title="Entities">
            <DictTable items={(payload.entities as Array<Record<string, unknown>>) || []} />
          </Section>
          <Section title="Relationships">
            <DictTable items={(payload.relationships as Array<Record<string, unknown>>) || []} />
          </Section>
          {(payload.stack as Array<Record<string, unknown>>)?.length > 0 && (
            <Section title="Technology Stack">
              <DictTable items={payload.stack as Array<Record<string, unknown>>} />
            </Section>
          )}
        </>
      );

    case "success_measures":
      return (
        <>
          {payload.overview && (
            <Section title="Overview">
              <p className="analysis-text">{String(payload.overview)}</p>
            </Section>
          )}
          <Section title="KPIs">
            <DictTable items={(payload.kpis as Array<Record<string, unknown>>) || []} />
          </Section>
        </>
      );

    case "challenges":
      return (
        <>
          {payload.overview && (
            <Section title="Overview">
              <p className="analysis-text">{String(payload.overview)}</p>
            </Section>
          )}
          {(["data_quality", "adoption", "ownership", "integration", "standardization", "security", "scope"] as const).map(
            (field) => (
              <Section key={field} title={titleCase(field)}>
                <BulletList items={(payload[field] as string[]) || []} />
              </Section>
            ),
          )}
        </>
      );

    case "closing_note":
      return (
        <>
          {payload.overview && (
            <Section title="Overview">
              <p className="analysis-text">{String(payload.overview)}</p>
            </Section>
          )}
          <Section title="Vision Alignment">
            <p className="analysis-text">{String(payload.vision_alignment || "")}</p>
          </Section>
          <Section title="First Deliverables">
            <BulletList items={(payload.first_deliverables as string[]) || []} />
          </Section>
          <Section title="Recommended Next Decision">
            <p className="analysis-text">{String(payload.recommended_next_decision || "")}</p>
          </Section>
          {payload.frontend_development_prompt && (
            <Section title="Frontend Development Prompt (JSON)">
              <pre
                style={{
                  margin: 0,
                  padding: 16,
                  overflowX: "auto",
                  whiteSpace: "pre-wrap",
                  background: "#f8fafc",
                  color: "#1f2937",
                  borderRadius: 8,
                  fontSize: 12,
                  lineHeight: 1.5,
                }}
              >
                {prettyJson(payload.frontend_development_prompt)}
              </pre>
            </Section>
          )}
          {payload.backend_development_prompt && (
            <Section title="Backend Development Prompt">
              <pre
                style={{
                  margin: 0,
                  padding: 16,
                  overflowX: "auto",
                  whiteSpace: "pre-wrap",
                  background: "#f8fafc",
                  color: "#1f2937",
                  borderRadius: 8,
                  fontSize: 12,
                  lineHeight: 1.5,
                }}
              >
                {String(payload.backend_development_prompt)}
              </pre>
            </Section>
          )}
        </>
      );

    default:
      return renderGenericPayload(payload);
  }
}

export function AnalysisStepView({
  step,
  payload,
  confidence,
  compact = false,
}: {
  step: string;
  payload: Record<string, unknown>;
  confidence?: string | null;
  compact?: boolean;
}) {
  const label = STEP_LABELS[step] || titleCase(step);

  if (compact) {
    return (
      <div className="analysis-compact-block">
        <h5>{label}</h5>
        {confidenceBadge(confidence)}
        {renderPayload(step, payload)}
      </div>
    );
  }

  return (
    <div className="card analysis-card" id={`analysis-${step}`}>
      <div className="analysis-card-header">
        <div>
          <h3>{label}</h3>
          {STEP_PURPOSES[step] && <p>{STEP_PURPOSES[step]}</p>}
        </div>
        {confidenceBadge(confidence)}
      </div>
      {renderPayload(step, payload)}
    </div>
  );
}

function sortAnalysisSteps(analysis: AnalysisStep[]): AnalysisStep[] {
  const orderMap = new Map<string, number>(ANALYSIS_STEP_ORDER.map((s, i) => [s, i]));
  return [...analysis].sort((a, b) => {
    const ai = orderMap.get(a.step) ?? 999;
    const bi = orderMap.get(b.step) ?? 999;
    return ai - bi;
  });
}

export function AnalysisOverview({ analysis }: { analysis: AnalysisStep[] }) {
  const [currentPage, setCurrentPage] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);
  const sorted = sortAnalysisSteps(analysis || []);
  const blueprint = analysis.find((s) => s.step === "product_blueprint");
  const delivery = analysis.find((s) => s.step === "delivery_plan");
  const firstSection = blueprint || sorted.find((s) => s.step === "executive_dashboard") || sorted[0];
  const implementation = delivery || analysis.find((s) => s.step === "implementation_approach");
  const taskCount = (implementation?.payload?.tasks as unknown[] | undefined)?.length || 0;
  const requirementCount = [
    ...((blueprint?.payload?.functional as unknown[] | undefined) || []),
    ...((blueprint?.payload?.non_functional as unknown[] | undefined) || []),
  ].length;
  const riskCount = ((delivery?.payload?.risks as unknown[] | undefined) || []).length;
  const focusedSteps = ANALYSIS_STEP_ORDER.slice(0, 5).filter((step) => analysis.some((item) => item.step === step));
  const isFocusedFormat = focusedSteps.length > 0;
  const visibleSteps = isFocusedFormat ? focusedSteps : sorted.map((step) => step.step);
  const paginatedSteps = sorted.filter((step) => visibleSteps.includes(step.step as typeof visibleSteps[number]));
  const activePage = Math.min(currentPage, Math.max(paginatedSteps.length - 1, 0));
  const activeStep = paginatedSteps[activePage];

  useEffect(() => {
    setCurrentPage((page) => Math.min(page, Math.max(paginatedSteps.length - 1, 0)));
  }, [paginatedSteps.length]);

  if (!analysis?.length) {
    return <p className="analysis-muted">No analysis yet. Run AI Analysis to generate.</p>;
  }

  const changePage = (nextPage: number, scrollToContent = false) => {
    setCurrentPage(Math.max(0, Math.min(nextPage, paginatedSteps.length - 1)));
    if (scrollToContent) {
      window.requestAnimationFrame(() => contentRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    }
  };

  return (
    <div className="analysis-report-shell">
      <div className="analysis-report-hero">
        <div>
          <span className="analysis-eyebrow">AI delivery brief</span>
          <h2>{isFocusedFormat ? "Five decisions. One build-ready plan." : "Project analysis"}</h2>
          {firstSection?.payload?.overview != null && String(firstSection.payload.overview) !== "" && (
            <p>{String(firstSection.payload.overview)}</p>
          )}
        </div>
        <div className="analysis-format-pill">{isFocusedFormat ? `${focusedSteps.length} of 5 complete` : `${analysis.length} sections`}</div>
      </div>

      <div className="analysis-summary-grid">
        <div className="analysis-summary-card"><span>Focused sections</span><strong>{isFocusedFormat ? focusedSteps.length : analysis.length}</strong></div>
        <div className="analysis-summary-card"><span>Requirements</span><strong>{requirementCount}</strong></div>
        <div className="analysis-summary-card"><span>Delivery tasks</span><strong>{taskCount}</strong></div>
        <div className="analysis-summary-card"><span>Tracked risks</span><strong>{riskCount}</strong></div>
      </div>

      <nav className="analysis-section-nav" aria-label="Analysis sections">
        {visibleSteps.map((stepKey, index) => (
          <button
            type="button"
            className={`analysis-nav-card ${index === activePage ? "active" : ""}`}
            onClick={() => changePage(index, true)}
            aria-current={index === activePage ? "page" : undefined}
            key={stepKey}
          >
            <span>{String(index + 1).padStart(2, "0")}</span>
            <div>
              <strong>{(STEP_LABELS[stepKey] || titleCase(stepKey)).replace(/^\d+\.\s*/, "")}</strong>
              {STEP_PURPOSES[stepKey] && <small>{STEP_PURPOSES[stepKey]}</small>}
            </div>
          </button>
        ))}
      </nav>

      <div className="analysis-page-stage" ref={contentRef}>
        <div className="analysis-page-heading">
          <div>
            <span>Section {activePage + 1} of {paginatedSteps.length}</span>
            <strong>{activeStep ? (STEP_LABELS[activeStep.step] || titleCase(activeStep.step)).replace(/^\d+\.\s*/, "") : "Analysis"}</strong>
          </div>
          <div className="analysis-page-dots" aria-label="Section pagination">
            {paginatedSteps.map((step, index) => (
              <button
                type="button"
                className={index === activePage ? "active" : ""}
                aria-label={`Go to ${(STEP_LABELS[step.step] || titleCase(step.step)).replace(/^\d+\.\s*/, "")}`}
                onClick={() => changePage(index)}
                key={step.id}
              />
            ))}
          </div>
        </div>

        {activeStep && (
        <AnalysisStepView
          key={activeStep.id}
          step={activeStep.step}
          payload={activeStep.payload}
          confidence={activeStep.confidence}
        />
        )}

        <div className="analysis-pagination-controls">
          <button type="button" className="btn-secondary" disabled={activePage === 0} onClick={() => changePage(activePage - 1, true)}>← Previous</button>
          <span>{activePage + 1} / {paginatedSteps.length}</span>
          <button type="button" className="btn-primary" disabled={activePage === paginatedSteps.length - 1} onClick={() => changePage(activePage + 1, true)}>Next →</button>
        </div>
      </div>
    </div>
  );
}

export function AnalysisTabView({
  step,
  analysis,
}: {
  step: string;
  analysis: AnalysisStep[] | undefined;
}) {
  const data = analysis?.find((a) => a.step === step);
  if (!data) return <EmptyState step={step} />;
  return (
    <AnalysisStepView
      step={data.step}
      payload={data.payload}
      confidence={data.confidence}
    />
  );
}
