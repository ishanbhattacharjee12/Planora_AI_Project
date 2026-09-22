import { useEffect, useRef } from "react";
import { AnalysisTokenUsage, projectsApi } from "../api";

function formatTokens(value: number): string {
  return value.toLocaleString();
}

export function AnalysisTokenBar({
  usage,
  analyzing = false,
  requestCount,
}: {
  usage: AnalysisTokenUsage | null | undefined;
  analyzing?: boolean;
  requestCount?: number;
}) {
  const hasUsage = (usage?.total_tokens || 0) > 0;

  return (
    <div className="analysis-token-bar" aria-live="polite">
      {analyzing && (
        <div className="analysis-progress-wrap">
          <div className="analysis-progress-track">
            <div className="analysis-progress-fill" />
          </div>
          <span className="analysis-progress-label">
            Running analysis… {requestCount ? `${Math.min(requestCount, 5)}/5 sections` : "5 focused sections (~2–4 min)"}
          </span>
        </div>
      )}

      <div className="analysis-token-stats">
        <div className="analysis-token-stat">
          <span className="analysis-token-label">Input tokens</span>
          <span className="analysis-token-value">{formatTokens(usage?.input_tokens ?? 0)}</span>
        </div>
        <div className="analysis-token-divider" aria-hidden="true" />
        <div className="analysis-token-stat">
          <span className="analysis-token-label">Output tokens</span>
          <span className="analysis-token-value">{formatTokens(usage?.output_tokens ?? 0)}</span>
        </div>
        <div className="analysis-token-divider" aria-hidden="true" />
        <div className="analysis-token-stat analysis-token-stat-total">
          <span className="analysis-token-label">Total</span>
          <span className="analysis-token-value">{formatTokens(usage?.total_tokens ?? 0)}</span>
        </div>
      </div>

      {!analyzing && !hasUsage && (
        <p className="analysis-token-hint">Token usage appears here after you run AI analysis.</p>
      )}
    </div>
  );
}

export function useAnalysisUsagePoll(
  projectId: number,
  enabled: boolean,
  since: string | null,
  onUpdate: (usage: AnalysisTokenUsage) => void,
) {
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  useEffect(() => {
    if (!enabled || !projectId) return;

    let cancelled = false;
    const poll = async () => {
      try {
        const usage = await projectsApi.getAnalysisUsage(projectId, since || undefined);
        if (!cancelled) onUpdateRef.current(usage);
      } catch {
        // ignore polling errors during long-running analysis
      }
    };

    poll();
    const timer = window.setInterval(poll, 4000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [projectId, enabled, since]);
}
