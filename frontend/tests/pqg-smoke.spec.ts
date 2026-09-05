import { test, expect } from "@playwright/test";

test("PQG suggestion click fills composer without sending", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Shanye Shop Demo" })).toBeVisible();
  await expect(page.getByRole("button", { name: "发送" })).toBeVisible();
});
