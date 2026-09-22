import { expect, test } from "@playwright/test";

const user = {
  id: 1,
  email: "manager1@planora.local",
  full_name: "Morgan Lee",
  role: "manager",
  department_id: 1,
  is_active: true,
  capacity_percent: 75,
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/me") return route.fulfill({ json: user });
    if (path === "/api/dashboard/stats") return route.fulfill({ json: { total_projects: 12, active_projects: 7, completed_projects: 3, pending_tasks: 18, overdue_tasks: 2, my_tasks: 0 } });
    if (path === "/api/projects") return route.fulfill({ json: [
      { id: 1, name: "Client Intelligence Hub", classification: "Confidential", status: "active", priority: "high", updated_at: "2026-09-15T09:30:00Z" },
      { id: 2, name: "Operations Workflow", classification: "Internal", status: "review", priority: "medium", updated_at: "2026-09-14T09:30:00Z" },
    ] });
    return route.fulfill({ json: {} });
  });
  await page.addInitScript((storedUser) => {
    localStorage.setItem("access_token", "visual-test-token");
    localStorage.setItem("user", JSON.stringify(storedUser));
  }, user);
});

test("manager dashboard fills the desktop workspace with responsive charts", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/manager/dashboard");
  await expect(page.getByRole("heading", { name: "Good to see you." })).toBeVisible();
  await expect(page.getByText("Client Intelligence Hub")).toBeVisible();
  await expect(page.locator(".recharts-responsive-container")).toHaveCount(2);
  await expect(page.locator(".main")).toHaveCSS("overflow", "auto");
});

test("manager dashboard uses mobile navigation without horizontal page overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/manager/dashboard");
  await expect(page.getByRole("button", { name: "Open navigation" })).toBeVisible();
  const hasHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(hasHorizontalOverflow).toBe(false);
});
