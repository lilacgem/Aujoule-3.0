/* Deterministic step playback of saved states; no interpolation or inferred timestamps. */
class StatePlayback {
    constructor(frames, durationMs, {clock = () => performance.now(), onState = () => {}, onUpdate = () => {}} = {}) {
        if (!Array.isArray(frames) || !frames.length || frames[0].atMs !== 0 || !Number.isFinite(durationMs) || durationMs <= 0) throw new Error('Invalid state timeline.');
        frames.forEach((frame, index) => {
            if (!Number.isFinite(frame.atMs) || frame.atMs < 0 || frame.atMs >= durationMs || (index && frame.atMs <= frames[index - 1].atMs)) throw new Error('Invalid state timing.');
        });
        this.frames = frames;
        this.durationMs = durationMs;
        this.clock = clock;
        this.onState = onState;
        this.onUpdate = onUpdate;
        this.positionMs = 0;
        this.playing = false;
        this.index = -1;
        this.lastClock = null;
        this.publish();
    }
    publish() {
        let index = 0;
        while (index + 1 < this.frames.length && this.frames[index + 1].atMs <= this.positionMs) index++;
        if (index !== this.index) { this.index = index; this.onState(this.frames[index], index); }
        this.onUpdate(this.positionMs, this.playing);
    }
    tick() {
        if (!this.playing) return;
        const now = this.clock();
        this.positionMs = Math.min(this.durationMs, this.positionMs + Math.max(0, now - this.lastClock));
        this.lastClock = now;
        if (this.positionMs >= this.durationMs) this.playing = false;
        this.publish();
    }
    play() {
        if (this.playing) return;
        if (this.positionMs >= this.durationMs) this.seek(0);
        this.playing = true;
        this.lastClock = this.clock();
        this.publish();
    }
    pause() { this.tick(); this.playing = false; this.lastClock = null; this.publish(); }
    seek(positionMs) {
        if (!Number.isFinite(positionMs)) throw new Error('Invalid playback position.');
        this.positionMs = Math.max(0, Math.min(this.durationMs, positionMs));
        this.lastClock = this.playing ? this.clock() : null;
        if (this.positionMs === this.durationMs) this.playing = false;
        this.publish();
    }
    restart() { this.pause(); this.seek(0); }
}
if (typeof module !== 'undefined') module.exports = StatePlayback;
