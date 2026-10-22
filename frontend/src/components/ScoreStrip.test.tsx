import { render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import type { SearchAnswer } from "../api/client";
import { fixture } from "../test/fakeApi";
import { ScoreStrip } from "./ScoreStrip";

const fast = (fixture("search-title-fast").body as SearchAnswer).hits[0];
const full = (fixture("search-ad-full").body as SearchAnswer).hits[0];

it("shows one rank per method, and a method that did not run as not run", () => {
  render(<ScoreStrip hit={fast} />);
  const strip = screen.getByRole("list", { name: /rank by search method/i });
  const cells = within(strip).getAllByRole("listitem").map((li) => li.textContent);
  expect(cells).toEqual([`Swedish model#${fast.ranks.kblab}`, `Keywords#${fast.ranks.bm25}`, "Accurate modelnot run"]);
});

it("shows the accurate model's rank once it has run", () => {
  render(<ScoreStrip hit={full} />);
  expect(screen.getByText("Accurate model").parentElement).toHaveTextContent(`#${full.ranks.harrier}`);
});
