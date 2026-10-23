import { useState } from "react";
import type { Registry } from "../api/client";
import { type Draft, emptyDraft, LABELS } from "../lib/offer";

type Exemption = Registry["exemptions"][string];
type Props = {
  exemptions: Exemption[];
  onSubmit: (d: Draft) => void;
  errors: Partial<Record<keyof Draft | "form", string>>;
  initial?: Draft;
  submitLabel?: string;
};

/** The offer's fields, following the API's Offer schema; errors come back from the API. */
export function OfferForm({ exemptions, onSubmit, errors, initial, submitLabel = "Use this offer" }: Props) {
  const [d, setD] = useState<Draft>(initial ?? emptyDraft);
  const set = (k: keyof Draft) => (e: React.ChangeEvent<HTMLInputElement>) => setD({ ...d, [k]: e.target.value });
  const field = (k: keyof Draft, type: string, extra: object = {}) => (
    <div className="flex flex-col gap-0.5">
      <label htmlFor={`offer-${k}`} className="text-sm">{LABELS[k]}</label>
      <input id={`offer-${k}`} type={type} value={d[k] as string} onChange={set(k)}
        aria-describedby={errors[k] ? `offer-${k}-error` : undefined} aria-invalid={!!errors[k]}
        className="rounded border border-line bg-panel px-2 py-1" {...extra} />
      {errors[k] && <p id={`offer-${k}-error`} className="text-xs text-bad">{errors[k]}</p>}
    </div>
  );
  return (
    <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); onSubmit(d); }}>
      <div className="grid gap-3 sm:grid-cols-2">
        {field("monthly_salary_sek", "number", { min: 1, inputMode: "numeric" })}
        {field("fte_percent", "number", { min: 1, max: 100 })}
        <fieldset className="flex flex-col gap-1">
          <legend className="text-sm">{LABELS.application_type}</legend>
          {(["first_permit", "extension"] as const).map((t) => (
            <label key={t} className="flex items-center gap-2 text-sm">
              <input type="radio" name="application_type" checked={d.application_type === t}
                onChange={() => setD({ ...d, application_type: t })} />
              {t === "first_permit" ? "First permit" : "Extension"}
            </label>
          ))}
        </fieldset>
        {field("filed_on", "date")}
        {field("decided_on", "date")}
        {d.application_type === "extension" && field("current_permit_granted_on", "date")}
      </div>
      {exemptions.length > 0 && (
        <fieldset className="space-y-1">
          <legend className="text-sm">{LABELS.exemptions}</legend>
          {exemptions.map((x) => (
            <label key={x.id} className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1" checked={d.exemptions.includes(x.id)}
                onChange={(e) => setD({ ...d, exemptions: e.target.checked
                  ? [...d.exemptions, x.id] : d.exemptions.filter((i) => i !== x.id) })} />
              <span>{x.label} <span className="text-xs text-muted">{x.conditions}</span></span>
            </label>
          ))}
          {errors.exemptions && <p className="text-xs text-bad">{errors.exemptions}</p>}
        </fieldset>
      )}
      {errors.form && <p role="alert" className="text-sm text-bad">{errors.form}</p>}
      <button type="submit" className="rounded bg-accent px-3 py-1.5 text-sm text-white">{submitLabel}</button>
    </form>
  );
}
