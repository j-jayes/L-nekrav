// The codes on the chart and in the comparison, shared by the user and the advisor (data-model.md).
// The most recent change wins, whichever side made it.
import type { SalaryPayload } from "../api/client";
import { MAX_CODES } from "./urlState";

export type Selection = {
  codes: string[];
  payloads: Record<string, SalaryPayload>;
  simulated: Record<string, boolean>;
  note: string | null; // the last thing the user should be told about the selection
  leftOut: string[]; // codes the advisor selected that did not fit
};

export type Action =
  | { type: "add"; code: string }
  | { type: "remove"; code: string }
  | { type: "advisor"; codes: string[] }
  | { type: "load"; codes: string[]; dropped: string[] }
  | { type: "payload"; code: string; payload: SalaryPayload }
  | { type: "simulated"; code: string };

export const initial = (): Selection => ({ codes: [], payloads: {}, simulated: {}, note: null, leftOut: [] });

const only = <T,>(r: Record<string, T>, codes: string[]) =>
  Object.fromEntries(Object.entries(r).filter(([c]) => codes.includes(c)));

function withCodes(s: Selection, codes: string[], note: string | null, leftOut: string[] = []): Selection {
  return { codes, payloads: only(s.payloads, codes), simulated: only(s.simulated, codes), note, leftOut };
}

export function select(s: Selection, a: Action): Selection {
  switch (a.type) {
    case "add":
      if (s.codes.includes(a.code)) return { ...s, note: `${a.code} is already selected.` };
      if (s.codes.length >= MAX_CODES)
        return { ...s, note: "The chart holds at most four codes: remove one first." };
      return withCodes(s, [...s.codes, a.code], null);
    case "remove":
      return withCodes(s, s.codes.filter((c) => c !== a.code), null);
    case "advisor": {
      const all = [...s.codes.filter((c) => !a.codes.includes(c)), ...a.codes];
      const kept = all.slice(-MAX_CODES);
      const leftOut = all.filter((c) => !kept.includes(c));
      return withCodes(s, kept, leftOut.length ? `Left out to keep four: ${leftOut.join(", ")}.` : null, leftOut);
    }
    case "load":
      return withCodes(s, a.codes, a.dropped.length ? `Not selected from the link: ${a.dropped.join(", ")}.` : null);
    case "payload":
      return s.codes.includes(a.code) ? { ...s, payloads: { ...s.payloads, [a.code]: a.payload } } : s;
    case "simulated":
      return { ...s, simulated: { ...s.simulated, [a.code]: !s.simulated[a.code] } };
  }
}
