/* Microphone-derived visual measurements; these are not scientific frequency or emotion estimates. */
class RecordingTelemetry {
    constructor(startedAt, intervalMs = 100) {
        this.startedAt = startedAt;
        this.intervalMs = intervalMs;
        this.timeline = [];
    }

    sample(elapsedMs, values) {
        const previous = this.timeline[this.timeline.length - 1];
        if (previous && elapsedMs - previous.elapsedMs < this.intervalMs) return;
        this.timeline.push({
            elapsedMs: Math.round(elapsedMs),
            microphoneLevel: values.microphoneLevel,
            hueDegrees: values.hueDegrees,
            resonance: values.resonance,
            rootValue: values.rootValue
        });
    }

    metadata({assetId, videoFilename, durationMs, mimeType, resolution, sampleRateHz}) {
        const levels = this.timeline.map(sample => sample.microphoneLevel);
        const final = this.timeline[this.timeline.length - 1] || null;
        return {
            schema: 'AuEvo-Recording/v1',
            assetId,
            videoFilename,
            startedAt: this.startedAt,
            durationMs: Math.round(durationMs),
            format: mimeType,
            resolution,
            audio: {sampleRateHz},
            telemetry: {
                source: 'microphone',
                nominalSampleIntervalMs: this.intervalMs,
                description: 'RMS microphone level (0–1), visual hue (degrees), audio-driven visual resonance, and digital root of summed FFT magnitudes. Sampled on animation frames; gaps may occur in background tabs. These are visualizer measurements, not pitch, emotion, or calibrated loudness.',
                summary: {
                    sampleCount: levels.length,
                    averageMicrophoneLevel: levels.length ? levels.reduce((sum, level) => sum + level, 0) / levels.length : null,
                    peakMicrophoneLevel: levels.length ? levels.reduce((peak, level) => Math.max(peak, level), 0) : null,
                    final
                },
                timeline: this.timeline.map(sample => ({...sample}))
            }
        };
    }
}

if (typeof module !== 'undefined') module.exports = RecordingTelemetry;
