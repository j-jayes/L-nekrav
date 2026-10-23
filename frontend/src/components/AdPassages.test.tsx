import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import type { SearchAnswer } from "../api/client";
import { fixture } from "../test/fakeApi";
import { AdPassages } from "./AdPassages";

const answer = fixture("search-ad-full").body as SearchAnswer;

it("marks each passage kept or set aside, with the reason in words", () => {
  render(<AdPassages answer={answer} />);
  const kept = screen.getByRole("list", { name: /read by the search/i });
  const aside = screen.getByRole("list", { name: /set aside/i });
  expect(kept).toHaveTextContent("Design, build and maintain the REST APIs");
  expect(kept).toHaveTextContent("under a duties heading");
  expect(kept).toHaveTextContent("first line, read as the job title");
  expect(aside).toHaveTextContent("Hybrid work with three office days a week");
  expect(aside).toHaveTextContent("under a benefits heading");
});

it("shows the text the search used", () => {
  render(<AdPassages answer={answer} />);
  expect(screen.getByText(/text the search used/i).closest("details")).toHaveTextContent(
    answer.searched_text.replace(/\s+/g, " ").slice(0, 40));
});

it("shows nothing for a search without ad parsing", () => {
  const { container } = render(<AdPassages answer={fixture("search-title-fast").body as SearchAnswer} />);
  expect(container).toBeEmptyDOMElement();
});
