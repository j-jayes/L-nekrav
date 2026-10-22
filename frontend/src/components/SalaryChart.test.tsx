import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { EligibilityAnswer, Registry, SalaryPayload } from "../api/client";
import { scale } from "../lib/chartScale";
import { fixture } from "../test/fakeApi";
import { CHART_WIDTH, chartRows, SalaryChart, sek } from "./SalaryChart";

const p = (name: string) => fixture(name).body as SalaryPayload;
const s2512 = p("salary-2512-age");
const latest = s2512.distributions.at(-1)!;
const x = (v: number) => scale([latest.p90, ...s2512.thresholds.map((t) => t.amount_sek)], CHART_WIDTH).x(v);
const num = (el: Element, attr: string) => Number(el.getAttribute(attr));

describe("chartRows", () => {
  it("takes the floor from applicable_rule_id, never choosing a rule itself", () => {
    const [plain, exempt, banned] = chartRows([p("salary-2512"), p("salary-3511-exempt"), p("salary-5343-banned")], {}, {});
    const rule = (q: SalaryPayload) => q.thresholds.find((t) => t.rule_id === q.applicable_rule_id)!;
    expect(plain.floor?.amount).toBe(rule(p("salary-2512")).amount_sek);
    expect(exempt.floor?.amount).toBe(rule(p("salary-3511-exempt")).amount_sek);
    expect(exempt.floor?.amount).not.toBe(plain.floor?.amount);
    expect(banned.floor).toBeNull();
    expect(banned.notes.join(" ")).toMatch(/permits cannot be granted/i);
  });

  it("takes the floor from the eligibility answer when an offer is entered", () => {
    const answer = fixture("eligibility-part-time").body as EligibilityAnswer;
    const [row] = chartRows([p("salary-2512")], { 2512: answer }, {});
    expect(row.floor).toMatchObject({ rule: answer.rule_id, amount: answer.threshold_sek });
    const [banned] = chartRows([p("salary-5343-banned")], { 5343: fixture("eligibility-banned").body as EligibilityAnswer }, {});
    expect(banned.floor).toBeNull();
  });

  it("leaves suppressed values out and names them", () => {
    const [row] = chartRows([p("salary-1211-suppressed")], {}, {});
    expect(row.bar).toBeNull(); // p10 is suppressed, so there is no P10-P90 bar
    expect(row.notes.join(" ")).toMatch(/SCB does not publish p10, p25/);
    const [none] = chartRows([p("salary-1111-all-suppressed")], {}, {});
    expect(none.bar).toBeNull();
    expect(none.median).toBeNull();
  });

  it("includes the simulated bar only when switched on", () => {
    expect(chartRows([s2512], {}, {})[0].simulated).toBeNull();
    expect(chartRows([s2512], {}, { 2512: true })[0].simulated?.p90).toBe(s2512.simulated!.p90);
  });
});

describe("SalaryChart", () => {
  it("draws each mark at the payload's value on one zero-based scale", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} simulated={{}} />);
    const row = screen.getByRole("group", { name: /2512/ });
    const bar = within(row).getByTestId("bar");
    expect(num(bar, "x")).toBeCloseTo(x(latest.p10!));
    expect(num(bar, "x") + num(bar, "width")).toBeCloseTo(x(latest.p90!));
    const band = within(row).getByTestId("band");
    expect(num(band, "x") + num(band, "width")).toBeCloseTo(x(latest.p25!));
    expect(num(within(row).getByTestId("median"), "x1")).toBeCloseTo(x(latest.median!));
    const dots = within(row).getAllByTestId("age-dot");
    const bands = s2512.age_bands.filter((a) => a.age_band !== "all" && a.mean_monthly != null);
    expect(dots.map((d) => num(d, "cx"))).toEqual(bands.map((a) => x(a.mean_monthly!)));
    const floor = s2512.thresholds.find((t) => t.rule_id === s2512.applicable_rule_id)!;
    expect(num(within(row).getByTestId("floor"), "x1")).toBeCloseTo(x(floor.amount_sek));
  });

  it("labels the floor with its share of the median and amount, from the payload", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} simulated={{}} />);
    const floor = s2512.thresholds.find((t) => t.rule_id === s2512.applicable_rule_id)!;
    const label = screen.getByText(/salary floor/i, { selector: "[data-floor-label]" });
    expect(label.textContent).toContain(`${floor.percent} % of the median`);
    expect(label.textContent?.replace(/\s/g, "")).toContain(String(floor.amount_sek));
  });

  it("links each floor to its rule's source and checked-on date, and says it is not legal advice", () => {
    const rules = (fixture("registry").body as Registry).rules;
    render(<SalaryChart payloads={[s2512]} eligibility={{}} simulated={{}} rules={rules} />);
    const label = screen.getByText(/salary floor/i, { selector: "[data-floor-label]" });
    const source = rules[s2512.applicable_rule_id!].source;
    expect(label.querySelector("a")).toHaveAttribute("href", source.url);
    expect(label).toHaveTextContent(`checked ${source.checked_on}`);
    expect(screen.getByText(/information, not legal advice/i)).toBeInTheDocument();
  });

  it("draws the simulated bar dashed and labelled, with its formula on request", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} simulated={{ 2512: true }} />);
    const ghost = screen.getByTestId("simulated");
    expect(ghost.getAttribute("stroke-dasharray")).toBeTruthy();
    expect(screen.getByText(/simulated, ages 25-34/i)).toBeInTheDocument();
    expect(screen.getByText(s2512.simulated!.formula)).toBeInTheDocument();
  });

  it("names the tables and credits the producer", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} simulated={{}} />);
    expect(screen.getByText(/TAB5932 \(2025\)/)).toBeInTheDocument();
    expect(screen.getByText(/Medlingsinstitutet \/ SCB lönestrukturstatistik \(AM0110\)/)).toBeInTheDocument();
  });

  it("gives every mark its value on focus, and offers the same figures as a table", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} simulated={{}} />);
    const bar = screen.getByTestId("bar").closest("[tabindex]")!;
    fireEvent.focus(bar);
    expect(screen.getByRole("status")).toHaveTextContent(/P10.*P90/);
    const table = screen.getByRole("table", { name: /salary by code/i });
    const squash = (t: string | null) => t?.replace(/\s/g, "");
    expect(squash(within(table).getByRole("row", { name: /2512/ }).textContent)).toContain(squash(sek(latest.median!)));
  });

  it("explains a code with no SCB figures instead of drawing a bar", () => {
    render(<SalaryChart payloads={[p("salary-1111-all-suppressed")]} eligibility={{}} simulated={{}} />);
    expect(screen.queryByTestId("bar")).toBeNull();
    expect(screen.getAllByText(/SCB does not publish/).length).toBeGreaterThan(0);
  });
});
