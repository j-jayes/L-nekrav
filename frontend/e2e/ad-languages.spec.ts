// An English job ad and its Swedish translation give the same top three codes (SC-003), and the
// timings behind SC-001 and SC-002 are measured on the way. The ads are read from AD_EN and
// AD_SV (files kept out of the repository); the results are printed for references/web-client-e2e.md.
import fs from "node:fs";
import { expect, type Page, test } from "@playwright/test";

const status = (p: Page) => p.locator("[aria-live=polite]").first();

async function topThree(page: Page, text: string) {
  const box = page.getByRole("textbox", { name: /job title or ad/i });
  await box.fill("");
  const t0 = Date.now();
  await box.fill(text);
  await expect(status(page)).toHaveText(/^Accurate results(?!.*refining)/, { timeout: 30_000 });
  const accurateMs = Date.now() - t0;
  const codes = await page.getByRole("article").evaluateAll((as) => as.slice(0, 3).map((a) => a.getAttribute("aria-label")!.slice(0, 4)));
  return { codes, accurateMs };
}

test("English and Swedish ads give the same top three codes", async ({ page }, info) => {
  test.skip(!process.env.AD_EN || !process.env.AD_SV, "set AD_EN and AD_SV to the two ad files");
  test.skip(info.project.name !== "desktop", "one run is enough");
  await page.goto("/?view=search");
  const box = page.getByRole("textbox", { name: /job title or ad/i });

  // SC-001: from each keystroke until the list on screen is the answer for the text in the box.
  const keystrokes: number[] = [];
  for (const ch of "intensive care nurse") {
    const t0 = Date.now();
    await box.press(ch === " " ? "Space" : ch);
    await page.waitForFunction(() => {
      const box = document.querySelector<HTMLTextAreaElement>("#q");
      return document.querySelector("[data-answer-for]")?.getAttribute("data-answer-for") === box?.value;
    }, null, { timeout: 5_000 });
    keystrokes.push(Date.now() - t0);
  }
  await page.waitForTimeout(1000);

  const en = await topThree(page, fs.readFileSync(process.env.AD_EN!, "utf8"));
  const sv = await topThree(page, fs.readFileSync(process.env.AD_SV!, "utf8"));
  console.log(JSON.stringify({ en, sv, keystrokeMsMax: Math.max(...keystrokes), keystrokeMsMedian: keystrokes.sort((a, b) => a - b)[keystrokes.length >> 1] }));
  expect([...sv.codes].sort()).toEqual([...en.codes].sort());
});
