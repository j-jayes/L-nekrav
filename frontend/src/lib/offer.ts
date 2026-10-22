// The offer draft shared by compare, the calculator, the chart's floor line and the advisor
// (data-model.md OfferDraft). It lives in memory only; the API validates it (FR-024).
import type { Offer } from "../api/client";

export type Draft = {
  monthly_salary_sek: string;
  fte_percent: string;
  application_type: Offer["application_type"];
  filed_on: string;
  decided_on: string;
  current_permit_granted_on: string;
  exemptions: string[];
};

export const LABELS: Record<keyof Draft, string> = {
  monthly_salary_sek: "Monthly salary (SEK)",
  fte_percent: "Share of full time (%)",
  application_type: "Application",
  filed_on: "Date filed",
  decided_on: "Expected decision date",
  current_permit_granted_on: "Current permit granted on",
  exemptions: "Personal exemptions",
};

const today = () => new Date().toISOString().slice(0, 10);

export const emptyDraft = (): Draft => ({
  monthly_salary_sek: "", fte_percent: "100", application_type: "first_permit", filed_on: today(),
  decided_on: today(), current_permit_granted_on: "", exemptions: [],
});

export function toOffer(d: Draft): Offer {
  return {
    monthly_salary_sek: Number(d.monthly_salary_sek), fte_percent: Number(d.fte_percent),
    application_type: d.application_type, filed_on: d.filed_on, decided_on: d.decided_on,
    ...(d.application_type === "extension" ? { current_permit_granted_on: d.current_permit_granted_on || null } : {}),
    exemptions: d.exemptions,
  };
}

type Problem = { loc: (string | number)[]; msg: string };
const FIELDS = Object.keys(LABELS) as (keyof Draft)[];

/** A 422's `detail` as one plain message per field. A model-level message ("decided_on cannot
 * be before filed_on") belongs to the first field it names; the rest go under "form". */
export function fieldErrors(detail: Problem[]): Partial<Record<keyof Draft | "form", string>> {
  const out: Partial<Record<keyof Draft | "form", string>> = {};
  for (const { loc, msg } of detail) {
    const plain = msg.replace(/^Value error, /, "");
    const named = FIELDS.filter((f) => plain.includes(f)).sort((a, b) => plain.indexOf(a) - plain.indexOf(b));
    const field = FIELDS.find((f) => loc.includes(f)) ?? named[0] ?? "form";
    const words = FIELDS.reduce((m, f) => m.replaceAll(f, LABELS[f]), plain);
    out[field] = `${words[0].toUpperCase()}${words.slice(1)}${words.endsWith(".") ? "" : "."}`;
  }
  return out;
}
