import { test as base, expect } from '@playwright/test';

// Each test authenticates against the in-memory server; no stored sessions.
export const test = base.extend({
  page: async ({ page }, use) => {
    const password = process.env.SIGECAP_E2E_ADMIN_PASSWORD;
    if (!password) throw new Error('Inicia las pruebas mediante playwright.config.ts.');
    await page.goto('/login/');
    await page.locator('[name="username"]').fill('admin');
    await page.locator('[name="password"]').fill(password);
    await Promise.all([
      page.waitForURL('http://127.0.0.1:8091/'),
      page.getByRole('button', { name: 'Iniciar sesión' }).click(),
    ]);
    await use(page);
  },
});

export { expect };
