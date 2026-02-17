import { test, expect } from "@playwright/test";
import { TEST_PASSWORD, clearAuth } from "./helpers";

test.describe("Authentication", () => {
  test.beforeEach(async ({ page }) => {
    await clearAuth(page);
  });

  test("shows login page for unauthenticated users", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByText("Budget Analyser")).toBeVisible();
    await expect(
      page.getByPlaceholder("Enter your password"),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Sign In" }),
    ).toBeVisible();
  });

  test("sign-in button is disabled when password is empty", async ({
    page,
  }) => {
    await page.goto("/login");
    await expect(
      page.getByRole("button", { name: "Sign In" }),
    ).toBeDisabled();
  });

  test("shows error on invalid password", async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder("Enter your password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page.getByText(/invalid password/i)).toBeVisible();
  });

  test("successful login redirects to dashboard", async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder("Enter your password").fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "Sign In" }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL("/", { timeout: 10_000 });
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });

  test("toggle password visibility", async ({ page }) => {
    await page.goto("/login");
    const input = page.getByPlaceholder("Enter your password");
    await expect(input).toHaveAttribute("type", "password");

    // Fill in password first so the toggle button area is populated
    await input.fill("test");

    // Click the eye icon button (it's the button inside the password field container)
    const toggleBtn = page.locator("input#password + button");
    await toggleBtn.click();
    await expect(input).toHaveAttribute("type", "text");
  });

  test("logout returns to login page", async ({ page }) => {
    // Login first
    await page.goto("/login");
    await page.getByPlaceholder("Enter your password").fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page).toHaveURL("/", { timeout: 10_000 });

    // Click logout in sidebar
    await page.getByText("Logout").click();
    await expect(page).toHaveURL(/\/login/);
  });
});
