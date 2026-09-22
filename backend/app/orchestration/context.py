import json
from typing import Any

from app.models import Project
from app.services.tech_stack import tech_label


def build_project_context(project: Project, prior: dict[str, Any] | None = None) -> str:
    parts = [
        f"Project Name: {project.name}",
        f"Project Idea: {project.idea}",
    ]
    if project.description:
        parts.append(f"Description: {project.description}")
    if project.business_objective:
        parts.append(f"Business Objective: {project.business_objective}")

    stack_lines: list[str] = []
    if project.frontend_technology:
        stack_lines.append(f"  Frontend: {tech_label(project.frontend_technology)}")
    if project.backend_technology:
        stack_lines.append(f"  Backend: {tech_label(project.backend_technology)}")
    if project.database_technology:
        stack_lines.append(f"  Database: {tech_label(project.database_technology)}")

    if stack_lines:
        parts.append(
            "Preferred Tech Stack (user-selected — MUST honor in all recommendations):\n"
            + "\n".join(stack_lines)
            + "\nDo not substitute a different primary frontend/backend/database unless "
            "the user's choice is incompatible with the idea (then explain why in overview)."
        )
    elif project.known_technologies:
        parts.append(f"Known Technologies: {project.known_technologies}")

    if project.business_constraints:
        parts.append(f"Business Constraints: {project.business_constraints}")
    if project.technical_constraints:
        parts.append(f"Technical Constraints: {project.technical_constraints}")
    if prior:
        parts.append(f"Prior Analysis: {json.dumps(prior, indent=2)[:6000]}")
    return "\n".join(parts)
