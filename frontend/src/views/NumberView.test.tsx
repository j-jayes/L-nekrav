import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useReducer, useState } from "react";
import { describe, expect, it, vi } from "vitest";
import type { Comparison, MarketAnswer, Registry } from "../api/client";
import { emptyDraft } from "../lib/offer";
import { initial, select } from "../lib/selection";
import type { AgeBand, Region } from "../lib/urlState";
import { type Fixture, fixture, serve } from "../test/fakeApi";
import { NumberView } from "./NumberView";

const rules = (fixture("registry").body as Registry).rules;
const three = fixture("compare-2512-2511-2519").body as Comparison;
const notice = (fixture("market-2512").body as MarketAnswer).notice;
const squash = (t: string | null | undefined) => t?.replace(/\s/g, "");

/** Real recorded answers, picked by what the page asks for. */
function routes() {
  const compare = (body: unknown): Fixture => {
    const codes = (body as { codes: string[] }).codes;
    if (codes.length === 1) return codes[0] === "3155" ? fixture("compare-3155") : fixture("compare-2512");
    return { status: 200, body: { ...three, columns: codes.map((c) => three.columns.find((col) => col.code === c)).filter(Boolean) } };
  };
  const salary = (_: unknown, url: URL): Fixture => {
    const code = url.pathname.split("/")[4];
    const adjusted = url.searchParams.has("age_band") || url.searchParams.has("region");
    if (code === "2111") return fixture("salary-2111-region-left-out");
    if (code === "3155") return fixture("salary-3155");
    if (code === "1111") return fixture("salary-1111-no-estimate");
    return fixture(adjusted ? `salary-${code}-age-region` : code === "2511" ? "salary-2511" : "salary-2512");
  };
  const eligibility = (body: unknown): Fixture => {
    const { code, monthly_salary_sek: n } = body as { code: string; monthly_salary_sek: number };
    if (code === "3155") return fixture("eligibility-3155-p25-missing");
    return fixture(n === 60000 ? `eligibility-${code}-60000` : `eligibility-${code === "2512" ? "pass" : code}`);
  };
  return {
    "POST /api/v1/compare": compare,
    "POST /api/v1/eligibility": eligibility,
    ...Object.fromEntries(["2511", "2512", "2519", "2111", "3155", "1111"].flatMap((c) => [
      [`GET /api/v1/occupations/${c}/salary`, salary],
      [`GET /api/v1/occupations/${c}/market`, fixture("market-2512")],
    ])),
  };
}

function Harness({ codes, age = null, region = null, number = "", onSearch = () => {} }: {
  codes: string[]; age?: AgeBand | null; region?: Region | null; number?: string; onSearch?: () => void }) {
  const [selection, dispatch] = useReducer(select, undefined, () => select(initial(), { type: "load", codes, dropped: [] }));
  const [a, setAge] = useState(age);
  const [r, setRegion] = useState(region);
  const [draft, setDraft] = useState({ ...emptyDraft(), monthly_salary_sek: number });
  return <NumberView selection={selection} dispatch={dispatch} age={a} setAge={setAge} region={r} setRegion={setRegion}
    draft={draft} setDraft={setDraft} onSearch={onSearch} rules={rules} exemptions={[]} />;
}

const cards = () => screen.findAllByRole("article");
const card = async (code: string) => (await cards()).find((c) => c.getAttribute("aria-label")?.startsWith(code))!;

describe("NumberView", () => {
  it("leads each code with SCB's published middle half and median", async () => {
    serve(routes());
    render(<Harness codes={["2511"]} />);
    const c = await card("2511");
    expect(squash((await within(c).findByTestId("headline")).textContent))
      .toBe(squash("SCB 2025: the middle half earn 47 700–66 700 SEK; median 56 200 SEK."));
  });

  it("places the candidate's number between published percentiles, never between invented ones", async () => {
    serve(routes());
    render(<Harness codes={["2511"]} number="60000" />);
    const c = await card("2511");
    expect(await within(c).findByText(/is between the median \(56\s200 SEK\) and the 75th percentile \(66\s700 SEK\)/)).toBeInTheDocument();
  });

  it("names a figure SCB does not publish instead of filling the gap", async () => {
    serve(routes());
    render(<Harness codes={["3155"]} number="45000" />);
    const c = await card("3155");
    expect(await within(c).findByText(/between the 10th percentile .* and the median/)).toBeInTheDocument();
    expect(within(c).getByText(/SCB publishes no 25th percentile for this code/)).toBeInTheDocument();
  });

  it("shows the estimate for the age band and area, marked as not an SCB figure", async () => {
    serve(routes());
    render(<Harness codes={["2511"]} age="25-34" region="SE11" />);
    const c = await card("2511");
    const chip = await within(c).findByTestId("estimate-chip");
    expect(chip).toHaveTextContent(/Estimate for ages 25-34 in Stockholm/);
    expect(squash(chip.textContent)).toContain(squash("44 711–62 520 SEK"));
    expect(chip).toHaveTextContent(/not an SCB figure/);
  });

  it("says which adjustment was left out, and why", async () => {
    serve(routes());
    render(<Harness codes={["2111"]} age="25-34" region="SE33" />);
    const chip = await within(await card("2111")).findByTestId("estimate-chip");
    expect(chip).toHaveTextContent(/Not adjusted for area: SCB publishes no mean for Upper Norrland in 2025/);
  });

  it("says why there is no estimate", async () => {
    serve(routes());
    render(<Harness codes={["1111"]} age="25-34" region="SE11" />);
    expect(await within(await card("1111")).findByText(/No estimate: SCB publishes neither P25 nor P75/)).toBeInTheDocument();
  });

  it("checks the number against the floor, with the floor's legal source", async () => {
    serve(routes());
    render(<Harness codes={["2511"]} number="60000" />);
    const c = await card("2511");
    expect(await within(c).findByText(/reaches the salary floor/)).toBeInTheDocument();
    expect(within(c).getByRole("link", { name: /Migrationsverket/ })).toHaveAttribute("href", rules.salary_90.source.url);
  });

  it("shows the honest-fit statement and the market notice once, whatever the number of codes", async () => {
    serve(routes());
    render(<Harness codes={["2512", "2511", "2519"]} number="60000" />);
    expect(await cards()).toHaveLength(3);
    expect(await screen.findAllByText(three.honest_fit)).toHaveLength(1);
    expect(await screen.findAllByText(notice)).toHaveLength(1);
  });

  it("keeps the cards in the order selected, never ranked by pay", async () => {
    serve(routes());
    render(<Harness codes={["2519", "2511", "2512"]} />);
    await screen.findAllByTestId("headline");
    expect((await cards()).map((c) => c.getAttribute("aria-label")?.slice(0, 4))).toEqual(["2519", "2511", "2512"]);
  });

  it("works with a single code", async () => {
    const seen = serve(routes());
    render(<Harness codes={["2512"]} />);
    expect(await cards()).toHaveLength(1);
    expect(seen.find((r) => r.url.pathname === "/api/v1/compare")?.body).toEqual({ codes: ["2512"] });
  });

  it("keeps the tasks and the market one click away", async () => {
    serve(routes());
    render(<Harness codes={["2512"]} />);
    const c = await card("2512");
    expect(within(c).getByText("What the work is").closest("details")).not.toHaveAttribute("open");
    expect(within(c).getByText("Market").closest("details")).not.toHaveAttribute("open");
  });

  it("says why an invalid number gives no position, and still shows the code", async () => {
    serve(routes());
    render(<Harness codes={["2511"]} />);
    await userEvent.type(screen.getByLabelText(/your number/i), "abc");
    expect(screen.getByText(/whole number of SEK a month/i)).toBeInTheDocument();
    expect(await within(await card("2511")).findByTestId("headline")).toBeInTheDocument();
    expect(screen.queryByText(/is between/)).toBeNull();
  });

  it("asks for a code first when none is selected", async () => {
    serve(routes());
    const onSearch = vi.fn();
    render(<Harness codes={[]} onSearch={onSearch} />);
    await userEvent.click(screen.getByRole("button", { name: /pick the code that matches your duties/i }));
    expect(onSearch).toHaveBeenCalled();
  });
});

describe("NumberView payloads", () => {
  it("fetches a code's figures again when it is removed and added back", async () => {
    const seen = serve(routes());
    function Again() {
      const [selection, dispatch] = useReducer(select, undefined, () => select(initial(), { type: "load", codes: ["2512"], dropped: [] }));
      const [draft, setDraft] = useState(emptyDraft());
      return (<>
        <button type="button" onClick={() => dispatch({ type: "add", code: "2512" })}>re-add</button>
        <NumberView selection={selection} dispatch={dispatch} age={null} setAge={() => {}} region={null}
          setRegion={() => {}} draft={draft} setDraft={setDraft} onSearch={() => {}} rules={rules} exemptions={[]} />
      </>);
    }
    render(<Again />);
    await screen.findByTestId("headline");
    await userEvent.click(screen.getByRole("button", { name: "Remove 2512" }));
    await userEvent.click(screen.getByRole("button", { name: "re-add" }));
    expect(await screen.findByTestId("headline")).toBeInTheDocument();
    expect(seen.filter((r) => r.url.pathname.endsWith("/2512/salary"))).toHaveLength(2);
  });
});
