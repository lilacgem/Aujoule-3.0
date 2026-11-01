const {chromium} = require('playwright');
const fs = require('fs');
const assert = require('assert/strict');
(async () => {
 const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
 try {
  const page = await browser.newPage({baseURL: process.env.EVOSPACE_URL || 'http://127.0.0.1:8001'});
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  if (process.env.THREE_JS_PATH) await page.route('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', r => r.fulfill({contentType: 'application/javascript', body: fs.readFileSync(process.env.THREE_JS_PATH)}));
  await page.goto('/');
  await page.waitForFunction(() => typeof statePlayback !== 'undefined' && statePlayback && !document.querySelector('#playbackControls').hidden);
  assert.equal(await page.evaluate(() => statePlayback.durationMs), 10000);
  await page.click('#playState'); await page.waitForTimeout(300);
  await page.click('#playState');
  const paused = await page.evaluate(() => statePlayback.positionMs);
  assert(paused > 0);
  await page.waitForTimeout(300);
  assert.equal(await page.evaluate(() => statePlayback.positionMs), paused);
  // Resume close to the step boundary to verify real clock-driven state advancement.
  await page.evaluate(() => statePlayback.seek(4900));
  await page.click('#playState');
  await page.waitForFunction(() => evoState.prototype.generation === 2);
  assert.equal(await page.evaluate(() => compiledGlow), .5);
  assert.equal(await page.locator('#packageSelect').inputValue(), '1');
  await page.click('#restartState');
  assert.equal(await page.evaluate(() => statePlayback.positionMs), 0);
  assert.equal(await page.evaluate(() => statePlayback.playing), false);
  assert.equal(await page.evaluate(() => compiledGlow), .8);
  // Exercise native keyboard seeking and the end state.
  await page.locator('#stateTimeline').focus(); await page.keyboard.press('End');
  await page.waitForFunction(() => statePlayback.positionMs === 10000);
  assert.equal(await page.locator('#playbackStatus').innerText(), 'Ended');
  assert.equal(await page.evaluate(() => evoState.prototype.generation), 2);
  await page.click('#playState');
  await page.waitForFunction(() => statePlayback.playing && evoState.prototype.generation === 1);
  await page.selectOption('#packageSelect', '1');
  await page.waitForFunction(() => !document.querySelector('#packageSelect').disabled && evoState.prototype.generation === 2);
  assert.equal(await page.evaluate(() => statePlayback.playing), false);
  assert.equal(await page.evaluate(() => statePlayback.positionMs), 5000);
  assert(await page.locator('#micButton').isDisabled());
  assert.deepEqual(errors, []);
  console.log('PASS: play/pause, timed generation change, restart, keyboard seek, end/replay and manual selection.');
 } finally {await browser.close();}
})().catch(error => {console.error(error); process.exit(1);});
