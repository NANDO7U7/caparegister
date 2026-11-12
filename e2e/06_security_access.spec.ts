import { test, expect } from './fixtures';

test.describe('Seguridad aislada', () => {
  test('Las rutas privadas redirigen al login sin sesión', async ({ browser }) => {
    const context = await browser.newContext();
    try {
      const page = await context.newPage();
      await page.goto('http://127.0.0.1:8091/administracion/');
      await expect(page).toHaveURL(/\/login\/\?next=/);
      await expect(page.locator('[name="username"]')).toBeVisible();
    } finally { await context.close(); }
  });

  test('Consulta autenticada no puede administrar ni falsificar rol', async ({ page }) => {
    await page.goto('/login/');
    await page.locator('[name="username"]').fill('consulta');
    await page.locator('[name="password"]').fill(process.env.SIGECAP_E2E_CONSULTA_PASSWORD!);
    await Promise.all([page.waitForURL('http://127.0.0.1:8091/'), page.getByRole('button', { name: 'Iniciar sesión' }).click()]);
    const token = (await page.context().cookies()).find(cookie => cookie.name === 'csrftoken')!.value;
    const response = await page.request.post('/administracion/catalogo/facultad/crear/', {
      headers: { 'X-CSRFToken': token, 'X-User-Role': 'ADMIN' }, form: { codigo: 'NO', nombre: 'No permitido' },
    });
    expect(response.status()).toBe(403);
    expect((await page.request.get('/administracion/')).status()).toBe(403);
    expect((await page.request.get('/')).status()).toBe(200);
  });

  test('Superusuario puede abrir el panel administrativo', async ({ page }) => {
    const response = await page.goto('/administracion/');
    expect(response?.status()).toBe(200);
    await expect(page.locator('.header-title h2')).toContainText('Administración');
  });

  test('Cerrar sesión invalida el acceso al Dashboard', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Cerrar sesión' }).click();
    await expect(page).toHaveURL('http://127.0.0.1:8091/login/');
    await page.goto('/');
    await expect(page).toHaveURL(/\/login\/\?next=/);
  });
});
