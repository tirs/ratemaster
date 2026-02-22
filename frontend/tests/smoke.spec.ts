import path from "path";
import { test, expect } from "@playwright/test";

const baseUrl = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:30000";
const testEmail = process.env.TEST_USER_EMAIL || "tmuseta@flowtasks.io";
const testPassword = process.env.TEST_USER_PASSWORD || "Simbarashe06@";

test.describe("RateMaster smoke tests", () => {
  test("homepage loads", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("RateMaster");
  });

  test("login page loads", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toContainText("Sign In");
  });

  test("signup page loads", async ({ page }) => {
    await page.goto("/signup");
    await expect(page.locator("h1")).toContainText("Create Account");
  });

  test("login flow - invalid credentials shows error", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "nonexistent@example.com");
    await page.fill('input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"]');
    await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible({
      timeout: 5000,
    });
  });

  test("dashboard requires auth - redirects to login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("happy path: login -> dashboard -> properties", async ({ page }) => {
    await page.goto(`${baseUrl}/login`);
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
    await expect(page.getByRole("heading", { name: /Portfolio Dashboard/i })).toBeVisible({ timeout: 5000 });
    await page.goto(`${baseUrl}/dashboard/properties`);
    await expect(page.getByRole("heading", { name: /^Properties$/ })).toBeVisible({ timeout: 5000 });
  });

  test("happy path: login -> upload -> run -> results", async ({ page }) => {
    test.setTimeout(90000); // Engine run can take 30-60s

    await page.goto(`${baseUrl}/login`);
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Create org + property for fresh test data
    const runId = Date.now();
    const orgName = `Smoke Org ${runId}`;
    const propName = `Smoke Prop ${runId}`;

    await page.goto(`${baseUrl}/dashboard/properties`);
    await expect(page.getByRole("heading", { name: /^Properties$/ })).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: /\+ Organization/i }).click();
    await page.fill('input[placeholder="Organization name"]', orgName);
    await page.getByRole("button", { name: /^Create$/ }).click();
    await expect(page.getByText(orgName)).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: /\+ Property/i }).click();
    await page.locator("#create-prop-org").selectOption({ label: orgName });
    await page.fill('input[placeholder="Property name"]', propName);
    await page.getByRole("button", { name: /^Add$/ }).click();
    await expect(page.getByText(propName)).toBeVisible({ timeout: 5000 });

    // Upload CSV
    await page.goto(`${baseUrl}/dashboard/data`);
    await expect(page.getByRole("heading", { name: /Data Ingestion/i })).toBeVisible({ timeout: 5000 });

    await page.locator('select').first().selectOption({ label: propName });

    const csvPath = path.join(__dirname, "fixtures", "sample.csv");
    await page.locator('#csv-upload').setInputFiles(csvPath);

    await expect(page.getByText(/Rows:|Health:/i)).toBeVisible({ timeout: 15000 });

    // Run Engine A
    await page.goto(`${baseUrl}/dashboard/engines`);
    await expect(page.getByRole("heading", { name: /Dual Engines/i })).toBeVisible({ timeout: 5000 });

    await page.locator("#engines-property").selectOption({ label: propName });
    await page.getByRole("button", { name: /Run Engine A/i }).click();

    await expect(page.getByText(/Engine run in progress|View/i)).toBeVisible({ timeout: 5000 });

    // Wait for run to complete (poll for "View" on a run)
    await expect(page.getByRole("button", { name: /^View$/ }).first()).toBeVisible({ timeout: 60000 });

    // View results on Contribution page
    await page.goto(`${baseUrl}/dashboard/contribution`);
    await expect(page.getByRole("heading", { name: /RateMaster Contribution/i })).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.glass-card').first()).toBeVisible();
  });
});
