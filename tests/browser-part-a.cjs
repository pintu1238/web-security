/* Verify the complete frontend is visible while Part B actions stay disabled. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'nitishield-part-a-'));
const port = process.env.TEST_PORT || '5059';
const base = `http://127.0.0.1:${port}`;
const python = process.env.PYTHON || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
fs.mkdirSync(path.join(temporary, 'legal_documents'));
for (const file of fs.readdirSync(path.join(root, 'Backend', 'legal_documents')).filter(file => file.endsWith('.pdf'))) {
  fs.copyFileSync(path.join(root, 'Backend', 'legal_documents', file), path.join(temporary, 'legal_documents', file));
}

const server = spawn(python, [path.join(__dirname, 'serve_test_app.py')], {
  cwd: root,
  env: {...process.env, NITISHIELD_TEST_DIR: temporary, NITISHIELD_TEST_STAGE: 'part_a', TEST_PORT: port},
  windowsHide: true,
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', data => { serverLog += data; });
server.stderr.on('data', data => { serverLog += data; });

async function main() {
  let ready = false;
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`Test server exited: ${serverLog}`);
    try {
      const response = await fetch(`${base}/api/health`);
      if (response.ok) { ready = true; break; }
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.ok(ready, `Test server did not start: ${serverLog}`);

  const executable = process.env.BROWSER_EXECUTABLE || (process.platform === 'win32' ? 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe' : undefined);
  const browser = await chromium.launch({headless: process.env.HEADLESS === '1', ...(executable ? {executablePath: executable} : {})});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1120}});
    const jsErrors = [];
    page.on('pageerror', error => jsErrors.push(error.message));
    await page.goto(base);
    await page.getByRole('heading', {name: 'Overview', exact: true}).waitFor();
    assert.equal(await page.locator('#connection-dot').count(), 0);
    assert.equal(await page.getByText('Workspace connected', {exact: true}).count(), 0);
    await page.getByText('Part A presentation mode.', {exact: false}).waitFor();

    const navigation = page.locator('#navigation .nav-item');
    assert.equal(await navigation.count(), 8);
    for (const label of ['Overview', 'Security scanner', 'Legal compliance', 'Legal assistant', 'Document studio', 'Knowledge base', 'Admin panel', 'User panel']) {
      await page.locator('#navigation').getByRole('link', {name: label}).waitFor();
    }

    await page.goto(`${base}/#scanner`);
    await page.getByText('SECURITY SCANNER', {exact: true}).waitFor();
    await page.getByText('Security scanner is reserved for Part B.', {exact: false}).waitFor();
    assert.equal(await page.getByRole('button', {name: 'Available in Part B', exact: true}).isDisabled(), true);
    assert.equal(await page.getByLabel('Website URL').isDisabled(), true);

    await page.goto(`${base}/#compliance`);
    await page.getByText('LEGAL COMPLIANCE', {exact: true}).waitFor();
    await page.getByText('Legal compliance is reserved for Part B.', {exact: false}).waitFor();
    assert.equal(await page.getByRole('button', {name: 'Add task', exact: true}).first().isDisabled(), true);
    assert.equal(await page.locator('[data-action="toggle-task"]').first().isDisabled(), true);

    await page.goto(`${base}/#admin`);
    await page.getByText('ADMINISTRATION', {exact: true}).waitFor();
    await page.getByText('Team management starts in Part B', {exact: false}).waitFor();
    await page.goto(`${base}/#user`);
    await page.getByText('MY WORK', {exact: true}).waitFor();
    await page.getByText('Assigned work starts in Part B', {exact: false}).waitFor();

    assert.deepEqual(jsErrors, []);
    process.stdout.write('PASS complete frontend is visible in Part A with Part B actions disabled\n');
  } finally {
    await browser.close();
  }
}

main().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; }).finally(() => {
  server.kill();
});
