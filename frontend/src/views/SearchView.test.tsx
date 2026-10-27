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
  render(<SearchView selection={initial()} dispatch={dispatch} onNext={() => {}} />);
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

describe("SearchView result cards", () => {
  it("keeps how each method ranked a code one step away (006 FR-020)", async () => {
    setup();
    await userEvent.type(screen.getByRole("textbox", { name: /job title or ad/i }), "backend");
    const first = (await screen.findAllByRole("article"))[0];
    const how = within(first).getByText("How this was matched").closest("details")!;
    expect(how).not.toHaveAttribute("open");
    expect(within(how).getByText(/Swedish model/)).toBeInTheDocument();
  });
});

describe("SearchView selection", () => {
  function withSelection(codes: string[]) {
    const seen = serve({});
    const dispatch = vi.fn();
    const onNext = vi.fn();
    render(<SearchView selection={{ ...initial(), codes }} dispatch={dispatch} onNext={onNext} />);
    return { seen, dispatch, onNext };
  }

  it("lists the selected codes with a way to remove each, and no chart (it moved to step 2)", async () => {
    const { dispatch, seen } = withSelection(["2512", "3511"]);
    await userEvent.click(screen.getByRole("button", { name: "Remove 2512" }));
    expect(dispatch).toHaveBeenCalledWith({ type: "remove", code: "2512" });
    expect(screen.queryByRole("figure")).toBeNull();
    expect(seen.filter((r) => r.url.pathname.endsWith("/salary"))).toHaveLength(0);
  });

  it("goes on to Your number, but only once a code is selected", async () => {
    const { onNext } = withSelection(["2512"]);
    await userEvent.click(screen.getByRole("button", { name: /next: your number/i }));
    expect(onNext).toHaveBeenCalled();
  });

  it("cannot go on with nothing selected", () => {
    withSelection([]);
    expect(screen.getByRole("button", { name: /next: your number/i })).toBeDisabled();
  });
});
