const test = require('node:test');
const assert = require('node:assert/strict');
const RecordingTelemetry = require('../EvoRoot/EvoSpace/RecordingTelemetry.js');
const options = {assetId: 'session', videoFilename: 'session.webm', durationMs: 250, mimeType: 'video/webm', resolution: {width: 640, height: 480}, sampleRateHz: 48000};
test('samples changed live values with elapsed timestamps and derives summaries', () => {
    const recorder = new RecordingTelemetry('2026-11-01T00:00:00Z');
    recorder.sample(0, {microphoneLevel: .2, hueDegrees: 30, resonance: .4, rootValue: 3});
    recorder.sample(50, {microphoneLevel: 1, hueDegrees: 90, resonance: 2, rootValue: 9});
    recorder.sample(100, {microphoneLevel: .8, hueDegrees: 120, resonance: 1.2, rootValue: 6});
    recorder.sample(200, {microphoneLevel: 0, hueDegrees: 180, resonance: .01, rootValue: 0});
    const output = recorder.metadata(options);
    assert.equal(output.videoFilename, 'session.webm');
    assert.deepEqual(output.telemetry.timeline.map(s => s.elapsedMs), [0, 100, 200]);
    assert.equal(output.telemetry.summary.peakMicrophoneLevel, .8);
    assert.equal(output.telemetry.summary.averageMicrophoneLevel, 1 / 3);
    assert.equal(output.telemetry.summary.final.rootValue, 0);
    recorder.sample(300, {microphoneLevel: 1});
    assert.equal(output.telemetry.timeline.length, 3, 'export must be a snapshot');
});
test('a new recording has no samples from a previous session', () => {
    const recorder = new RecordingTelemetry('new-session');
    const output = recorder.metadata(options);
    assert.equal(output.telemetry.summary.sampleCount, 0);
    assert.equal(output.telemetry.summary.averageMicrophoneLevel, null);
    assert.equal(output.telemetry.summary.final, null);
    assert.deepEqual(output.telemetry.timeline, []);
    assert.equal('frequency' in output, false);
    assert.equal('animation_url' in output, false);
});
