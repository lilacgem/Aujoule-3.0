const test = require('node:test');
const assert = require('node:assert/strict');
const StatePlayback = require('../EvoRoot/EvoSpace/StatePlayback.js');
test('play, pause, resume, seek, restart, end and replay use a monotonic clock', () => {
    let now = 0;
    const selected = [];
    const player = new StatePlayback([{atMs: 0}, {atMs: 5000}], 10000, {clock: () => now, onState: (_, index) => selected.push(index)});
    player.play(); now = 2000; player.tick(); assert.equal(player.positionMs, 2000);
    player.pause(); now = 8000; player.tick(); assert.equal(player.positionMs, 2000);
    player.play(); now = 11000; player.tick(); assert.equal(player.positionMs, 5000); assert.equal(player.index, 1);
    player.seek(1000); assert.equal(player.index, 0);
    now = 12000; player.tick(); assert.equal(player.positionMs, 2000);
    player.restart(); assert.equal(player.positionMs, 0); assert.equal(player.playing, false);
    player.play(); now = 30000; player.tick(); assert.equal(player.positionMs, 10000); assert.equal(player.playing, false);
    player.play(); assert.equal(player.positionMs, 0); assert.equal(player.playing, true);
    assert.deepEqual(selected, [0, 1, 0, 1, 0]);
});
test('invalid timings rejected; seeking clamps to bounds; repeated play is idempotent', () => {
    for (const frames of [[], [{atMs: 1}], [{atMs: 0}, {atMs: 0}], [{atMs: 0}, {atMs: 10000}]]) assert.throws(() => new StatePlayback(frames, 10000));
    const player = new StatePlayback([{atMs: 0}], 1000);
    player.seek(-50); assert.equal(player.positionMs, 0);
    player.seek(9999); assert.equal(player.positionMs, 1000);
    assert.throws(() => player.seek(NaN));
});
