import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { MapAnswer } from "../api/client";
import { fixture, serve } from "../test/fakeApi";
import { OccupationMap } from "./OccupationMap";

const map = fixture("map").body as MapAnswer;
const point = (code: string) => map.points.find((p) => p.code === code)!;

function setup(props: { hits?: string[]; selected?: string[] } = {}) {
  serve({
    "GET /api/v1/closeness?a=2511&b=2512": fixture("closeness-2511-2512"),
    "GET /api/v1/closeness?a=1311&b=1312": fixture("closeness-1311-1312"),
  });
  const onSelect = vi.fn();
  render(<OccupationMap map={map} hits={props.hits ?? []} selected={props.selected ?? []} onSelect={onSelect} />);
  return { onSelect };
}

describe("OccupationMap", () => {
  it("draws one point per code; the major group is read per point, not painted on the map", () => {
    setup({ hits: ["2512"] });
    expect(screen.getAllByTestId("point")).toHaveLength(map.points.length);
    expect(screen.queryAllByTestId("group-label")).toHaveLength(0); // groups are skill levels, not regions
    fireEvent.focus(screen.getByRole("button", { name: /^2512 / }));
    expect(screen.getByRole("status")).toHaveTextContent(map.major_groups["2"].en);
  });

  it("frames the selected codes and their neighbours on request", async () => {
    setup({ selected: ["2511"] });
    await userEvent.click(screen.getByRole("button", { name: "Zoom to the selected codes" }));
    expect(screen.getByTestId("zoom-layer").getAttribute("transform")).not.toBe("translate(0 0) scale(1)");
  });

  it("labels the selected codes and the search results, not every neighbour", () => {
    setup({ hits: ["2519"], selected: ["2511"] });
    const labels = screen.getAllByTestId("point-label").map((l) => l.textContent);
    expect(labels.sort()).toEqual(["2511", "2519"]);
  });

  it("never colours by pay: every point outside the codes in play looks the same", () => {
    setup({ hits: ["2511"] });
    const fills = new Set(screen.getAllByTestId("point").map((p) => p.getAttribute("fill")));
    expect(fills.size).toBe(1);
  });

  it("outlines the search hits and fills the selected codes, with lines to five neighbours", () => {
    setup({ hits: ["2511", "2512", "2519"], selected: ["2511"] });
    expect(screen.getAllByTestId("hit")).toHaveLength(2); // 2511 is drawn as selected, not as a hit
    expect(screen.getAllByTestId("selected")).toHaveLength(1);
    const links = screen.getAllByTestId("link");
    expect(links.map((l) => l.getAttribute("data-to"))).toEqual(point("2511").neighbours.slice(0, 5).map((n) => n.code));
  });

  it("shows a point's titles, median and closeness to the selected code", async () => {
    setup({ hits: ["2512"], selected: ["2511"] });
    fireEvent.focus(screen.getByRole("button", { name: /^2512 / }));
    const tip = screen.getByRole("status");
    expect(tip).toHaveTextContent(point("2512").title_en!);
    expect(tip).toHaveTextContent(new RegExp(`Median ${point("2512").median_sek!.toLocaleString("sv-SE")}`.replace(/\s/g, "\\s")));
    expect(await within(tip).findByText(/Closer to 2511 than 99 % of pairs/)).toBeInTheDocument();
  });

  it("lists every code at a stacked spot, and says when two codes share a description", async () => {
    setup({ hits: ["1312"], selected: ["1311"] });
    fireEvent.focus(screen.getByRole("button", { name: /^1312 / }));
    const tip = screen.getByRole("status");
    expect(tip).toHaveTextContent("1311");
    expect(tip).toHaveTextContent("1312");
    expect(await within(tip).findByText(/Same official description as 1311/)).toBeInTheDocument();
  });

  it("selects a code from the keyboard", async () => {
    const { onSelect } = setup({ hits: ["2512"] });
    screen.getByRole("button", { name: /^2512 / }).focus();
    await userEvent.keyboard("{Enter}");
    expect(onSelect).toHaveBeenCalledWith("2512");
  });

  it("zooms with buttons and resets", async () => {
    setup();
    const layer = screen.getByTestId("zoom-layer");
    await userEvent.click(screen.getByRole("button", { name: "Zoom in" }));
    expect(layer.getAttribute("transform")).toMatch(/scale\(1\.5/);
    await userEvent.click(screen.getByRole("button", { name: "Reset the view" }));
    expect(layer.getAttribute("transform")).toBe("translate(0 0) scale(1)");
  });

  it("offers the same codes as a table, and says what distances mean", () => {
    setup();
    const table = screen.getByRole("table", { name: /occupations and their nearest/i });
    expect(within(table).getAllByRole("row")).toHaveLength(map.points.length + 1);
    expect(screen.getByText(/distances on the map are approximate/i)).toBeInTheDocument();
    expect(screen.getByText(/the duties do/i)).toBeInTheDocument();
  });
});
