TECH_LABELS: dict[str, str] = {
    "html_css_js": "HTML / CSS / JavaScript",
    "react": "React",
    "vue": "Vue.js",
    "angular": "Angular",
    "nextjs": "Next.js",
    "svelte": "Svelte",
    "node_express": "Node.js (Express)",
    "python_fastapi": "Python (FastAPI)",
    "python_django": "Python (Django)",
    "java_spring": "Java (Spring Boot)",
    "dotnet": ".NET",
    "go": "Go",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "sqlite": "SQLite",
    "redis": "Redis",
}


def tech_label(value: str | None) -> str | None:
    if not value:
        return None
    return TECH_LABELS.get(value, value)


def compose_known_technologies(
    frontend: str | None,
    backend: str | None,
    database: str | None,
) -> str:
    parts: list[str] = []
    if frontend:
        parts.append(f"Frontend: {tech_label(frontend)}")
    if backend:
        parts.append(f"Backend: {tech_label(backend)}")
    if database:
        parts.append(f"Database: {tech_label(database)}")
    return " | ".join(parts)
