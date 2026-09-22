export interface TechOption {
  value: string;
  label: string;
}

export const FRONTEND_OPTIONS: TechOption[] = [
  { value: "", label: "Select frontend..." },
  { value: "html_css_js", label: "HTML / CSS / JavaScript" },
  { value: "react", label: "React" },
  { value: "vue", label: "Vue.js" },
  { value: "angular", label: "Angular" },
  { value: "nextjs", label: "Next.js" },
  { value: "svelte", label: "Svelte" },
];

export const BACKEND_OPTIONS: TechOption[] = [
  { value: "", label: "Select backend..." },
  { value: "node_express", label: "Node.js (Express)" },
  { value: "python_fastapi", label: "Python (FastAPI)" },
  { value: "python_django", label: "Python (Django)" },
  { value: "java_spring", label: "Java (Spring Boot)" },
  { value: "dotnet", label: ".NET" },
  { value: "go", label: "Go" },
];

export const DATABASE_OPTIONS: TechOption[] = [
  { value: "", label: "Select database..." },
  { value: "postgresql", label: "PostgreSQL" },
  { value: "mysql", label: "MySQL" },
  { value: "mongodb", label: "MongoDB" },
  { value: "sqlite", label: "SQLite" },
  { value: "redis", label: "Redis" },
];

export function techLabel(
  value: string | null | undefined,
  options: TechOption[]
): string {
  if (!value) return "—";
  return options.find((o) => o.value === value)?.label ?? value;
}
