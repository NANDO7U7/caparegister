import { test, expect } from '@playwright/test';

test.describe('Flujo 1: Navegación Global y Dashboard Principal', () => {
  test('Debe cargar el Dashboard principal con KPIs y analíticas', async ({ page }) => {
    await page.goto('/');
    
    // Verificar título y estructura
    await expect(page).toHaveTitle(/Dashboard Principal — SIGECAP/);
    await expect(page.locator('.sidebar-brand h1')).toHaveText('SIGECAP');
    
    // Verificar tarjetas de KPIs principales en el Dashboard
    const kpiCards = page.locator('.kpi-card');
    await expect(kpiCards).toHaveCount(6);
    
    // Verificar que los valores numéricos están presentes
    await expect(page.locator('text=Capacitaciones').first()).toBeVisible();
    await expect(page.locator('text=Docentes Formados').first()).toBeVisible();
    await expect(page.locator('text=Inscripciones').first()).toBeVisible();
    await expect(page.locator('text=Horas Impartidas').first()).toBeVisible();
    await expect(page.locator('text=Gasto Ejecutado').first()).toBeVisible();

    // Verificar botón de acceso a Consola PIF · UGB
    const btnConsola = page.locator('text=Consola PIF · UGB').first();
    await expect(btnConsola).toBeVisible();
  });

  test('Debe navegar a través de los enlaces del menú lateral', async ({ page }) => {
    await page.goto('/');

    // 1. Calendario
    await page.click('aside a[href*="calendario"]');
    await expect(page).toHaveURL(/.*calendario/);
    await expect(page.locator('h2:has-text("Calendario")')).toBeVisible();

    // 3. Padrón General
    await page.click('aside a[href*="personas"]:not([href*="matriz"]):not([href*="portal"])');
    await expect(page).toHaveURL(/.*personas/);

    // 4. Portal Docente
    await page.click('aside a[href*="portal"]');
    await expect(page).toHaveURL(/.*portal/);

    // 5. Costos y Presupuesto
    await page.click('aside a[href*="costos"]');
    await expect(page).toHaveURL(/.*costos/);

    // 6. Catálogos Base
    await page.click('aside a[href*="catalogos"]');
    await expect(page).toHaveURL(/.*catalogos/);

    // 7. Panel de Administración Web
    await page.click('aside a[href*="administracion"]');
    await expect(page).toHaveURL(/.*administracion/);

    // 8. Retornar a Consola PIF · UGB
    await page.click('aside a[href="/capacitaciones/"]');
    await expect(page).toHaveURL(/.*capacitaciones/);
    await expect(page.locator('h1')).toContainText('Sistema de Gestión de Registro de Capacitaciones');
  });
});
