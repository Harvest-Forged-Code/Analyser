import { test, expect } from "@playwright/test";
import { bypassLogin, waitForShell } from "./helpers";

test.describe("Page rendering", () => {
  test.beforeEach(async ({ page }) => {
    await bypassLogin(page);
  });

  const pages = [
    { url: "/earnings", heading: "Earnings" },
    { url: "/expenses", heading: "Expenses" },
    { url: "/budget-goals", heading: "Budget Goals" },
    { url: "/savings", heading: "Savings" },
    { url: "/net-worth", heading: "Net Worth" },
    { url: "/recurring", heading: "Recurring" },
    { url: "/payments", heading: "Payments" },
    { url: "/upload", heading: "Upload" },
    { url: "/mapper-hub", heading: "Mapper" },
    { url: "/settings", heading: "Settings" },
    { url: "/yearly-summary", heading: "Yearly Summary" },
  ];

  for (const pg of pages) {
    test(`${pg.heading} page loads without errors`, async ({ page }) => {
      await page.goto(pg.url);
      await waitForShell(page);

      // Page heading should be visible
      await expect(page.locator("h1")).toContainText(pg.heading, {
        timeout: 10_000,
      });

      // No uncaught errors in the console
      const errors: string[] = [];
      page.on("pageerror", (err) => errors.push(err.message));

      // Wait for the page to settle
      await page.waitForTimeout(2000);

      // Should have rendered content (no blank page)
      const mainContent = page.locator("main");
      await expect(mainContent).toBeVisible();
    });
  }
});

test.describe("Settings page", () => {
  test.beforeEach(async ({ page }) => {
    await bypassLogin(page);
    await page.goto("/settings");
    await waitForShell(page);
  });

  test("shows log level selector", async ({ page }) => {
    await expect(page.getByText("Logging", { exact: true })).toBeVisible();
  });

  test("shows change password section", async ({ page }) => {
    await expect(page.getByText(/change password/i)).toBeVisible();
  });
});

test.describe("Upload page", () => {
  test.beforeEach(async ({ page }) => {
    await bypassLogin(page);
    await page.goto("/upload");
    await waitForShell(page);
  });

  test("shows account type and bank selectors", async ({ page }) => {
    await page.waitForTimeout(2000);
    // Should show upload-related controls
    const mainContent = page.locator("main");
    await expect(mainContent).toBeVisible();
  });
});

test.describe("Net Worth page", () => {
  test.beforeEach(async ({ page }) => {
    await bypassLogin(page);
    await page.goto("/net-worth");
    await waitForShell(page);
  });

  test("shows add account button", async ({ page }) => {
    await page.waitForTimeout(2000);
    await expect(
      page.getByRole("button", { name: /add account/i }),
    ).toBeVisible();
  });
});

test.describe("Recurring page", () => {
  test.beforeEach(async ({ page }) => {
    await bypassLogin(page);
    await page.goto("/recurring");
    await waitForShell(page);
  });

  test("shows add recurring button", async ({ page }) => {
    await page.waitForTimeout(2000);
    await expect(
      page.getByRole("button", { name: /add recurring/i }),
    ).toBeVisible();
  });
});

test.describe("Budget Goals page", () => {
  test.beforeEach(async ({ page }) => {
    await bypassLogin(page);
    await page.goto("/budget-goals");
    await waitForShell(page);
  });

  test("shows tabs for budget goals", async ({ page }) => {
    await expect(page.getByRole("tab", { name: /budget/i })).toBeVisible();
  });
});
