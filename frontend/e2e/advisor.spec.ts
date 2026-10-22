// The advisor drawer selects codes on the chart while it works (SC-008). Run against
// scripts/serve_fake_advisor.py, whose scripted model looks up 2512 and compares 2512 and 2511.
import { expect, test } from "@playwright/test";

test("the chart follows the advisor before its memo arrives", async ({ page }) => {
  await page.goto("/?view=search");
  await page.getByRole("button", { name: "Ask the advisor" }).click();
  const drawer = page.locator('aside[aria-label="Advisor"]'); // a dialog on a phone, a side panel on desktop
  await expect(drawer).toContainText("third-party language model");
  await drawer.getByLabel("Job ad").fill("Backend Developer (Python)\n\nYou will build and maintain our APIs.");
  await drawer.getByRole("button", { name: "Ask" }).click();

  const chart = page.getByRole("region", { name: "Salary chart" });
  await expect(chart.getByRole("group", { name: /^2512 / })).toBeVisible();
  await expect(drawer.getByRole("region", { name: "Memo" })).toHaveCount(0); // the chart moved first
  await expect(chart.getByRole("group", { name: /^2511 / })).toBeVisible();
  await expect(drawer.getByRole("region", { name: "Memo" })).toContainText("Code 2512 fits the duties");
  await expect(drawer.getByRole("region", { name: "Memo" })).toContainText("third-party");
  await expect(page).toHaveURL(/codes=2512%2C2511/);
});
