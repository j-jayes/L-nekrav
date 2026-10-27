import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";
import { fixture, serve } from "./test/fakeApi";

const at = (search: string) => history.replaceState(null, "", `/${search}`);

describe("App", () => {
  afterEach(() => at(""));

  it("opens the view named in the address", async () => {
    serve({});
    at("?view=legal");
    render(<App />);
    expect(await screen.findByRole("heading", { name: "The salary requirement" })).toBeInTheDocument();
  });

  it("drops an unknown code from a link and says so, keeping the known one", async () => {
    serve({
      "GET /api/v1/occupations/2512": fixture("occupation-2512"),
      "GET /api/v1/occupations/9999": fixture("occupation-9999"),
    });
    at("?view=compare&codes=2512,9999");
    render(<App />);
    expect(await screen.findByText(/Not selected from the link: 9999/)).toBeInTheDocument();
    expect(location.search).toBe("?view=number&codes=2512"); // an old compare link opens Your number
  });

  it("at phone width the open drawer is modal: focus moves in, the page is inert, Escape returns", async () => {  // Copilot on PR #4
    serve({});
    at("");
    render(<App />);
    const button = await screen.findByRole("button", { name: "Ask the advisor" });
    await userEvent.click(button);
    const drawer = screen.getByRole("dialog", { name: "Advisor" });
    await waitFor(() => expect(drawer).toContainElement(document.activeElement as HTMLElement));
    expect(document.querySelector("[data-page]")).toHaveAttribute("inert");
    await userEvent.keyboard("{Escape}");
    expect(document.querySelector("[data-page]")).not.toHaveAttribute("inert");
    expect(button).toHaveFocus();
  });

  it("shows the views as three numbered steps (006 FR-016)", async () => {
    serve({});
    at("");
    render(<App />);
    const nav = await screen.findByRole("navigation", { name: "Steps" });
    expect([...nav.querySelectorAll("button")].map((b) => b.textContent)).toEqual(
      ["1 Find your code", "2 Your number", "3 The rules"]);
  });

  it("writes the view to the address", async () => {
    serve({});
    at("");
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "2 Your number" }));
    expect(await screen.findByRole("heading", { name: "Your number" })).toBeInTheDocument();
    expect(location.search).toBe("?view=number");
  });

  it("ends Your number with a step on to the rules", async () => {
    serve({});
    at("?view=number");
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: /next: the rules/i }));
    expect(await screen.findByRole("heading", { name: "The salary requirement" })).toBeInTheDocument();
  });
});
