import { defineConfig, devices } from '@playwright/test';

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
    ['json', { outputFile: 'test-results/playwright-results.json' }]
  ],
  use: {
    baseURL: 'http://127.0.0.1:8000',
    trace: 'on-first-retry',
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
    command: 'python sigecap/manage.py runserver 127.0.0.1:8000',
    url: 'http://127.0.0.1:8000/',
    reuseExistingServer: true,
    timeout: 60000,
  },
});
