import type { EligibilityAnswer } from "../api/client";
import { sek } from "./SalaryChart";
import { SourceLink } from "./SourceLink";

// Status in words and an icon, never colour alone; a pass and a fail look alike otherwise (FR-012).
const STATUS: Record<EligibilityAnswer["status"], string> = {
  pass: "✓ The offer reaches the salary floor",
  fail: "✗ The offer does not reach the salary floor",
  not_permitted: "✗ Work permits cannot be granted for this code",
  out_of_scope: "– This offer is outside what Lönekrav checks",
};

export function Margin({ answer }: { answer: EligibilityAnswer }) {
  if (answer.margin_sek == null) return null;
  const sign = answer.margin_sek >= 0 ? "+" : "−";
  return (
    <span className="tabular-nums">
      {sign}{sek(Math.abs(answer.margin_sek))}
      {answer.margin_percent != null && ` (${sign}${Math.abs(answer.margin_percent)} %)`}
    </span>
  );
}

/** The API's eligibility answer: status, rule, threshold, margin, warnings, sources, disclaimer. */
export function EligibilityResult({ answer, compact = false }: { answer: EligibilityAnswer; compact?: boolean }) {
  return (
    <div className="space-y-1 text-sm">
      <p className="font-semibold">{STATUS[answer.status]}</p>
      {answer.threshold_sek != null && (
        <p>
          Floor {sek(answer.threshold_sek)}
          {answer.median && ` (${answer.percent} % of the median ${sek(answer.median.amount)}, SCB ${answer.median.scb_reference_year})`}
          {answer.margin_sek != null && <>; margin <Margin answer={answer} /></>}
        </p>
      )}
      {!compact && <p className="text-muted">{answer.reason}</p>}
      {answer.warnings.map((w) => (
        <p key={w.kind} className="border-l-4 border-warn pl-2">
          <strong>Note:</strong> {w.message} <SourceLink source={w.source} />
        </p>
      ))}
      {!compact && (
        <>
          <ul className="space-y-0.5">
            {answer.sources.map((s) => <li key={s.key}><SourceLink source={s} /></li>)}
          </ul>
          <p className="text-xs text-muted">{answer.disclaimer}</p>
        </>
      )}
    </div>
  );
}
