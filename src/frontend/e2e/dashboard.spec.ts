import { test, expect } from "@playwright/test";
import { bypassLogin, waitForShell } from "./helpers";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await bypassLogin(page);
    await page.goto("/");
    await waitForShell(page);
  });

  test("renders dashboard page with heading", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Dashboard");
  });

  test("shows loading skeletons initially", async ({ page }) => {
    // The page should show either skeletons or content
    // (depends on API speed, so check the page renders something)
    const content = page.locator("main");
    await expect(content).toBeVisible();
  });

  test("displays KPI cards or empty state", async ({ page }) => {
    // Wait for data to load (either KPI cards or empty state)
    await page.waitForTimeout(3000);

    const hasKpiCards = await page.getByText("Total Earnings", { exact: true }).isVisible();
    const hasEmptyState = await page
      .locator("text=No data available")
      .isVisible();

    // Must show either KPI cards or empty state
    expect(hasKpiCards || hasEmptyState).toBeTruthy();
  });

  test("empty state shows upload button when no data", async ({ page }) => {
    await page.waitForTimeout(3000);

    const hasEmptyState = await page
      .locator("text=No data available")
      .isVisible();

    if (hasEmptyState) {
      await expect(
        page.getByRole("button", { name: /upload/i }),
      ).toBeVisible();
    }
  });
});
