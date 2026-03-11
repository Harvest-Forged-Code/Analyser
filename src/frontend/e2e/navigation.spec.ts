import { test, expect } from "@playwright/test";
import { bypassLogin, waitForShell } from "./helpers";

test.describe("Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await bypassLogin(page);
    await page.goto("/");
    await waitForShell(page);
  });

  const navRoutes = [
    { label: "Dashboard", url: "/", heading: "Dashboard" },
    { label: "Yearly Summary", url: "/yearly-summary", heading: "Yearly Summary" },
    { label: "Earnings", url: "/earnings", heading: "Earnings" },
    { label: "Expenses", url: "/expenses", heading: "Expenses" },
    { label: "Payments", url: "/payments", heading: "Payments" },
    { label: "Budget Goals", url: "/budget-goals", heading: "Budget Goals" },
    { label: "Savings", url: "/savings", heading: "Savings" },
    { label: "Net Worth", url: "/net-worth", heading: "Net Worth" },
    { label: "Upload", url: "/upload", heading: "Upload" },
    { label: "Mapper Hub", url: "/mapper-hub", heading: "Mapper" },
    { label: "Settings", url: "/settings", heading: "Settings" },
  ];

  for (const route of navRoutes) {
    test(`navigates to ${route.label}`, async ({ page }) => {
      // Click the sidebar link
      await page.getByRole("link", { name: route.label }).click();
      await expect(page).toHaveURL(route.url);
      // Page heading should contain the expected text
      await expect(
        page.getByRole("heading", { level: 1 }).or(page.locator("h1")),
      ).toContainText(route.heading);
    });
  }

  test("sidebar collapse toggle works", async ({ page }) => {
    // Sidebar should initially show labels
    await expect(page.getByText("Collapse")).toBeVisible();

    // Click collapse
    await page.getByText("Collapse").click();

    // Labels should be hidden (sidebar collapsed)
    await expect(page.getByText("Collapse")).not.toBeVisible();
  });

  test("theme toggle switches between light and dark", async ({ page }) => {
    const html = page.locator("html");

    // Toggle to dark
    await page.getByText("Dark Mode").click();
    await expect(html).toHaveClass(/dark/);

    // Toggle back to light
    await page.getByText("Light Mode").click();
    await expect(html).not.toHaveClass(/dark/);
  });
});
