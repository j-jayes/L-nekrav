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
      await expect(p.getByRole("group", { name: /^3511 / })).toBeVisible();
    },
  },
  {
    name: "compare",
    url: "/?view=compare&codes=2512,2511,3511",
    ready: async (p) => {
      await expect(p.getByRole("article")).toHaveCount(3);
      for (const code of ["2512", "2511", "3511"]) // Feature 005: each column's market panel
        await expect(p.getByRole("region", { name: `Market for ${code}` }).getByRole("region", { name: "Ads per year" })).toBeVisible();
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
