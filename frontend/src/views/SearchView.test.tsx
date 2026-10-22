import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { SearchAnswer } from "../api/client";
import { initial } from "../lib/selection";
import { fixture, serve } from "../test/fakeApi";
import { SearchView } from "./SearchView";

const FAST = fixture("search-title-fast").body as SearchAnswer;
const FULL = fixture("search-title-full").body as SearchAnswer;

function setup(full: SearchAnswer = FULL) {
  const seen = serve({
    "POST /api/v1/search": (body) => ({ status: 200, body: (body as { mode: string }).mode === "full" ? full : FAST }),
  });
  const dispatch = vi.fn();
  render(<SearchView selection={initial()} dispatch={dispatch} age={null} setAge={() => {}} />);
  return { seen, dispatch };
}

describe("SearchView", () => {
  it("shows fast results while typing, then the accurate ones after a pause", async () => {
    const { seen } = setup();
    await userEvent.type(screen.getByRole("textbox", { name: /job title or ad/i }), "backend developer");
    expect(await screen.findByText(/accurate results/i, {}, { timeout: 3000 })).toBeInTheDocument();
    expect(seen.filter((r) => (r.body as { mode: string }).mode === "fast").length).toBeGreaterThan(1);
    expect(seen.filter((r) => (r.body as { mode: string }).mode === "full")).toHaveLength(1);
    const first = screen.getAllByRole("article")[0];
    expect(first).toHaveAccessibleName(`${FULL.hits[0].code} ${FULL.hits[0].title_en}`);
  });

  it("says why the accurate search did not run", async () => {
    setup({ ...FAST, fallback_reason: "harrier failed to load: out of memory" });
    await userEvent.type(screen.getByRole("textbox", { name: /job title or ad/i }), "backend");
    expect(await screen.findByText(/harrier failed to load: out of memory/, {}, { timeout: 3000 })).toBeInTheDocument();
  });

  it("adds a selected result to the chart", async () => {
    const { dispatch } = setup();
    await userEvent.type(screen.getByRole("textbox", { name: /job title or ad/i }), "backend");
    const first = (await screen.findAllByRole("article"))[0];
    await userEvent.click(within(first).getByRole("button", { name: /add .* to chart/i }));
    expect(dispatch).toHaveBeenCalledWith({ type: "add", code: expect.stringMatching(/^\d{4}$/) });
  });
});

describe("SearchView chart", () => {
  function withSelection(codes: string[], age: "25-34" | null = null) {
    const seen = serve({
      "GET /api/v1/occupations/2512/salary": fixture("salary-2512"),
      "GET /api/v1/occupations/2512/salary?age_band=25-34": fixture("salary-2512-age"),
      "GET /api/v1/occupations/3511/salary": fixture("salary-3511-exempt"),
    });
    const dispatch = vi.fn();
    const selection = { ...initial(), codes };
    const view = render(<SearchView selection={selection} dispatch={dispatch} age={age} setAge={() => {}} />);
    return { seen, dispatch, view, selection };
  }

  it("fetches each selected code's salary, with the age band when one is chosen", async () => {
    const { seen, dispatch } = withSelection(["2512", "3511"], "25-34");
    await vi.waitFor(() => expect(dispatch).toHaveBeenCalledTimes(2));
    expect(seen.map((r) => r.url.pathname + r.url.search).sort()).toEqual([
      "/api/v1/occupations/2512/salary?age_band=25-34", "/api/v1/occupations/3511/salary?age_band=25-34"]);
    expect(dispatch).toHaveBeenCalledWith(expect.objectContaining({ type: "payload", code: "2512" }));
  });

  it("removes a code from its chip and toggles its simulated bar", async () => {
    const { dispatch, view } = withSelection(["2512"], "25-34");
    await userEvent.click(screen.getByRole("button", { name: "Remove 2512" }));
    expect(dispatch).toHaveBeenCalledWith({ type: "remove", code: "2512" });
    view.rerender(<SearchView selection={{ ...initial(), codes: ["2512"], payloads: {
      2512: fixture("salary-2512-age").body as never } }} dispatch={dispatch} age="25-34" setAge={() => {}} />);
    await userEvent.click(screen.getByRole("checkbox", { name: /simulated bar for 2512/i }));
    expect(dispatch).toHaveBeenCalledWith({ type: "simulated", code: "2512" });
  });
});
