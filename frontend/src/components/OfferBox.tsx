import type { EligibilityAnswer, Offer, Registry } from "../api/client";
import type { Draft } from "../lib/offer";
import { OfferPanel } from "./OfferPanel";
import { sek } from "./SalaryChart";

type Props = {
  code: string;
  draft: Draft;
  offer: Offer | null;
  registry: Registry | null;
  onApplied: (draft: Draft, offer: Offer, answer: EligibilityAnswer) => void;
  onClear: () => void;
};

/** The shared offer, collapsible; applying it moves each code's floor line and fills the comparison. */
export function OfferBox({ code, draft, offer, registry, onApplied, onClear }: Props) {
  return (
    <details className="rounded border border-line bg-panel p-3">
      <summary className="cursor-pointer text-sm font-semibold">
        {offer ? `Your offer: ${sek(offer.monthly_salary_sek)} a month at ${offer.fte_percent} % of full time`
          : "Add your offer to see whether it reaches each code's floor"}
      </summary>
      <div className="mt-3 space-y-2">
        <OfferPanel code={code} draft={draft} exemptions={Object.values(registry?.exemptions ?? {})}
          onApplied={onApplied} />
        {offer && <button type="button" className="text-sm text-accent underline" onClick={onClear}>Remove the offer</button>}
      </div>
    </details>
  );
}
