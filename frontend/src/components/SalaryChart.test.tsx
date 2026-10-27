import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { EligibilityAnswer, Registry, SalaryPayload } from "../api/client";
import { scale } from "../lib/chartScale";
import { fixture } from "../test/fakeApi";
import { CHART_WIDTH, chartRows, SalaryChart, sek } from "./SalaryChart";

const p = (name: string) => fixture(name).body as SalaryPayload;
const s2512 = p("salary-2512-age-region");
const s2511 = p("salary-2511-age-region");
const latest = s2512.distributions.at(-1)!;
const floorOf = (q: SalaryPayload) => q.thresholds.find((t) => t.rule_id === q.applicable_rule_id)!;
const NUMBER = 60000;
const num = (el: Element, attr: string) => Number(el.getAttribute(attr));
const squash = (t: string | null | undefined) => t?.replace(/\s/g, "");

/** The values the chart draws for 2512 alone, so the test computes the same scale. */
function x2512(withNumber: boolean) {
  const sim = s2512.simulated!;
  const values = [latest.p10, latest.p90, latest.median, floorOf(s2512).amount_sek, sim.p25, sim.p75,
    withNumber ? NUMBER : null];
  return scale(values, CHART_WIDTH).x;
}

describe("chartRows", () => {
  it("takes the floor from applicable_rule_id, never choosing a rule itself", () => {
    const [plain, exempt, banned] = chartRows([p("salary-2512"), p("salary-3511-exempt"), p("salary-5343-banned")], {});
    expect(plain.floor?.amount).toBe(floorOf(p("salary-2512")).amount_sek);
    expect(exempt.floor?.amount).toBe(floorOf(p("salary-3511-exempt")).amount_sek);
    expect(exempt.floor?.amount).not.toBe(plain.floor?.amount);
    expect(banned.floor).toBeNull();
    expect(banned.notes.join(" ")).toMatch(/permits cannot be granted/i);
  });

  it("takes the floor from the eligibility answer when an offer is entered", () => {
    const answer = fixture("eligibility-part-time").body as EligibilityAnswer;
    const [row] = chartRows([p("salary-2512")], { 2512: answer });
    expect(row.floor).toMatchObject({ rule: answer.rule_id, amount: answer.threshold_sek });
    const [banned] = chartRows([p("salary-5343-banned")], { 5343: fixture("eligibility-banned").body as EligibilityAnswer });
    expect(banned.floor).toBeNull();
  });

  it("leaves suppressed values out and names them", () => {
    const [row] = chartRows([p("salary-1211-suppressed")], {});
    expect(row.spread).toBeNull(); // p10 is suppressed, so there is no P10-P90 bar
    expect(row.notes.join(" ")).toMatch(/SCB does not publish p10, p25/);
    const [none] = chartRows([p("salary-1111-all-suppressed")], {});
    expect(none.spread).toBeNull();
    expect(none.middle).toBeNull();
    expect(none.median).toBeNull();
  });

  it("carries the estimate whenever the payload has one; no checkbox decides it", () => {
    expect(chartRows([p("salary-2512")], {})[0].estimate).toBeNull();
    expect(chartRows([s2512], {})[0].estimate?.p75).toBe(s2512.simulated!.p75);
  });
});

describe("SalaryChart", () => {
  it("draws the spread, the middle half and the median at the payload's values", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} number={null} />);
    const x = x2512(false);
    const row = screen.getByRole("group", { name: /2512/ });
    const spread = within(row).getByTestId("spread");
    expect(num(spread, "x")).toBeCloseTo(x(latest.p10!));
    expect(num(spread, "x") + num(spread, "width")).toBeCloseTo(x(latest.p90!));
    const middle = within(row).getByTestId("middle");
    expect(num(middle, "x")).toBeCloseTo(x(latest.p25!));
    expect(num(middle, "x") + num(middle, "width")).toBeCloseTo(x(latest.p75!));
    expect(num(within(row).getByTestId("median"), "x1")).toBeCloseTo(x(latest.median!));
    expect(num(within(row).getByTestId("floor"), "x1")).toBeCloseTo(x(floorOf(s2512).amount_sek));
    expect(within(row).queryByTestId("age-dot")).toBeNull(); // 006 FR-014: the dots are gone
  });

  it("draws the estimate as a dashed outline, labelled as not an SCB figure", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} number={null} />);
    const x = x2512(false);
    const est = screen.getByTestId("estimate");
    expect(est.getAttribute("stroke-dasharray")).toBeTruthy();
    expect(num(est, "x")).toBeCloseTo(x(s2512.simulated!.p25!));
    expect(screen.getByText(/estimate for ages 25-34 in Stockholm: not an SCB figure/i)).toBeInTheDocument();
    expect(screen.getByText(s2512.simulated!.formula)).toBeInTheDocument();
    expect(screen.getByText(/Estimates are not SCB figures/)).toBeInTheDocument();
  });

  it("draws the candidate's number once across every row, labelled once", () => {
    render(<SalaryChart payloads={[s2512, s2511]} eligibility={{}} number={NUMBER} />);
    const lines = screen.getAllByTestId("number");
    expect(lines).toHaveLength(2);
    expect(new Set(lines.map((l) => l.getAttribute("x1"))).size).toBe(1);
    expect(screen.getAllByText(/^your 60\s000$/i)).toHaveLength(1);
    expect(screen.getAllByText(/^floor$/)).toHaveLength(1);
  });

  it("scales around the drawn values: the axis starts below the lowest and above zero", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} number={NUMBER} />);
    const ticks = screen.getByTestId("axis").querySelectorAll("text");
    const first = Number(ticks[0].textContent!.replace("k", "")) * 1000;
    expect(first).toBeGreaterThan(0);
    expect(first).toBeLessThan(Math.min(latest.p10!, floorOf(s2512).amount_sek));
  });

  it("shows no number line without a number, and invites one", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} number={null} />);
    expect(screen.queryByTestId("number")).toBeNull();
    expect(screen.getByText(/enter your number to see it on the chart/i)).toBeInTheDocument();
  });

  it("lists only the marks drawn in the legend", () => {
    render(<SalaryChart payloads={[p("salary-2512")]} eligibility={{}} number={null} />);
    const legend = screen.getByRole("list", { name: "Legend" });
    expect(legend).toHaveTextContent(/P10–P90/);
    expect(legend).toHaveTextContent(/Middle half \(P25–P75\)/);
    expect(legend).not.toHaveTextContent(/Estimate/);
    expect(legend).not.toHaveTextContent(/Your number/);
  });

  it("labels the floor with its share of the median, its amount and its source", () => {
    const rules = (fixture("registry").body as Registry).rules;
    render(<SalaryChart payloads={[s2512]} eligibility={{}} number={null} rules={rules} />);
    const floor = floorOf(s2512);
    const label = screen.getByText(/salary floor/i, { selector: "[data-floor-label]" });
    expect(label.textContent).toContain(`${floor.percent} % of the median`);
    expect(squash(label.textContent)).toContain(String(floor.amount_sek));
    expect(label.querySelector("a")).toHaveAttribute("href", rules[s2512.applicable_rule_id!].source.url);
    expect(screen.getByText(/information, not legal advice/i)).toBeInTheDocument();
  });

  it("names the tables and credits the producer", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} number={null} />);
    const caption = screen.getByText(/^Monthly salary, SEK/, { selector: "figcaption" });
    expect(caption).toHaveTextContent(/TAB5932 \(2025\), TAB5844 \(2025\), TAB5696 \(2025\)/);
    expect(caption).toHaveTextContent(/Medlingsinstitutet \/ SCB lönestrukturstatistik \(AM0110\)/);
  });

  it("gives every mark its value on focus, and the table lists every drawn value", () => {
    render(<SalaryChart payloads={[s2512]} eligibility={{}} number={NUMBER} />);
    fireEvent.focus(screen.getByTestId("spread").closest("[tabindex]")!);
    expect(screen.getByRole("status")).toHaveTextContent(/P10.*P90/);
    fireEvent.focus(screen.getByTestId("estimate").closest("[tabindex]")!);
    expect(screen.getByRole("status")).toHaveTextContent(/estimate/i);
    const table = screen.getByRole("table", { name: /salary by code/i });
    const head = squash(within(table).getAllByRole("columnheader").map((h) => h.textContent).join("|"));
    expect(head).toBe(squash("Code|P10|P25|Median|P75|P90|Estimate P25–P75|Floor|Your number"));
    const row = squash(within(table).getByRole("row", { name: /2512/ }).textContent);
    for (const v of [latest.p75!, s2512.simulated!.p25!, s2512.simulated!.p75!, NUMBER])
      expect(row).toContain(squash(sek(v)));
  });

  it("explains a code with no SCB figures instead of drawing a bar", () => {
    render(<SalaryChart payloads={[p("salary-1111-all-suppressed")]} eligibility={{}} number={null} />);
    expect(screen.queryByTestId("spread")).toBeNull();
    expect(screen.getAllByText(/SCB does not publish/).length).toBeGreaterThan(0);
  });
});
