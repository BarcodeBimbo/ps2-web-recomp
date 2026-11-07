// Run with Node and Playwright installed. Uses synthetic input, not a game ROM.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox']});
  const context = await browser.newContext({viewport: {width: 844, height: 390}, hasTouch: true, isMobile: true});
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    const body = url.pathname.endsWith('boot.txt') ? 'cdrom0:\\SCUS_971.98;1' : fs.readFileSync(path.join(__dirname, '../web/shell.html'), 'utf8').replace('{{{ SCRIPT }}}', '');
    return route.fulfill({status: 200, contentType: url.pathname.endsWith('boot.txt') ? 'text/plain' : 'text/html', body});
  });
  const page = await context.newPage(), errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:8620/play/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/?touch');
  await page.evaluate(() => {
    document.getElementById('overlay').remove();
    window.testOutput = [];
    Module._ps2web_pad_connected = () => {};
    Module._ps2web_pad = (...args) => testOutput.push(args);
    Module._ps2web_pressure = () => {};
    Module._ps2web_rumble = () => 0;
  });
  const cdp = await context.newCDPSession(page);
  const rect = async selector => page.locator(selector).boundingBox();
  const center = r => ({x: r.x + r.width / 2, y: r.y + r.height / 2});
  const left = await rect('[data-stick="left"]'), right = await rect('[data-stick="right"]');
  assert(left && right);
  const cross = center(await rect('[data-slot="14"]'));
  const touches = [{...center(left), id: 1}, {...center(right), id: 2}, {...cross, id: 3}];
  await cdp.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: touches});
  touches[0].x += left.width / 2; touches[1].y -= right.height / 2;
  await cdp.send('Input.dispatchTouchEvent', {type: 'touchMove', touchPoints: touches});
  const output = await page.evaluate(() => {pollPlayer(0, null, true); return testOutput.at(-1);});
  assert.equal(output[1] & 16384, 16384, 'simultaneous Cross');
  assert.equal(output[2], 255, 'left stick right');
  assert.equal(output[5], 0, 'right stick up');
  await cdp.send('Input.dispatchTouchEvent', {type: 'touchCancel', touchPoints: []});
  await page.waitForTimeout(110);
  assert.deepEqual(await page.evaluate(() => {pollPlayer(0, null, true);return testOutput.at(-1).slice(1);}), [0,128,128,128,128]);
  // Start tap survives until the next emulator sample.
  await page.locator('[data-slot="3"]').tap();
  assert.equal(await page.evaluate(() => {pollPlayer(0,null,true);return testOutput.at(-1)[1] & 8;}), 8);
  // Remapping a touch position affects the emulator and survives a reload.
  await page.locator('#open-pc-controls').tap();
  await page.locator('#touch-mapping summary').tap();
  await page.locator('#touch-bindings label').filter({hasText: 'Start position'}).locator('select').selectOption('14');
  await page.locator('#close-pc-controls').tap();
  await page.locator('[data-slot="3"]').tap();
  assert.equal(await page.evaluate(() => {pollPlayer(0,null,true);return testOutput.at(-1)[1] & 16384;}), 16384);
  await page.evaluate(() => { clearInput(); });
  assert.equal(await page.evaluate(() => fingers.size), 0);
  await page.reload();
  assert.equal(await page.locator('[data-slot="3"]').innerText(), 'Cross');
  await page.evaluate(() => document.getElementById('overlay').remove());
  // Check controller targets and settings across phone sizes and orientation.
  for (const [width,height] of [[390,844],[360,640],[844,390],[568,320]]) {
    await page.setViewportSize({width,height});
    await page.waitForTimeout(100);
    for (const selector of ['[data-slot="3"]','[data-stick="left"]','[data-stick="right"]','[data-slot="14"]']) {
      const r = await rect(selector);
      assert(r.x >= 0 && r.y >= 0 && r.x+r.width <= width+1 && r.y+r.height <= height+1, `${selector} fits ${width}x${height}: ${JSON.stringify(r)}`);
      const hit = await page.evaluate(({x,y,selector}) => document.querySelector(selector).contains(document.elementFromPoint(x,y)), {...center(r), selector});
      assert(hit, `${selector} is reachable at ${width}x${height}`);
    }
    await page.screenshot({path: `/tmp/mobile-${width}x${height}.png`});
    await page.locator('#open-pc-controls').tap();
    assert(await page.locator('#pc-controls').isVisible());
    await page.locator('#close-pc-controls').tap();
  }
  await page.locator('#touch-toggle').tap();
  assert.equal(await page.locator('#touch').getAttribute('aria-hidden'), 'true');
  await page.locator('#touch-toggle').tap();
  assert.equal(await page.locator('#touch').getAttribute('aria-hidden'), 'false');
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('PASS: multitouch, both sticks, Start, cancellation, remapping, persistence, visibility, phone layouts, no JS errors');
})().catch(e => {console.error(e);process.exit(1);});
