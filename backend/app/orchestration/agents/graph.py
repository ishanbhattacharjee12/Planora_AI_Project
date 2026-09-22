import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import ai_gateway
from app.models import ClassificationLevel, OrchestrationRun, Project
from app.orchestration.context import build_project_context
from app.orchestration.state import STEP_SCHEMAS, WORKFLOW_STEPS
from app.orchestration.normalize import normalize_json_payload
from app.orchestration.workflow import ANALYSIS_MAX_TOKENS, ANALYSIS_SYSTEM_PROMPT


def _schema_hint(schema) -> str:
    return json.dumps(schema.model_json_schema(), separators=(",", ":"))


class AgentState(TypedDict):
    project_id: int
    project_context: str
    classification: str
    user_id: int
    rag_context: str
    results: dict[str, Any]
    current_step: str


async def _run_agent_step(
    state: AgentState,
    step_name: str,
    instruction: str,
    db: AsyncSession,
    project: Project,
) -> dict[str, Any]:
    schema = STEP_SCHEMAS[step_name]
    context = state["project_context"]
    if state.get("results"):
        context += f"\nPrior: {json.dumps(state['results'])[:4000]}"
    if state.get("rag_context"):
        context += f"\n<retrieved_context>{state['rag_context'][:3000]}</retrieved_context>"

    messages = [
        {"role": "system", "content": f"{ANALYSIS_SYSTEM_PROMPT} Task: {instruction}"},
        {"role": "user", "content": f"{context}\nSchema: {_schema_hint(schema)}"},
    ]
    raw = await ai_gateway.complete_json(
        db,
        messages=messages,
        request_type=f"agent_{step_name}",
        user_id=state["user_id"],
        project_id=state["project_id"],
        classification=ClassificationLevel(state["classification"]),
        schema_name=step_name,
        json_schema=schema.model_json_schema(),
        max_tokens=ANALYSIS_MAX_TOKENS,
    )
    return schema.model_validate(normalize_json_payload(raw, schema)).model_dump()


def build_agent_graph(db: AsyncSession, project: Project):
    graph = StateGraph(AgentState)

    def make_node(step_name: str, instruction: str):
        async def node(state: AgentState) -> AgentState:
            result = await _run_agent_step(state, step_name, instruction, db, project)
            results = dict(state.get("results", {}))
            results[step_name] = result
            return {**state, "results": results, "current_step": step_name}
        return node

    prev = None
    for step_name, _, instruction in WORKFLOW_STEPS:
        graph.add_node(step_name, make_node(step_name, instruction))
        if prev:
            graph.add_edge(prev, step_name)
        else:
            graph.set_entry_point(step_name)
        prev = step_name
    graph.add_edge(prev, END)
    return graph.compile()


async def run_agent_orchestration(
    db: AsyncSession,
    project: Project,
    user_id: int,
    rag_context: str = "",
) -> dict[str, Any]:
    run = OrchestrationRun(
        project_id=project.id,
        mode="agents",
        status="running",
        current_step="starting",
    )
    db.add(run)
    await db.flush()

    initial_state: AgentState = {
        "project_id": project.id,
        "project_context": build_project_context(project),
        "classification": project.classification.value,
        "user_id": user_id,
        "rag_context": rag_context,
        "results": {},
        "current_step": "starting",
    }

    try:
        compiled = build_agent_graph(db, project)
        final_state = await compiled.ainvoke(initial_state)
        run.status = "completed"
        run.state_json = final_state.get("results", {})
        run.current_step = "done"
        await db.flush()
        return final_state.get("results", {})
    except Exception as exc:
        run.status = "failed"
        run.state_json = {"error": str(exc)}
        await db.flush()
        raise
