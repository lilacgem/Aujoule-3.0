const {chromium} = require('playwright');
const fs = require('fs');
const assert = require('assert/strict');
(async () => {
    const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH,
        args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
    try {
        const page = await browser.newPage({baseURL: process.env.EVOSPACE_URL || 'http://127.0.0.1:8001'});
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        if (process.env.THREE_JS_PATH) await page.route('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
            route => route.fulfill({contentType: 'application/javascript', body: fs.readFileSync(process.env.THREE_JS_PATH)}));
        await page.goto(process.env.EVOSPACE_URL || 'http://127.0.0.1:8001');
        await page.waitForFunction(() => typeof evoState !== 'undefined' && evoState?.prototype && !document.querySelector('#packageControls').hidden);
        const initial = await page.evaluate(() => ({id: evoState.prototype.stateId, glow: compiledGlow, generation: evoState.prototype.generation}));
        assert.equal(initial.glow, .8);
        assert.equal(initial.generation, 1);
        assert(await page.locator('#micButton').isDisabled());
        assert(await page.locator('#recordButton').isDisabled());
        await page.selectOption('#packageSelect', '1');
        await page.waitForFunction(() => evoState.prototype.generation === 2);
        assert.equal(await page.evaluate(() => compiledGlow), .5);
        assert.notEqual(await page.evaluate(() => evoState.prototype.stateId), initial.id);
        // A bad response must not replace the last valid baseline or its selection.
        await page.route('**/api/state?index=0', route => route.fulfill({json: {schema: 'invalid'}}));
        await page.selectOption('#packageSelect', '0');
        await page.waitForFunction(() => document.querySelector('#stateStatus').textContent.includes('previous state retained'));
        assert.equal(await page.locator('#packageSelect').inputValue(), '1');
        assert.equal(await page.evaluate(() => compiledGlow), .5);
        const response = await page.request.get('/api/state?index=-1');
        assert.equal(response.status(), 400);
        assert.equal((await page.request.get('/baseline-package.json')).status(), 404);
        assert.equal((await page.request.get('/api/packages', {headers: {Host: 'untrusted.example'}})).status(), 403);
        assert.deepEqual(errors, []);
        console.log('PASS: baseline and changed packages render; invalid load retains state; private files and foreign Host blocked.');
    } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exit(1);});
