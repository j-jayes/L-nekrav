import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { fixture, serve, type Fixture } from "../test/fakeApi";
import { MarketPanel } from "./MarketPanel";

type Answer = { live: { ads: number; positions: number; counties: { name: string; ads: number }[];
  no_county: number }; history: { year: number; ads: number }[]; notice: string };
const m2512 = fixture("market-2512").body as Answer;
const FLOOR = 31000; // a sample amount; the panel only displays what it is given

function setup(f: Fixture, code = "2512") {
  serve({ [`GET /api/v1/occupations/${code}/market`]: f });
  render(<MarketPanel code={code} floor={FLOOR} />);
}

const squash = (t: string | null | undefined) => t?.replace(/\s/g, "");

describe("MarketPanel", () => {
  it("shows open ads, positions, the top five counties and the rest folded away", async () => {
    setup(fixture("market-2512"));
    const open = await screen.findByRole("region", { name: "Open now" });
    expect(squash(open.textContent)).toContain(squash(`${m2512.live.ads.toLocaleString("sv-SE")} open ads`));
    expect(squash(open.textContent)).toContain(squash(`${m2512.live.positions.toLocaleString("sv-SE")} positions`));
    const top = within(open).getByRole("list", { name: "Top counties" });
    expect(within(top).getAllByRole("listitem")).toHaveLength(5);
    expect(within(top).getAllByRole("listitem")[0].textContent).toContain(m2512.live.counties[0].name);
    // the live counts change with every recording: read them from the fixture
    expect(within(open).getByText(`${m2512.live.counties.length - 5} more counties`)).toBeInTheDocument();
    expect(within(open).getByText(new RegExp(`no county given: ${m2512.live.no_county}`, "i"))).toBeInTheDocument();
    expect(within(open).getByRole("link", { name: /JobSearch/ })).toHaveAttribute("href", expect.stringContaining("occupation-group="));
    expect(open.textContent).toMatch(/fetched \d{4}-\d{2}-\d{2} \d{2}:\d{2}/);
  });

  it("names the codes that share a count", async () => {
    setup(fixture("market-1211"), "1211");
    const open = await screen.findByRole("region", { name: "Open now" });
    expect(open.textContent).toMatch(/Shared with 1212: JobTech counts these codes together/);
  });

  it("shows no number for a code JobTech does not publish", async () => {
    setup(fixture("market-4430"), "4430");
    const open = await screen.findByRole("region", { name: "Open now" });
    expect(open.textContent).toMatch(/JobTech publishes no ads under this code, so there is no count/);
    expect(open.textContent).not.toMatch(/\d/);
    const history = screen.getByRole("region", { name: "Ads per year" });
    expect(history.textContent).toMatch(/no count/);
  });

  it("says the live count is unavailable, with the reason and no number", async () => {
    setup(fixture("market-unavailable"));
    const open = await screen.findByRole("region", { name: "Open now" });
    expect(open.textContent).toMatch(/The live count is unavailable \(connection error\)/);
    expect(open.textContent).not.toMatch(/\d/);
  });

  it("shows regional means beside the national floor, never as a threshold, with suppressed cells", async () => {
    setup(fixture("market-1211"), "1211");
    const pay = await screen.findByRole("region", { name: /Pay by area/ });
    expect(pay.textContent).toMatch(/These are mean salaries/);
    expect(squash(pay.textContent)).toContain(squash(`${FLOOR.toLocaleString("sv-SE")} SEK`));
    expect(pay.textContent).toMatch(/same in every area/);
    const rows = within(within(pay).getByRole("table")).getAllByRole("row");
    expect(rows).toHaveLength(10); // header + Sweden + 8 areas
    expect(rows[1].textContent).toMatch(/^Sweden/);
    expect(rows[2].textContent).toMatch(/Stockholm/);
    expect(rows[3].textContent).toMatch(/not published.*not published/);
    expect(pay.textContent).toMatch(/SCB TAB5696/);
  });

  it("labels a shared count even when the live count is unavailable (US3/AC3)", async () => {
    const f = structuredClone(fixture("market-1211"));
    (f.body as { live: unknown }).live = (fixture("market-unavailable").body as { live: unknown }).live;
    setup(f, "1211");
    const history = await screen.findByRole("region", { name: "Ads per year" });
    expect(history.textContent).toMatch(/Shared with 1212/);
  });

  it("shows when the regional figures were fetched", async () => {
    setup(fixture("market-1211"), "1211");
    const pay = await screen.findByRole("region", { name: /Pay by area/ });
    expect(pay.textContent).toMatch(/fetched \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC/);
  });

  it("gives the range of fetch times when the years were fetched at different times", async () => {
    const f = structuredClone(fixture("market-2512"));
    const h = (f.body as { history: { fetched_at: string }[] }).history;
    h[h.length - 1].fetched_at = "2027-01-03T08:00:00Z";
    setup(f);
    const history = await screen.findByRole("region", { name: "Ads per year" });
    expect(history.textContent).toMatch(/fetched 2026-10-23 \d{2}:\d{2} UTC to 2027-01-03 08:00 UTC/);
  });

  it("draws one bar per year with a table view, and a zero year as 0", async () => {
    const f = structuredClone(fixture("market-2512"));
    (f.body as Answer).history[0].ads = 0;
    setup(f);
    const history = await screen.findByRole("region", { name: "Ads per year" });
    expect(within(history).getAllByTestId("year-bar")).toHaveLength(m2512.history.length);
    const table = within(history).getByRole("table");
    const first = within(table).getAllByRole("row")[1];
    expect(first.textContent).toBe(`${m2512.history[0].year}0`);
    expect(history.textContent).toMatch(/Platsbanken/);
  });

  it("shows the notice, and an error if its own request fails", async () => {
    setup(fixture("market-2512"));
    expect(await screen.findByText(m2512.notice)).toBeInTheDocument();
  });

  it("says when the market could not be loaded", async () => {
    setup({ status: 500, body: { detail: "internal error" } });
    expect(await screen.findByRole("alert")).toHaveTextContent(/market data could not be loaded/i);
  });
});
