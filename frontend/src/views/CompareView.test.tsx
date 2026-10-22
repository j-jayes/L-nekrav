import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Comparison, Offer } from "../api/client";
import { fixture, serve } from "../test/fakeApi";
import { CompareView } from "./CompareView";

const withOffer = fixture("compare-offer").body as Comparison;
const OFFER = { monthly_salary_sek: 30000, fte_percent: 100, application_type: "first_permit",
  filed_on: "2026-10-01", decided_on: "2026-10-22" } as Offer;

function setup(codes: string[], offer: Offer | null) {
  const seen = serve({ "POST /api/v1/compare": (body) =>
    (body as { offer?: unknown }).offer ? fixture("compare-offer") : fixture("compare-2512-2511") });
  const toSearch = vi.fn();
  render(<CompareView codes={codes} offer={offer} onSearch={toSearch} />);
  return { seen, toSearch };
}

describe("CompareView", () => {
  it("shows one column per code, in the order selected, with its official task text and source", async () => {
    const { seen } = setup(["2512", "2511", "3511"], OFFER);
    const cols = await screen.findAllByRole("article");
    expect(cols.map((c) => c.getAttribute("aria-label")?.slice(0, 4))).toEqual(["2512", "2511", "3511"]);
    expect(seen[0].body).toEqual({ codes: ["2512", "2511", "3511"], offer: OFFER });
    const first = within(cols[0]);
    expect(first.getByText(withOffer.columns[0].tasks_sv[0].text)).toBeInTheDocument();
    expect(first.getAllByRole("link", { name: /jobtech|esco|scb/i }).length).toBeGreaterThan(0);
    expect(screen.getByText(withOffer.honest_fit)).toBeInTheDocument();
  });

  it("shows each code's threshold, and with an offer whether it passes and by how much", async () => {
    setup(["2512", "2511", "3511"], OFFER);
    const [fail, , pass] = await screen.findAllByRole("article");
    expect(within(fail).getByText(/does not reach/i)).toBeInTheDocument();
    expect(within(pass).getByText(/reaches/i)).toBeInTheDocument();
    expect(within(pass).getByText(/exempt code/i)).toBeInTheDocument();
    const squash = (t: string | null) => t?.replace(/\s/g, "");
    expect(squash(pass.textContent)).toContain(squash(withOffer.columns[2].eligibility!.margin_sek!.toLocaleString("sv-SE")));
  });

  it("styles a passing and a failing code alike apart from the status (FR-012)", async () => {
    setup(["2512", "2511", "3511"], OFFER);
    const [fail, , pass] = await screen.findAllByRole("article");
    expect(pass.className).toBe(fail.className);
  });

  it("works without an offer", async () => {
    setup(["2512", "2511"], null);
    const cols = await screen.findAllByRole("article");
    expect(cols).toHaveLength(2);
    expect(screen.queryByText(/does not reach|reaches/i)).toBeNull();
  });

  it("explains that it needs two codes and links back to search", async () => {
    const { seen, toSearch } = setup(["2512"], null);
    expect(screen.getByText(/at least two codes/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /find codes/i }));
    expect(toSearch).toHaveBeenCalled();
    expect(seen).toHaveLength(0);
  });
});
