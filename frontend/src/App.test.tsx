import { render, screen } from "@testing-library/react";
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
    expect(location.search).toBe("?view=compare&codes=2512");
  });

  it("writes the view to the address", async () => {
    serve({});
    at("");
    render(<App />);
    (await screen.findByRole("button", { name: "Compare" })).click();
    expect(await screen.findByRole("heading", { name: "Compare codes" })).toBeInTheDocument();
    expect(location.search).toBe("?view=compare");
  });
});
