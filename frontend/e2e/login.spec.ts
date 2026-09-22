import { expect, Page, test } from "@playwright/test";

const manager = {
  id: 1,
  email: "manager1@planora.local",
  full_name: "Manager One",
  role: "manager",
  department_id: null,
  is_active: true,
  capacity_percent: 100,
};

async function mockWorkspace(page: Page) {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/login") return route.fulfill({ json: { access_token: "test-token", refresh_token: "refresh-token" } });
    if (path === "/api/auth/me") return route.fulfill({ json: manager });
    if (path === "/api/dashboard/stats") return route.fulfill({ json: { total_projects: 0, active_projects: 0, completed_projects: 0, pending_tasks: 0, overdue_tasks: 0, my_tasks: 0 } });
    if (path === "/api/projects") return route.fulfill({ json: [] });
    return route.fulfill({ json: {} });
  });
}

test("application opens the manager home without a login page", async ({ page }) => {
  await mockWorkspace(page);
  await page.goto("/");
  await expect(page).toHaveURL(/manager\/dashboard/);
  await expect(page.getByRole("heading", { name: "Good to see you." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in" })).toHaveCount(0);
});

test("legacy login URL redirects to the home workspace", async ({ page }) => {
  await mockWorkspace(page);
  await page.goto("/login");
  await expect(page).toHaveURL(/manager\/dashboard/);
});
