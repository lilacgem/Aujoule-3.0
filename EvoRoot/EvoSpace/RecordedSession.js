/* Local-file playback: no fetch, uploads, storage or microphone access. */
function validateRecordingMetadata(data, filename) {
    if (!data || data.schema !== 'AuEvo-Recording/v1') throw new Error('Unsupported recording metadata. Use the JSON exported with a recent recording.');
    if (data.videoFilename !== filename) throw new Error('Metadata filename does not match this video. Select its matching JSON file.');
    if (!Number.isFinite(data.durationMs) || data.durationMs <= 0 || data.telemetry?.source !== 'microphone') throw new Error('Invalid session duration or telemetry source.');
    const interval = data.telemetry.nominalSampleIntervalMs;
    if (!Number.isFinite(interval) || interval <= 0) throw new Error('Invalid sample interval.');
    const samples = data.telemetry.timeline;
    if (!Array.isArray(samples)) throw new Error('Missing session timeline.');
    let previous = -1;
    let sum = 0, peak = 0;
    for (const sample of samples) {
        if (!Number.isFinite(sample.elapsedMs) || sample.elapsedMs < previous || sample.elapsedMs < 0 || sample.elapsedMs > data.durationMs) throw new Error('Invalid timeline timestamps.');
        previous = sample.elapsedMs;
        for (const [key, max] of [['microphoneLevel', 1], ['hueDegrees', 360], ['resonance', Infinity], ['rootValue', 9]]) {
            if (!Number.isFinite(sample[key]) || sample[key] < 0 || sample[key] > max) throw new Error(`Invalid timeline value: ${key}`);
        }
        if (!Number.isInteger(sample.rootValue)) throw new Error('Invalid digital root.');
        sum += sample.microphoneLevel;
        peak = Math.max(peak, sample.microphoneLevel);
    }
    const summary = data.telemetry.summary;
    if (!summary || summary.sampleCount !== samples.length) throw new Error('Summary count does not match the timeline.');
    const average = samples.length ? sum / samples.length : null;
    const expectedPeak = samples.length ? peak : null;
    if ((average === null ? summary.averageMicrophoneLevel !== null : !Number.isFinite(summary.averageMicrophoneLevel) || Math.abs(summary.averageMicrophoneLevel - average) > 1e-9) || summary.peakMicrophoneLevel !== expectedPeak) throw new Error('Summary values do not match recorded samples.');
    return data;
}

function recordingSampleAt(data, elapsedMs) {
    const samples = data.telemetry.timeline;
    let lo = 0, hi = samples.length - 1, found = -1;
    while (lo <= hi) {
        const mid = Math.floor((lo + hi) / 2);
        if (samples[mid].elapsedMs <= elapsedMs) { found = mid; lo = mid + 1; }
        else hi = mid - 1;
    }
    if (found < 0 || elapsedMs > data.durationMs || elapsedMs - samples[found].elapsedMs > Math.max(500, data.telemetry.nominalSampleIntervalMs * 3)) return null;
    return samples[found];
}

function initializeRecordedSession() {
    const video = document.getElementById('sessionVideo');
    if (!video) return;
    const status = document.getElementById('sessionStatus');
    const telemetry = document.getElementById('sessionTelemetry');
    const videoInput = document.getElementById('openRecording');
    const metadataInput = document.getElementById('openRecordingMetadata');
    let url = null, filename = null, metadata = null, revision = 0, savedControls = null;
    const controlIds = ['micButton', 'recordButton', 'packageSelect', 'playState', 'restartState', 'stateTimeline'];
    function update() {
        if (!metadata) { telemetry.textContent = 'No linked telemetry. Video can play without metadata.'; return; }
        const sample = recordingSampleAt(metadata, video.currentTime * 1000);
        telemetry.textContent = sample
            ? `Recorded time ${video.currentTime.toFixed(1)}s • Microphone level ${sample.microphoneLevel.toFixed(4)} • Hue ${sample.hueDegrees.toFixed(1)}° • Audio response ${sample.resonance.toFixed(4)} • Root ${sample.rootValue}`
            : `Recorded time ${video.currentTime.toFixed(1)}s • No sample available here (start or sampling gap).`;
    }
    function close() {
        revision++;
        video.pause();
        video.removeAttribute('src');
        video.load();
        if (url) URL.revokeObjectURL(url);
        url = filename = metadata = null;
        videoInput.value = metadataInput.value = '';
        document.getElementById('sessionMetadataReview').textContent = '';
        if (savedControls) for (const [id, disabled] of Object.entries(savedControls)) document.getElementById(id).disabled = disabled;
        savedControls = null;
        status.textContent = 'No recording loaded. Files stay on this device.';
        update();
    }
    videoInput.onchange = () => {
        const file = videoInput.files[0];
        if (!file) return;
        if (typeof window.prepareRecordedSession === 'function' && !window.prepareRecordedSession()) { status.textContent = 'Stop and finish saving the active recording first.'; videoInput.value = ''; return; }
        revision++;
        video.pause();
        if (url) URL.revokeObjectURL(url);
        if (!savedControls) savedControls = Object.fromEntries(controlIds.map(id => [id, document.getElementById(id).disabled]));
        for (const id of controlIds) document.getElementById(id).disabled = true;
        metadata = null;
        metadataInput.value = '';
        document.getElementById('sessionMetadataReview').textContent = '';
        filename = file.name;
        url = URL.createObjectURL(file);
        video.src = url;
        video.load();
        status.textContent = `Recorded Session: ${filename}. Optional: open its matching metadata.`;
        update();
    };
    metadataInput.onchange = async () => {
        const file = metadataInput.files[0];
        if (!file) return;
        const expectedRevision = revision;
        try {
            if (!filename) throw new Error('Open the video recording first.');
            if (file.size > 20 * 1024 * 1024) throw new Error('Metadata is larger than the 20 MB preview limit.');
            const candidate = validateRecordingMetadata(JSON.parse(await file.text()), filename);
            if (expectedRevision !== revision) return;
            if (Number.isFinite(video.duration) && Math.abs(video.duration * 1000 - candidate.durationMs) > Math.max(1000, candidate.durationMs * .05)) throw new Error('Metadata duration does not match the video.');
            metadata = candidate;
            status.textContent = `Recorded Session: ${filename} • metadata matched by filename, ${metadata.telemetry.timeline.length} samples. No integrity hash is present in this format.`;
            document.getElementById('sessionMetadataReview').textContent = JSON.stringify(metadata, null, 2);
            update();
        } catch (error) {
            if (expectedRevision !== revision) return;
            status.textContent = `Metadata not loaded: ${error.message}${metadata ? ' Previous metadata retained.' : ''}`;
        } finally { metadataInput.value = ''; }
    };
    for (const event of ['timeupdate', 'seeked', 'loadedmetadata', 'pause', 'ended', 'ratechange']) video.addEventListener(event, update);
    video.addEventListener('error', () => { if (filename) status.textContent = 'This recording cannot be played in this browser. Try a supported WebM/MP4 file.'; });
    document.getElementById('closeRecording').onclick = close;
    window.addEventListener('pagehide', close);
    update();
}
if (typeof module !== 'undefined') module.exports = {validateRecordingMetadata, recordingSampleAt};
if (typeof document !== 'undefined') document.addEventListener('DOMContentLoaded', initializeRecordedSession);
