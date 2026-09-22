"""Generate a structured PDF report from the focused project analysis."""

from __future__ import annotations

import io
import json
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import Project, ProjectAnalysis
from app.orchestration.state import STEP_ORDER

SECTION_TITLES: dict[str, str] = {
    "product_blueprint": "1. Product Blueprint",
    "solution_architecture": "2. Solution Architecture",
    "delivery_plan": "3. Delivery Plan",
    "team_operations": "4. Team & Operations",
    "launch_growth": "5. Launch & Growth",
    # Legacy titles keep previously generated reports downloadable.
    "executive_dashboard": "1. Executive Dashboard",
    "projects": "2. Projects",
    "resources": "3. Resources",
    "staffing": "4. Staffing",
    "people_development": "5. People Development",
    "business": "6. Business",
    "analytics": "7. Analytics",
    "reports": "8. Reports",
    "administration": "9. Administration",
    "quick_links": "10. Quick Links",
    "cross_module_workflows": "11. Cross-module Workflows",
    "data_structure": "12. High-Level Data Structure",
    "implementation_approach": "13. Suggested Implementation Approach",
    "success_measures": "14. Key Success Measures",
    "challenges": "15. Challenges & Considerations",
    "future_enhancements": "16. Future Enhancements",
    "closing_note": "17. Closing Note",
}

SKIP_KEYS = {"confidence"}

DEFAULT_HOW_TO_READ = (
    "This document is written as a practical starting point rather than a final technical "
    "specification. The screens shown in the document are reference designs to help the team "
    "agree on what the system should provide. The numbers and names visible in the mock-ups are "
    "examples and should be replaced with actual data during implementation."
)

OVERVIEW_BLUE = colors.HexColor("#1a3b5d")
OVERVIEW_BLUE_LIGHT = colors.HexColor("#2b6cb0")


def _title_case(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _escape(text: Any) -> str:
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE).strip()
    cleaned = re.sub(r"[-\s]+", "-", cleaned)
    return cleaned or "project-analysis"


def _format_status(status: Any) -> str:
    raw = status.value if hasattr(status, "value") else str(status)
    return raw.replace("_", " ").strip().title()


def _resolve_purpose(project: Project) -> str:
    for value in (project.business_objective, project.description, project.idea):
        if value:
            return str(value)
    return "—"


def _display(value: str | None) -> str:
    return value.strip() if value and value.strip() else "—"


class AnalysisPdfBuilder:
    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "ReportTitle",
            parent=self.styles["Title"],
            fontSize=22,
            leading=26,
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        self.subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=self.styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        self.section_style = ParagraphStyle(
            "SectionHeading",
            parent=self.styles["Heading1"],
            fontSize=16,
            leading=20,
            spaceBefore=10,
            spaceAfter=8,
            textColor=colors.HexColor("#1a1a2e"),
        )
        self.subsection_style = ParagraphStyle(
            "SubsectionHeading",
            parent=self.styles["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.HexColor("#2d3748"),
        )
        self.body_style = ParagraphStyle(
            "Body",
            parent=self.styles["BodyText"],
            fontSize=10,
            leading=14,
            spaceAfter=6,
        )
        self.muted_style = ParagraphStyle(
            "Muted",
            parent=self.body_style,
            textColor=colors.HexColor("#718096"),
            fontSize=9,
        )
        self.overview_title_style = ParagraphStyle(
            "OverviewTitle",
            parent=self.styles["Heading1"],
            fontSize=18,
            leading=22,
            spaceAfter=10,
            textColor=OVERVIEW_BLUE,
        )
        self.overview_subtitle_style = ParagraphStyle(
            "OverviewSubtitle",
            parent=self.styles["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=14,
            spaceAfter=6,
            textColor=OVERVIEW_BLUE_LIGHT,
        )
        self.overview_cell_style = ParagraphStyle(
            "OverviewCell",
            parent=self.body_style,
            fontSize=10,
            leading=13,
        )

    def build(self, project: Project, analyses: list[ProjectAnalysis]) -> bytes:
        by_step = {a.step: a for a in analyses}
        ordered = [by_step[s] for s in STEP_ORDER if s in by_step]
        ordered.extend(a for a in analyses if a.step not in STEP_ORDER)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
            title=f"{project.name} — AI Analysis Report",
            author="Planora AI",
        )

        story: list[Any] = []
        story.extend(self._document_overview_page(project, ordered))
        story.append(PageBreak())

        for analysis in ordered:
            story.extend(self._render_section(analysis))
            story.append(PageBreak())

        doc.build(story)
        return buffer.getvalue()

    def _document_overview_page(self, project: Project, analyses: list[ProjectAnalysis]) -> list[Any]:
        document_type = getattr(project, "document_type", None) or "Functional Documentation"
        how_to_read = getattr(project, "how_to_read", None) or DEFAULT_HOW_TO_READ

        overview_rows = [
            ("Project", _display(project.name)),
            ("Organization", _display(getattr(project, "organization", None))),
            ("Document Type", _display(document_type)),
            ("Primary Users", _display(getattr(project, "primary_users", None))),
            ("Purpose", _resolve_purpose(project)),
            ("Status", _display(_format_status(project.status))),
        ]

        story: list[Any] = [
            Paragraph("Document Overview", self.overview_title_style),
            Spacer(1, 0.08 * inch),
            self._overview_table(overview_rows),
            Paragraph("How to read this document", self.overview_subtitle_style),
            Paragraph(_escape(how_to_read), self.body_style),
            Paragraph("Contents", self.overview_subtitle_style),
            Spacer(1, 0.05 * inch),
        ]

        items = [
            ListItem(
                Paragraph(_escape(SECTION_TITLES.get(a.step, _title_case(a.step))), self.body_style),
                leftIndent=12,
            )
            for a in analyses
        ]
        story.append(ListFlowable(items, bulletType="1", start="1", leftIndent=18))
        return story

    def _overview_table(self, rows: list[tuple[str, str]]) -> Table:
        data: list[list[Any]] = [
            [
                Paragraph("<b>Item</b>", self.overview_cell_style),
                Paragraph("<b>Details</b>", self.overview_cell_style),
            ]
        ]
        for item, details in rows:
            data.append([
                Paragraph(f"<b>{_escape(item)}</b>", self.overview_cell_style),
                Paragraph(_escape(details), self.overview_cell_style),
            ])

        table = Table(data, colWidths=[1.8 * inch, 4.7 * inch], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), OVERVIEW_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def _render_section(self, analysis: ProjectAnalysis) -> list[Any]:
        title = SECTION_TITLES.get(analysis.step, _title_case(analysis.step))
        confidence = analysis.confidence or analysis.payload.get("confidence")
        story: list[Any] = [Paragraph(_escape(title), self.section_style)]
        if confidence:
            story.append(Paragraph(f"<i>Confidence: {_escape(confidence)}</i>", self.muted_style))

        payload = analysis.payload or {}
        if payload.get("overview"):
            story.extend([
                Paragraph("Overview", self.subsection_style),
                Paragraph(_escape(payload["overview"]), self.body_style),
            ])

        for key, value in payload.items():
            if key in SKIP_KEYS or key == "overview":
                continue
            story.extend(self._render_field(_title_case(key), value))
        return story

    def _render_field(self, label: str, value: Any) -> list[Any]:
        if value is None or value == "" or value == [] or value == {}:
            return []

        if isinstance(value, str):
            return [
                Paragraph(_escape(label), self.subsection_style),
                Paragraph(_escape(value), self.body_style),
            ]

        if isinstance(value, list):
            if not value:
                return []
            if all(isinstance(item, str) for item in value):
                return [
                    Paragraph(_escape(label), self.subsection_style),
                    self._bullet_list(value),
                ]
            if all(isinstance(item, dict) for item in value):
                if label.lower() in {"kpi cards", "kpis"} or any("metric" in item for item in value):
                    return [
                        Paragraph(_escape(label), self.subsection_style),
                        self._dict_table(value),
                    ]
                if any("task_id" in item for item in value):
                    return self._render_tasks(label, value)
                return [
                    Paragraph(_escape(label), self.subsection_style),
                    self._dict_table(value),
                ]

        if isinstance(value, dict):
            return [
                Paragraph(_escape(label), self.subsection_style),
                Paragraph(_escape(json.dumps(value, indent=2, ensure_ascii=False)), self.body_style),
            ]

        return [
            Paragraph(_escape(label), self.subsection_style),
            Paragraph(_escape(value), self.body_style),
        ]

    def _render_tasks(self, label: str, tasks: list[dict[str, Any]]) -> list[Any]:
        story: list[Any] = [Paragraph(_escape(label), self.subsection_style)]
        for task in tasks:
            header = f"{task.get('task_id', 'TASK')} — {task.get('name', 'Untitled')}"
            story.append(Paragraph(f"<b>{_escape(header)}</b>", self.body_style))
            if task.get("description"):
                story.append(Paragraph(_escape(task["description"]), self.body_style))
            meta = []
            if task.get("priority"):
                meta.append(f"Priority: {task['priority']}")
            if task.get("estimated_effort_days") is not None:
                meta.append(f"Effort: {task['estimated_effort_days']} days")
            if task.get("difficulty"):
                meta.append(f"Difficulty: {task['difficulty']}")
            if meta:
                story.append(Paragraph(_escape(" · ".join(meta)), self.muted_style))
            skills = task.get("required_skills") or {}
            if isinstance(skills, dict) and skills:
                skill_text = ", ".join(f"{k} ({v})" for k, v in skills.items())
                story.append(Paragraph(f"<i>Skills:</i> {_escape(skill_text)}", self.muted_style))
            deps = task.get("dependencies") or []
            if deps:
                story.append(Paragraph(f"<i>Depends on:</i> {_escape(', '.join(str(d) for d in deps))}", self.muted_style))
            story.append(Spacer(1, 0.08 * inch))
        return story

    def _bullet_list(self, items: list[Any]) -> ListFlowable:
        return ListFlowable(
            [ListItem(Paragraph(_escape(item), self.body_style), leftIndent=12) for item in items],
            bulletType="bullet",
            leftIndent=18,
        )

    def _dict_table(self, rows: list[dict[str, Any]]) -> Table:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        if not keys:
            keys = ["value"]

        data = [[Paragraph(f"<b>{_escape(_title_case(k))}</b>", self.body_style) for k in keys]]
        for row in rows:
            data.append([Paragraph(_escape(row.get(k, "—")), self.body_style) for k in keys])

        table = Table(data, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a202c")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table


def build_analysis_pdf(project: Project, analyses: list[ProjectAnalysis]) -> bytes:
    return AnalysisPdfBuilder().build(project, analyses)


def analysis_pdf_filename(project: Project) -> str:
    return f"{_safe_filename(project.name)}-analysis-v{project.current_version}.pdf"
