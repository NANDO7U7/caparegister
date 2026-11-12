import { defineConfig, devices } from '@playwright/test';
import { randomBytes } from 'node:crypto';

for (const role of ['ADMIN', 'PIF', 'COORD', 'CONSULTA']) {
  process.env[`SIGECAP_E2E_${role}_PASSWORD`] ||= randomBytes(32).toString('base64url');
}

/**
 * Playwright Test configuration for SIGECAP — Sistema de Gestión de Capacitaciones UGB · PIF.
 * Compatible with Playwright Test for VS Code.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 30000,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/playwright-results.json' }]
  ],
  use: {
    baseURL: 'http://127.0.0.1:8091',
    trace: 'off',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [
    {
      name: 'Google Chrome',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
      },
    },
    {
      name: 'Microsoft Edge',
      use: {
        ...devices['Desktop Edge'],
        channel: 'msedge',
      },
    },
  ],
  webServer: {
    command: `"${process.env.SIGECAP_PYTHON || 'python'}" sigecap/e2e_server.py`,
    url: 'http://127.0.0.1:8091/login/',
    reuseExistingServer: false,
    timeout: 60000,
  },
});
