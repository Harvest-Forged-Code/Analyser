import { type Page } from "@playwright/test";

/** Default password for test environment (from AppPreferences default). */
export const TEST_PASSWORD = "123456";

/**
 * Bypass the login page by injecting auth state into localStorage.
 * Zustand persists auth-store under the key "auth-storage".
 */
export async function bypassLogin(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem(
      "auth-storage",
      JSON.stringify({ state: { isAuthenticated: true }, version: 0 }),
    );
  });
}

/**
 * Log in via the login form with the given password.
 */
export async function loginViaForm(page: Page, password = TEST_PASSWORD) {
  await page.goto("/login");
  await page.getByPlaceholder("Enter your password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();
}

/** Wait for the sidebar to be visible (indicates authenticated shell loaded). */
export async function waitForShell(page: Page) {
  await page.waitForSelector("text=Budget Analyser", { timeout: 10_000 });
}

/** Clear auth state so the next navigation hits the login page. */
export async function clearAuth(page: Page) {
  await page.addInitScript(() => {
    localStorage.removeItem("auth-storage");
  });
}
