import { test, expect } from './fixtures';

test.describe('Flujo 2: Consola Integral UGB · PIF (Filtros, Pestañas y Métricas)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/capacitaciones/');
  });

  test('Debe mostrar la cabecera institucional UGB PIF y los 4 KPIs superiores', async ({ page }) => {
    await expect(page).toHaveTitle(/SGRC · UGB/);
    await expect(page.locator('header')).toContainText('UGB · PIF');
    await expect(page.locator('header')).toContainText('Sistema de Gestión de Registro de Capacitaciones');
    await expect(page.locator('header')).toContainText('PostgreSQL Activo');

    // Verificar las 4 tarjetas de KPIs
    await expect(page.locator('#kpiTotalEventos')).toBeVisible();
    await expect(page.locator('#kpiModalidadSplit')).toBeVisible();
    await expect(page.locator('#kpiTotalParticipantes')).toBeVisible();
    await expect(page.locator('#kpiTotalHoras')).toBeVisible();
    await expect(page.locator('#kpiTotalInversion')).toBeVisible();

    // Comprobar que no están vacíos
    const totalEventosText = await page.locator('#kpiTotalEventos').innerText();
    expect(Number(totalEventosText)).toBeGreaterThan(0);
  });

  test('Debe alternar correctamente entre las 3 pestañas principales', async ({ page }) => {
    // 1. Pestaña inicial: Registro de Capacitaciones
    await expect(page.locator('#view-registro')).toBeVisible();
    await expect(page.locator('#view-participantes')).toBeHidden();
    await expect(page.locator('#view-presupuesto')).toBeHidden();

    // 2. Cambiar a "2. Directorio y Expediente Docente"
    await page.click('#tabBtn-participantes');
    await expect(page.locator('#view-participantes')).toBeVisible();
    await expect(page.locator('#view-registro')).toBeHidden();
    await expect(page.locator('#view-presupuesto')).toBeHidden();

    // Verificar que la tabla de participantes tiene registros
    const participantesRows = page.locator('#participantesTableBody tr');
    await expect(participantesRows.first()).toBeVisible();

    // 3. Cambiar a "3. Control Presupuestario y Áreas PIF"
    await page.click('#tabBtn-presupuesto');
    await expect(page.locator('#view-presupuesto')).toBeVisible();
    await expect(page.locator('#view-registro')).toBeHidden();
    await expect(page.locator('#view-participantes')).toBeHidden();

    // Verificar que los proyectos institucionales están presentes
    await expect(page.locator('#presupuestoProyectosContainer')).toContainText('IGA004');
    await expect(page.locator('#presupuestoProyectosContainer')).toContainText('IGA005');
    await expect(page.locator('#presupuestoProyectosContainer')).toContainText('FOR002');

    // 4. Regresar a Registro
    await page.click('#tabBtn-registro');
    await expect(page.locator('#view-registro')).toBeVisible();
  });

  test('Debe filtrar capacitaciones por búsqueda de texto y tipo', async ({ page }) => {
    const tableRows = page.locator('#capacitacionesTableBody tr');
    const initialCount = await tableRows.count();
    expect(initialCount).toBeGreaterThan(0);

    // Búsqueda por texto "Blockchain"
    await page.fill('#filterSearch', 'Blockchain');
    await expect(page.locator('#capacitacionesTableBody')).toContainText('Taller de Blockchain para docentes');

    // Limpiar filtros
    await page.click('button:has-text("Limpiar")');
    await expect(page.locator('#filterSearch')).toHaveValue('');
    const restoredCount = await tableRows.count();
    expect(restoredCount).toBe(initialCount);

    // Filtrar por Estado "Finalizada"
    await page.selectOption('#filterEstado', 'Finalizada');
    const finalizadasCount = await tableRows.count();
    expect(finalizadasCount).toBeGreaterThan(0);
  });
});
