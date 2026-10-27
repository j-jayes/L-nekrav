// The three main views at phone and desktop width (SC-005, SC-009): a screenshot of each for the
// record, no sideways scroll, and no serious or critical axe violations.
import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

const SHOTS = "../references/web-client-screenshots";

const VIEWS: { name: string; url: string; ready: (p: Page) => Promise<void> }[] = [
  {
    name: "search",
    url: "/?view=search&codes=2512,3511",
    ready: async (p) => {
      await p.getByRole("textbox", { name: /job title or ad/i }).fill("backend developer");
      await expect(p.getByText(/^Accurate results/)).toBeVisible({ timeout: 60_000 }); // a cold container loads Harrier (~17 s)
      await expect(p.getByRole("button", { name: "Remove 3511" })).toBeVisible();
      // 007: the map, beside the results on a wide screen and folded away on a phone
      const fold = p.getByText("Map of similar occupations", { exact: true });
      if (await fold.isVisible()) await fold.click();
      await expect(p.getByRole("group", { name: /Map of occupations/ })).toBeVisible();
      await expect(p.getByTestId("selected")).toHaveCount(2);
    },
  },
  {
    name: "number", // 006: replaces the compare view
    url: "/?view=number&codes=2511,2512,2519&age=25-34&region=SE11",
    ready: async (p) => {
      await p.getByRole("textbox", { name: /your number/i }).fill("60000");
      await expect(p.getByRole("article")).toHaveCount(3);
      await expect(p.getByText(/is between the median/).first()).toBeVisible();
      await expect(p.getByTestId("estimate-chip").first()).toBeVisible();
      await expect(p.getByText(/reaches the salary floor/).first()).toBeVisible();
    },
  },
  {
    name: "legal",
    url: "/?view=legal",
    ready: async (p) => { await expect(p.getByRole("list", { name: "Timeline" }).getByRole("listitem").first()).toBeVisible(); },
  },
];

for (const v of VIEWS) {
  test(`${v.name} view`, async ({ page }, info) => {
    await page.goto(v.url);
    await v.ready(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
    const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    const serious = violations.filter((x) => x.impact === "serious" || x.impact === "critical");
    expect(serious.map((x) => `${x.id}: ${x.nodes.length} × ${x.help}`)).toEqual([]);
    await page.screenshot({ path: `${SHOTS}/${v.name}-${info.project.name}.png`, fullPage: true });
  });
}

// SC-001: on a phone, the first card's position, estimate and floor check need no scrolling.
test("your number above the fold", async ({ page }, info) => {
  test.skip(info.project.name !== "phone", "phone only");
  await page.goto("/?view=number&codes=2511,2512,2519&age=25-34&region=SE11");
  await page.getByRole("textbox", { name: /your number/i }).fill("60000");
  const first = page.getByRole("article").first();
  for (const el of [first.getByText(/is between the median/), first.getByTestId("estimate-chip"),
    first.getByText(/reaches the salary floor/)]) {
    await expect(el).toBeVisible();
    const box = (await el.boundingBox())!;
    expect(box.y + box.height).toBeLessThanOrEqual(page.viewportSize()!.height);
  }
});
