"""Validate manager workflow against DE template §2 Projects and §4 Staffing.

Uses the local SQLite database (backend/projectintel.db) via the FastAPI app.
Does not require a live AI provider for the core path: create project, create
task, skill-based recommendations, assign, dashboard stats.

Run from backend/:
  $env:PYTHONPATH = "."
  python scripts/seed.py
  python scripts/validate_manager_workflow.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.main import app

CHECKS: list[dict] = []


def record(section: str, name: str, ok: bool, detail: str) -> None:
    CHECKS.append({"section": section, "name": name, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {section} / {name}: {detail}")


async def run() -> int:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"email": "manager1@planora.local", "password": "manager123"},
        )
        record(
            "setup",
            "manager login",
            login.status_code == 200 and "access_token" in login.json(),
            f"HTTP {login.status_code}",
        )
        if login.status_code != 200:
            return 1
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = await client.get("/api/auth/me", headers=headers)
        record("setup", "GET /api/auth/me", me.status_code == 200, me.json().get("role", ""))
        record(
            "setup",
            "role is manager",
            me.json().get("role") == "manager",
            str(me.json().get("role")),
        )

        # --- §2 Projects ---
        created = await client.post(
            "/api/projects",
            headers=headers,
            json={
                "name": "DE Workflow Validation Project",
                "idea": "Internal validation of project master, tasks, and staffing match.",
                "description": "Created by scripts/validate_manager_workflow.py",
                "business_objective": "Confirm manager E2E against DE template sections 2 and 4",
            },
        )
        record("§2 Projects", "create project", created.status_code == 201, f"HTTP {created.status_code}")
        if created.status_code != 201:
            print(created.text)
            return 1
        project = created.json()
        pid = project["id"]
        record(
            "§2 Projects",
            "project master fields (AI intake)",
            all(k in project for k in ("id", "name", "idea", "status", "business_objective", "priority")),
            f"id={pid} status={project.get('status')}",
        )
        record(
            "§2 Projects",
            "expected_deadline not on API response",
            "expected_deadline" not in project,
            "DB column exists; ProjectResponse omits dates (gap vs PDF schedule)",
        )
        record(
            "§2 Projects",
            "client/account not on project",
            "client" not in project and "account" not in project,
            "No client/account master (gap vs PDF)",
        )
        record(
            "§2 Projects",
            "health score not on project",
            "health_score" not in project and "project_health_score" not in project,
            "No health score field (gap vs PDF)",
        )

        listed = await client.get("/api/projects", headers=headers)
        ids = [p["id"] for p in listed.json()] if listed.status_code == 200 else []
        record(
            "§2 Projects",
            "list manager projects",
            listed.status_code == 200 and pid in ids,
            f"HTTP {listed.status_code}, count={len(ids)}",
        )

        detail = await client.get(f"/api/projects/{pid}", headers=headers)
        record("§2 Projects", "get project detail", detail.status_code == 200, f"HTTP {detail.status_code}")

        analysis = await client.get(f"/api/projects/{pid}/analysis", headers=headers)
        record(
            "§2 Projects",
            "analysis endpoint",
            analysis.status_code == 200,
            f"HTTP {analysis.status_code}, steps={len(analysis.json()) if analysis.status_code == 200 else 0}",
        )

        versions = await client.get(f"/api/projects/{pid}/versions", headers=headers)
        record("§2 Projects", "version list", versions.status_code == 200, f"HTTP {versions.status_code}")

        approve = await client.post(f"/api/projects/{pid}/approve", headers=headers)
        approve_status = str(approve.json().get("status", "")).lower() if approve.status_code == 200 else ""
        record(
            "§2 Projects",
            "approve plan (HITL)",
            approve.status_code == 200 and approve_status == "approved",
            f"HTTP {approve.status_code} status={approve_status or approve.text[:120]}",
        )

        gen = await client.post(f"/api/projects/{pid}/generate-tasks", headers=headers)
        record(
            "§2 Projects",
            "generate tasks after approve",
            gen.status_code == 200,
            f"HTTP {gen.status_code} body={gen.text[:200]}",
        )

        task = await client.post(
            f"/api/tasks/project/{pid}",
            headers=headers,
            json={
                "name": "Implement auth module",
                "description": "Staffing validation task",
                "required_skills": {"Python": "advanced", "FastAPI": "advanced"},
            },
        )
        record("§2 Projects", "manual task create (milestones=tasks)", task.status_code == 201, f"HTTP {task.status_code}")
        if task.status_code != 201:
            print(task.text)
            return 1
        task_id = task.json()["id"]

        tasks = await client.get(f"/api/tasks/project/{pid}", headers=headers)
        record(
            "§2 Projects",
            "list project tasks",
            tasks.status_code == 200 and len(tasks.json()) >= 1,
            f"HTTP {tasks.status_code} count={len(tasks.json()) if tasks.status_code == 200 else 0}",
        )

        # --- §4 Staffing ---
        employees = await client.get("/api/employees", headers=headers)
        emp_ok = employees.status_code == 200 and len(employees.json()) >= 1
        record(
            "§4 Staffing",
            "list employees (resource pool)",
            emp_ok,
            f"HTTP {employees.status_code} count={len(employees.json()) if employees.status_code == 200 else 0}",
        )
        alice = next((e for e in employees.json() if e.get("email") == "alice@planora.local"), None) if emp_ok else None
        record("§4 Staffing", "seeded employee Alice", alice is not None, str(alice.get("id") if alice else None))

        recs = await client.get(f"/api/employees/tasks/{task_id}/recommendations", headers=headers)
        rec_list = recs.json() if recs.status_code == 200 else []
        record(
            "§4 Staffing",
            "AI skill matching recommendations",
            recs.status_code == 200 and len(rec_list) >= 1,
            f"HTTP {recs.status_code} candidates={len(rec_list)}",
        )
        if rec_list:
            top = rec_list[0]
            record(
                "§4 Staffing",
                "match score + workload on ranking",
                "skill_match_percent" in top and "workload_percent" in top,
                f"top={top.get('full_name')} match={top.get('skill_match_percent')}% load={top.get('workload_percent')}%",
            )

        assignee_id = alice["id"] if alice else (rec_list[0]["employee_id"] if rec_list else None)
        assign = await client.post(
            f"/api/tasks/{task_id}/assign",
            headers=headers,
            json={"assignee_id": assignee_id},
        )
        record(
            "§4 Staffing",
            "direct task assign (no request pipeline)",
            assign.status_code == 200 and assign.json().get("assignee_id") == assignee_id,
            f"HTTP {assign.status_code} assignee={assign.json().get('assignee_id') if assign.status_code == 200 else None}",
        )

        staffing_routes = await client.get("/api/staffing-requests", headers=headers)
        record(
            "§4 Staffing",
            "staffing_requests entity",
            staffing_routes.status_code in {404, 405},
            f"HTTP {staffing_routes.status_code} (gap: no formal request workflow)",
        )

        stats = await client.get("/api/dashboard/stats", headers=headers)
        record(
            "§1 Dashboard",
            "manager KPI stats",
            stats.status_code == 200 and "total_projects" in stats.json(),
            json.dumps(stats.json()) if stats.status_code == 200 else f"HTTP {stats.status_code}",
        )
        keys = set(stats.json().keys()) if stats.status_code == 200 else set()
        record(
            "§1 Dashboard",
            "no bench/utilization KPIs",
            "bench" not in keys and "utilization" not in keys,
            f"keys={sorted(keys)}",
        )

    failed = sum(1 for c in CHECKS if not c["ok"])
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed, {failed} failed")
    out = Path(__file__).resolve().parent.parent / "validation_manager_workflow.json"
    out.write_text(json.dumps(CHECKS, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
