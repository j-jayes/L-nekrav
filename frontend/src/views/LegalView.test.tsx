import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { EligibilityAnswer, Registry, TimelineEvent } from "../api/client";
import { emptyDraft } from "../lib/offer";
import { fixture, serve } from "../test/fakeApi";
import { LegalView } from "./LegalView";

const registry = fixture("registry").body as Registry;
const timeline = fixture("timeline").body as TimelineEvent[];
const partTime = fixture("eligibility-part-time").body as EligibilityAnswer;

function setup(answer = fixture("eligibility-part-time")) {
  const seen = serve({ "GET /api/v1/legal/timeline": fixture("timeline"), "POST /api/v1/eligibility": answer });
  const onApplied = vi.fn();
  render(<LegalView registry={registry} draft={emptyDraft()} onApplied={onApplied} />);
  return { seen, onApplied };
}

describe("LegalView", () => {
  it("shows every rule with its source link and checked-on date", () => {
    setup();
    const rules = screen.getByRole("region", { name: /the rules/i });
    for (const r of Object.values(registry.rules)) expect(rules).toHaveTextContent(r.applies_to);
    const links = within(rules).getAllByRole("link");
    expect(links.length).toBeGreaterThanOrEqual(Object.keys(registry.rules).length);
    expect(rules).toHaveTextContent(`checked ${registry.rules.salary_90.source.checked_on}`);
  });

  it("lists the exempt, banned and partly banned codes with their Swedish titles", () => {
    setup();
    const lists = screen.getByRole("region", { name: /codes with their own rules/i });
    const blocks = within(lists).getAllByRole("list");
    Object.values(registry.code_lists).forEach((cl, i) => {
      const items = within(blocks[i]).getAllByRole("listitem").map((li) => li.textContent);
      expect(items).toEqual(Object.entries(cl.codes).map(([code, title]) => `${code} ${title}`));
    });
  });

  it("lists the personal exemptions and the statements", () => {
    setup();
    const exemptions = screen.getByRole("region", { name: /personal exemptions/i });
    for (const x of Object.values(registry.exemptions)) expect(exemptions).toHaveTextContent(x.label);
    for (const st of Object.values(registry.statements)) expect(screen.getByText(st.text)).toBeInTheDocument();
  });

  it("shows the timeline in date order, as the API gives it", async () => {
    setup();
    const list = await screen.findByRole("list", { name: /timeline/i });
    const items = await within(list).findAllByRole("listitem");
    expect(items).toHaveLength(timeline.length);
    expect(items[0]).toHaveTextContent(timeline[0].summary);
    expect(items.at(-1)).toHaveTextContent(timeline.at(-1)!.summary);
  });

  it("checks an offer for a code and shows the answer, with the part-time warning and disclaimer", async () => {
    const { seen, onApplied } = setup();
    await userEvent.clear(screen.getByLabelText(/^ssyk code/i));
    await userEvent.type(screen.getByLabelText(/^ssyk code/i), "2512");
    await userEvent.type(screen.getByLabelText(/monthly salary/i), "26000");
    await userEvent.clear(screen.getByLabelText(/share of full time/i));
    await userEvent.type(screen.getByLabelText(/share of full time/i), "50");
    await userEvent.click(screen.getByRole("button", { name: /check this offer/i }));
    const result = await screen.findByRole("region", { name: /result/i });
    expect(seen.at(-1)?.body).toMatchObject({ code: "2512", monthly_salary_sek: 26000, fte_percent: 50 });
    expect(result).toHaveTextContent(partTime.warnings[0].message);
    expect(result).toHaveTextContent(partTime.disclaimer);
    expect(onApplied).toHaveBeenCalled();
  });

  it("shows any warning the API gives, such as a stale median", async () => {
    const stale = { ...partTime, warnings: [{ ...partTime.warnings[0], kind: "stale_median" as const,
      message: "A new SCB median may have been published." }] };
    setup({ status: 200, body: stale });
    await userEvent.type(screen.getByLabelText(/^ssyk code/i), "2512");
    await userEvent.click(screen.getByRole("button", { name: /check this offer/i }));
    expect(await screen.findByText(/A new SCB median may have been published/)).toBeInTheDocument();
  });

  it("says that it is information, not legal advice", () => {
    setup();
    expect(screen.getAllByText(/information, not legal advice/i).length).toBeGreaterThan(0);
  });
});
