import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import type { SearchAnswer, SearchHit } from "../api/client";
import { fixture } from "../test/fakeApi";
import { ResultList } from "./ResultList";

const answer = fixture("search-ad-full").body as SearchAnswer;
const exempt: SearchHit = { ...answer.hits[1], legal_flags: (fixture("compare-offer").body as {
  columns: { legal_flags: SearchHit["legal_flags"] }[] }).columns[2].legal_flags };

it("shows code, both titles, the matched passage and the honest-fit notice, in the API's order", () => {
  render(<ResultList answer={answer} selected={[]} onSelect={() => {}} />);
  const items = screen.getAllByRole("article");
  expect(items.map((i) => i.getAttribute("aria-label"))).toEqual(answer.hits.map((h) => `${h.code} ${h.title_en}`));
  const first = within(items[0]);
  expect(first.getByText(answer.hits[0].title_sv)).toBeInTheDocument();
  expect(first.getByText(answer.hits[0].matched_chunk.text.slice(0, 30), { exact: false })).toBeInTheDocument();
  expect(screen.getByText(answer.honest_fit)).toBeInTheDocument();
});

it("shows a legal flag in words, with its source", () => {
  render(<ResultList answer={{ ...answer, hits: [exempt] }} selected={[]} onSelect={() => {}} />);
  const flag = screen.getByText(/exempt code/i).closest("li")!;
  expect(flag).toHaveTextContent(exempt.legal_flags[0].note);
  expect(within(flag).getByRole("link")).toHaveAttribute("href", exempt.legal_flags[0].source.url);
});

it("selects a result, and marks one already selected", async () => {
  const onSelect = vi.fn();
  render(<ResultList answer={answer} selected={[answer.hits[1].code]} onSelect={onSelect} />);
  const [first, second] = screen.getAllByRole("article");
  await userEvent.click(within(first).getByRole("button", { name: /add .* to chart/i }));
  expect(onSelect).toHaveBeenCalledWith(answer.hits[0].code);
  expect(within(second).getByRole("button", { name: /on chart/i })).toBeDisabled();
});
