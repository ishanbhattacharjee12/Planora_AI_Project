import { ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

const CHART_COLORS = ["#f2c811", "#171717", "#71717a", "#d4d4d8"];

export function MetricCard({
  label,
  value,
  icon,
  tone = "neutral",
  detail,
  onClick,
}: {
  label: string;
  value: number | string;
  icon: ReactNode;
  tone?: "positive" | "negative" | "neutral";
  detail?: string;
  onClick?: () => void;
}) {
  const TrendIcon = tone === "positive" ? ArrowUpRight : tone === "negative" ? ArrowDownRight : Minus;
  return (
    <article className={`metric-card ${onClick ? "is-clickable" : ""}`} onClick={onClick} onKeyDown={(event) => { if (onClick && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); onClick(); } }} role={onClick ? "link" : undefined} tabIndex={onClick ? 0 : undefined}>
      <div className="metric-card-top">
        <span className="metric-icon">{icon}</span>
        {detail && <span className={`metric-detail ${tone}`}><TrendIcon size={13} />{detail}</span>}
      </div>
      <strong className="metric-value">{value}</strong>
      <span className="metric-label">{label}</span>
    </article>
  );
}

export function WorkloadBarChart({ data }: { data: Array<{ name: string; value: number }> }) {
  return (
    <div className="chart-frame" role="img" aria-label="Workload overview bar chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 6, right: 4, left: -24, bottom: 0 }}>
          <CartesianGrid stroke="#ecebe7" vertical={false} />
          <XAxis dataKey="name" tick={{ fill: "#71717a", fontSize: 13 }} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} tick={{ fill: "#a1a1aa", fontSize: 13 }} axisLine={false} tickLine={false} />
          <Tooltip cursor={{ fill: "#faf9f5" }} contentStyle={{ border: "1px solid #e4e2dc", borderRadius: 6, boxShadow: "0 10px 25px rgba(0,0,0,.08)" }} />
          <Bar dataKey="value" fill="#171717" radius={[4, 4, 0, 0]} maxBarSize={42} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DistributionChart({
  data,
  centerLabel,
  onSliceClick,
}: {
  data: Array<{ name: string; value: number }>;
  centerLabel: string;
  onSliceClick?: (item: { name: string; value: number }) => void;
}) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const populated = total ? data : [{ name: "No data", value: 1 }];
  return (
    <div className="distribution-wrap">
      <div className="donut-frame">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={populated} dataKey="value" nameKey="name" innerRadius="67%" outerRadius="91%" paddingAngle={total ? 3 : 0} stroke="none" onClick={(_, index) => { const item = populated[index]; if (item && onSliceClick) onSliceClick(item); }}>
              {populated.map((_, index) => <Cell key={index} fill={total ? CHART_COLORS[index % CHART_COLORS.length] : "#ecebe7"} />)}
            </Pie>
            <Tooltip contentStyle={{ border: "1px solid #e4e2dc", borderRadius: 6 }} />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center"><strong>{total}</strong><span>{centerLabel}</span></div>
      </div>
      <div className="chart-legend">
        {data.map((item, index) => (
          <div className={`legend-row ${onSliceClick ? "is-clickable" : ""}`} key={item.name} onClick={() => onSliceClick?.(item)} role={onSliceClick ? "link" : undefined} tabIndex={onSliceClick ? 0 : undefined} onKeyDown={(event) => { if (onSliceClick && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); onSliceClick(item); } }}>
            <span className="legend-dot" style={{ background: CHART_COLORS[index % CHART_COLORS.length] }} />
            <span>{item.name}</span><strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Panel({ title, eyebrow, action, children, className = "" }: {
  title: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`workspace-panel ${className}`}>
      <header className="panel-header">
        <div>{eyebrow && <span className="panel-eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>
        {action}
      </header>
      {children}
    </section>
  );
}
