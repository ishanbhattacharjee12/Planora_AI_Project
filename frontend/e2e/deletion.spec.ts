import { expect, test } from "@playwright/test";

const manager = {
  id: 1,
  email: "manager1@planora.local",
  full_name: "Manager One",
  role: "manager",
  department_id: null,
  is_active: true,
  capacity_percent: 100,
};

const project = {
  id: 7,
  name: "Temporary Project",
  status: "draft",
  priority: "medium",
  classification: "internal",
  updated_at: "2026-09-21T09:30:00Z",
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/me") return route.fulfill({ json: manager });
    if (path === "/api/projects") return route.fulfill({ json: [project] });
    if (path === "/api/logs") return route.fulfill({ json: Array.from({ length: 8 }, (_, index) => ({
      id: 11 + index,
      project_id: project.id + index,
      project_name: index === 0 ? project.name : `Project Memory ${index + 1}`,
      snippet: "A temporary planning workspace",
      summary: "Temporary project summary",
      architecture: "Frontend: React · Backend: FastAPI · Database: SQLite",
      semantic_summary: "Temporary planning workspace",
      index_status: "indexed",
      created_at: project.updated_at,
      updated_at: project.updated_at,
    })) });
    return route.fulfill({ json: {} });
  });
  await page.addInitScript((storedUser) => {
    localStorage.setItem("access_token", "visual-test-token");
    localStorage.setItem("user", JSON.stringify(storedUser));
  }, manager);
});

test("project and log delete controls require explicit confirmation", async ({ page }) => {
  await page.goto("/manager/projects");
  await expect(page.locator(".sidebar-brand img")).toHaveAttribute("src", "/rt-logo.png");
  const logoIsRenderedAtNativeQuality = await page.locator(".sidebar-brand img").evaluate((image: HTMLImageElement) => image.naturalWidth >= image.clientWidth);
  expect(logoIsRenderedAtNativeQuality).toBe(true);

  await page.getByRole("button", { name: `Delete ${project.name}` }).click();
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await expect(page.getByText("This action cannot be undone.")).toBeVisible();
  await page.getByRole("button", { name: "Keep project" }).click();
  await expect(page.getByRole("alertdialog")).toHaveCount(0);

  await page.goto("/manager/logs");
  await page.getByRole("button", { name: `Delete ${project.name}` }).click();
  await expect(page.getByRole("alertdialog")).toContainText("also removes its complete project");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("alertdialog")).toHaveCount(0);
});

test("logs paginate compactly with four memories per page", async ({ page }) => {
  await page.goto("/manager/logs");
  await expect(page.locator(".memory-card")).toHaveCount(4);
  await expect(page.getByText("Showing 1–4 of 8")).toBeVisible();
  await expect(page.getByText("Project Memory 8")).toHaveCount(0);

  await page.getByRole("button", { name: "Next logs page" }).click();
  await expect(page.locator(".memory-card")).toHaveCount(4);
  await expect(page.getByText("Showing 5–8 of 8")).toBeVisible();
  await expect(page.getByText("Project Memory 8")).toBeVisible();
});
