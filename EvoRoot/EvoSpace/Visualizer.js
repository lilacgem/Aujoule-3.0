/**
* @file visualizer.js
* @description Procedural Fluid Mirror Core with microphone recording telemetry
*/

const BrandConfig = {
name: 'AuEvo',
legal: 'AuEvo Collective',
project: 'AuEvo Mirror',
};

let evoState = null;
let statePlayback = null;

function validateDisplayState(state) {
    if (!state || state.schema !== 'EvoMirror-State/v3' || !state.orb) throw new Error('Unsupported state format.');
    for (const key of ['glow', 'density', 'motion', 'complexity', 'coreIntensity']) {
        if (!Number.isFinite(state.orb[key]) || state.orb[key] < 0 || state.orb[key] > 1) throw new Error(`Invalid Orb value: ${key}`);
    }
    for (const key of ['primaryColor', 'secondaryColor', 'coreColor']) {
        if (!/^#[0-9a-f]{6}$/i.test(state.orb[key])) throw new Error(`Invalid Orb color: ${key}`);
    }
}

function displayState(state) {
    validateDisplayState(state);
    applyEvoState(state);
    evoState = state;
    const status = document.getElementById('stateStatus');
    const prototype = state.prototype;
    if (status) status.textContent = prototype
        ? `Prototype baseline • generation ${prototype.generation} • lineage incomplete`
        : 'Legacy baseline • provenance unverified';
    if (status) status.title = prototype?.stateId || '';
    if (prototype) {
        // These prototype permissions permit a baseline view only, not microphone use or recording.
        document.getElementById('micButton').disabled = true;
        document.getElementById('micButton').innerText = 'BASELINE VIEW — MICROPHONE OFF';
        document.getElementById('recordButton').disabled = true;
    }
}

async function loadEvoState() {
    try {
        const response = await fetch('./evo_state.json', {cache: 'no-store'});
        if (!response.ok) throw new Error(`State load failed: ${response.status}`);
        displayState(await response.json());
        console.log('AUEVO compiled state loaded:', evoState);
        if (evoState.prototype) await loadPackageChoices();
    } catch (error) {
        console.error('Unable to load AUEVO compiled state:', error);
        const status = document.getElementById('stateStatus');
        if (status) status.textContent = evoState ? 'Load failed — previous state retained' : 'Ambient fallback — no valid compiled state';
    }
}

async function loadPackageChoices() {
    const response = await fetch('/api/packages', {cache: 'no-store'});
    if (!response.ok) throw new Error('Unable to list saved packages.');
    const choices = await response.json();
    const select = document.getElementById('packageSelect');
    for (const choice of choices) {
        const option = document.createElement('option');
        option.value = choice.index;
        option.textContent = `${choice.name} — generation ${choice.generation}`;
        select.appendChild(option);
    }
    document.getElementById('packageControls').hidden = false;
    let selected = select.value;
    select.onchange = async () => {
        if (statePlayback) statePlayback.pause();
        select.disabled = true;
        try {
            const response = await fetch(`/api/state?index=${encodeURIComponent(select.value)}`, {cache: 'no-store'});
            if (!response.ok) throw new Error('Unable to load selected package.');
            displayState(await response.json());
            selected = select.value;
            if (statePlayback) {
                const frame = statePlayback.frames.find(frame => String(frame.packageIndex) === selected);
                if (frame) statePlayback.seek(frame.atMs);
            }
        } catch (error) {
            select.value = selected;
            document.getElementById('stateStatus').textContent = 'Load failed — previous state retained';
            console.error(error);
        } finally { select.disabled = false; }
    };
    await loadStatePlayback(select, value => { selected = value; });
}

async function loadStatePlayback(select, rememberSelection) {
    try {
        const response = await fetch('/api/timeline', {cache: 'no-store'});
        if (!response.ok) throw new Error('State timeline unavailable.');
        const timeline = await response.json();
        if (timeline.schema !== 'AUEVO-StateTimeline/v0.1' || timeline.timingOrigin !== 'configured-demo' || !Array.isArray(timeline.frames)) throw new Error('Unsupported state timeline.');
        for (const frame of timeline.frames) {
            validateDisplayState(frame.state);
            if (!frame.state.prototype || !Number.isInteger(frame.packageIndex) || frame.packageIndex < 0 || frame.packageIndex >= select.options.length) throw new Error('Invalid timeline reference.');
        }
        const range = document.getElementById('stateTimeline');
        const button = document.getElementById('playState');
        const status = document.getElementById('playbackStatus');
        const formatTime = ms => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`;
        statePlayback = new StatePlayback(timeline.frames, timeline.durationMs, {
            onState: frame => {
                displayState(frame.state);
                select.value = String(frame.packageIndex);
                rememberSelection(select.value);
            },
            onUpdate: (position, playing) => {
                range.value = position;
                range.setAttribute('aria-valuetext', `${formatTime(position)} of ${formatTime(timeline.durationMs)}`);
                document.getElementById('playbackTime').textContent = `${formatTime(position)} / ${formatTime(timeline.durationMs)}`;
                button.textContent = playing ? 'Pause states' : 'Play states';
                const text = position === timeline.durationMs ? 'Ended' : playing ? 'Playing' : 'Paused';
                if (status.textContent !== text) status.textContent = text;
            }
        });
        range.max = timeline.durationMs;
        button.onclick = () => statePlayback.playing ? statePlayback.pause() : statePlayback.play();
        document.getElementById('restartState').onclick = () => statePlayback.restart();
        range.oninput = () => { const position = Number(range.value); statePlayback.pause(); statePlayback.seek(position); };
        document.getElementById('playbackControls').hidden = false;
    } catch (error) {
        console.error('State playback unavailable:', error);
        document.getElementById('playbackStatus').textContent = 'Playback unavailable; saved-state selection still works.';
        document.getElementById('playbackControls').hidden = false;
        for (const id of ['playState', 'restartState', 'stateTimeline']) document.getElementById(id).disabled = true;
    }
}

function applyEvoState(state) {
    if (!state || !state.orb) return;

    const orb = state.orb;

    // Preserve the compiled Orb as the baseline.
    compiledMotion = THREE.MathUtils.clamp(
        orb.motion,
        0.01,
        1.0
    );

    compiledComplexity = THREE.MathUtils.clamp(
        orb.complexity,
        0.01,
        1.0
    );

    compiledDensity = THREE.MathUtils.clamp(
        orb.density,
        0.0,
        1.0
    );

    compiledGlow = THREE.MathUtils.clamp(
        orb.glow,
        0.0,
        1.0
    );

    compiledCoreIntensity = THREE.MathUtils.clamp(
        orb.coreIntensity,
        0.0,
        1.0
    );

    if (orb.primaryColor) {
        const color = new THREE.Color(orb.primaryColor);
        const hsl = {};

        color.getHSL(hsl);
        compiledHue = hsl.h;
    }

    // Initialize the live Orb from the compiled baseline.
    dynamicFactor = compiledComplexity;
    coreBrilliance =
        0.75 + (compiledCoreIntensity * 4.0);

    baseStarSpeed =
        0.0005 + (compiledMotion * 0.01);

    colorAccumulator = compiledHue;

    mirrorMaterial.uniforms.hueShift.value =
        compiledHue;

    mirrorMaterial.uniforms.satMul.value =
        0.75 + (compiledDensity * 0.75);

    mirrorMaterial.uniforms.lightMul.value =
        0.7 + (compiledGlow * 0.8);

    mirrorMaterial.uniforms.factor.value =
        dynamicFactor;

    mirrorMaterial.uniforms.brilliance.value =
        coreBrilliance;

    console.log('AUEVO compiled baseline established:', {
        motion: compiledMotion,
        complexity: compiledComplexity,
        density: compiledDensity,
        glow: compiledGlow,
        coreIntensity: compiledCoreIntensity,
        hue: compiledHue
    });
}
console.log('âš¡ [AUJOULE] Initializing Pure Procedural Fluid Mirror Core...');

// --- 1. CORE SYSTEM SCENE SETTING ---
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ 
canvas: document.querySelector('#bg'),
alpha: true,
preserveDrawingBuffer: true 
});

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x000002, 1);
camera.position.z = 44;

let mouseX = 0, mouseY = 0;
let dynamicFactor = 0.05;
let colorAccumulator = 0.5; 
let coreBrilliance = 1.0;
let baseStarSpeed = 0.0005;
let compiledMotion = 0.05;
let compiledComplexity = 0.05;
let compiledDensity = 0.5;
let compiledGlow = 0.5;
let compiledCoreIntensity = 1.0;
let compiledHue = 0.5;

const resonanceSettings = {
hueOffset: 0.08,
sensitivity: 2.0,
colorBoost: 0.22
};

window.addEventListener('mousemove', (event) => {
mouseX = (event.clientX / window.innerWidth) * 2 - 1;
mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
});

// --- 2. KINETIC DRIFT STARFIELD SYSTEM ---
const starCount = 3500;
const starGeometry = new THREE.BufferGeometry();
const starPositions = new Float32Array(starCount * 3);

for (let i = 0; i < starCount * 3; i += 3) {
starPositions[i] = (Math.random() - 0.5) * 200;
starPositions[i+1] = (Math.random() - 0.5) * 200;
starPositions[i+2] = (Math.random() - 0.5) * 100 - 50;
}

starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
const starMaterial = new THREE.PointsMaterial({ 
color: 0xffffff, 
size: 0.45, 
transparent: true, 
opacity: 0.6,
blending: THREE.AdditiveBlending 
});
const stars = new THREE.Points(starGeometry, starMaterial);
scene.add(stars);

// --- 3. HIGH-INTENSITY PROCEDURAL SHADERS ---
const vertexShader = `
varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vScreenPos;
varying vec3 vLocalPos;
uniform float time;
uniform float factor;

vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
float snoise(vec2 v){
const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
vec2 i = floor(v + dot(v, C.yy) );
vec2 x0 = v - i + dot(i, C.xx);
vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
vec4 x12 = x0.xyxy + C.xxzz; x12.xy -= i1; i = mod(i, 289.0);
vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 )) + i.x + vec3(0.0, i1.x, 1.0 ));
vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
m = m*m ; m = m*m ;
vec3 x = 2.0 * fract(p * C.www) - 1.0; vec3 h = abs(x) - 0.5; vec3 ox = floor(x + 0.5); vec3 a0 = x - ox;
m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
vec3 g; g.x = a0.x * x0.x + h.x * x0.y; g.yz = a0.yz * x12.xz + h.yz * x12.yw;
return 130.0 * dot(m, g);
}

void main() {
vUv = uv; vNormal = normalize(normalMatrix * normal); vLocalPos = position;
vec3 pos = position;

float noiseFreq = 0.18;

float primaryNoise =
    snoise(pos.xy * noiseFreq + time * 0.35);

float secondaryNoise =
    snoise(pos.yz * 0.24 - time * 0.28);

float tertiaryNoise =
    snoise(pos.zx * 0.20 + time * 0.22);

float displacement =
    primaryNoise * (1.5 + factor * 7.0);

displacement +=
    secondaryNoise * (0.8 + factor * 4.0);

displacement +=
    tertiaryNoise * (0.5 + factor * 2.5);

vec3 morphed = pos + normal * displacement;

vec4 mvPosition = modelViewMatrix * vec4(morphed, 1.0);

gl_Position = projectionMatrix * mvPosition;

vScreenPos = gl_Position.xyz / gl_Position.w;
}
`;

const fragmentShader = `
uniform float time; uniform float factor; uniform float satMul; uniform float lightMul; uniform float hueShift; uniform float brilliance;
varying vec2 vUv; varying vec3 vNormal; varying vec3 vScreenPos; varying vec3 vLocalPos;

vec3 hsl2rgb(vec3 c) {
vec3 rgb = clamp(abs(mod(c.x*6.0+vec3(0.0,4.0,2.0),6.0)-3.0)-1.0, 0.0, 1.0);
return c.z + c.y * (rgb-0.5)*(1.0-abs(2.0*c.z-1.0));
}

void main() {
vec3 nNormal = normalize(vNormal);
float surfaceNoise =
    sin(vLocalPos.x * 0.18 + time * 0.30) *
    cos(vLocalPos.y * 0.15 - time * 0.24);

float secondarySurface =
    sin(
        (vLocalPos.x + vLocalPos.y + vLocalPos.z) * 0.24
        - time * 0.38
    );

surfaceNoise =
    surfaceNoise * 0.72 +
    secondarySurface * 0.28;
float sat = clamp(0.85 * satMul, 0.0, 1.0);
float light = clamp(0.45 * lightMul, 0.0, 1.0);
vec3 fluidBaseColor = hsl2rgb(
    vec3(
        mod(hueShift + surfaceNoise * 0.08, 1.0),
        sat,
        light
    )
);
float lightAngle = max(dot(nNormal, vec3(0.3, 0.3, 1.0)), 0.0);
vec3 dynamicEmissive = fluidBaseColor * (0.7 + lightAngle * 1.0 + factor * 1.5);
float flowA =
    sin(
        vLocalPos.x * 0.28 +
        vLocalPos.z * 0.12 +
        time * 1.25
    );

float flowB =
    cos(
        vLocalPos.y * 0.31 -
        vLocalPos.z * 0.16 -
        time * 1.05
    );

float flowC =
    sin(
        (vLocalPos.x + vLocalPos.y) * 0.18 +
        time * 0.65
    );

float currentLine =
    abs(flowA * flowB * 0.75 + flowC * 0.25);
float currentGlow = pow(1.0 - smoothstep(0.0, 0.12 + (factor * 0.2), currentLine), 3.0);
vec3 plasmaCurrentColor =
    hsl2rgb(
        vec3(mod(hueShift + 0.04, 1.0), 0.9, 0.6)
    ) * currentGlow * (0.35 + factor * 3.2);
float fresnel = pow(1.0 - max(dot(nNormal, vec3(0.0, 0.0, 1.0)), 0.0), 3.0);
vec3 outerHaloColor =
    hsl2rgb(
        vec3(mod(hueShift + 0.02, 1.0), 0.9, 0.5)
    );
vec3 atmosphericHalo =
    outerHaloColor *
    fresnel *
    (1.2 + factor * 3.2) *
    (0.45 + brilliance * 0.45);
float radialDistance = length(vScreenPos.xy);
float coreSoftFlare =
    pow(
        max(1.0 - radialDistance, 0.0),
        5.0
    );

float coreAura =
    pow(
        max(1.0 - radialDistance * 0.72, 0.0),
        8.0
    );

vec3 centralLightBoost =
    vec3(1.0, 0.94, 1.0) *
    (
        coreSoftFlare * (0.25 + factor * 1.4) +
        coreAura * (brilliance * 0.18)
    );

vec3 finalMix = mix(dynamicEmissive, atmosphericHalo, 0.3 + fresnel * 0.4) + plasmaCurrentColor + centralLightBoost;
finalMix *= 1.25; finalMix = clamp(finalMix, 0.0, 1.0); finalMix = pow(finalMix, vec3(0.92));
gl_FragColor = vec4(finalMix, 0.98);
}
`;

// --- 4. PRODUCTION ENGINE GEOMETRY COMPILATION ---
const geometry = new THREE.SphereGeometry(16, 96, 96); 
const mirrorMaterial = new THREE.ShaderMaterial({
uniforms: {
time: { value: 0.0 }, factor: { value: 0.05 }, hueShift: { value: 0.5 },
satMul: { value: 1.0 }, lightMul: { value: 1.0 }, brilliance: { value: 1.0 }
},
vertexShader: vertexShader, fragmentShader: fragmentShader, transparent: true, side: THREE.DoubleSide
});
const mirrorSphere = new THREE.Mesh(geometry, mirrorMaterial);
scene.add(mirrorSphere);

loadEvoState();

console.log('ðŸŒŒ Pure mathematical color spectrum matrix locked and active.');

// --- 5. ADVANCED SOUND DECODER & TELEMETRY LABS ---
let audioContext, analyser, dataArray;
let micStream = null; let canvasStream = null; let recordingStream = null;
let mediaRecorder = null; let recordedChunks = [];
const micButton = document.getElementById('micButton');
const recordButton = document.getElementById('recordButton');

micButton.onclick = async () => {
if (audioContext) return;
try {
const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
micStream = stream;
audioContext = new (window.AudioContext || window.webkitAudioContext)();
const source = audioContext.createMediaStreamSource(stream);

analyser = audioContext.createAnalyser();
analyser.fftSize = 256;
dataArray = new Uint8Array(analyser.frequencyBinCount);

source.connect(analyser);
canvasStream = document.querySelector('#bg').captureStream(30);

micButton.innerText = "MIRROR CORE ENGAGED";
micButton.style.border = "1px solid #00ffaa"; micButton.style.color = "#00ffaa";

const status = document.getElementById('micStatus');
if (status) status.innerText = 'ENGAGED';
if (recordButton) {
recordButton.disabled = false;
recordButton.innerText = 'START RECORDING';
}
} catch (err) {
console.error("Microphone linkage failure:", err);
micButton.innerText = "HARDWARE SYNC ERROR";
const status = document.getElementById('micStatus');
if (status) status.innerText = 'ERROR';
}
};

setTimeout(() => {
const md = document.getElementById('awarenessDisplay'); if (md) md.innerText = 'RESONANT';
const brandEl = document.getElementById('brandName'); if (brandEl) brandEl.innerText = BrandConfig.name;
}, 100);

let recordingTelemetry = null;
let recordingStartTime = 0;
let recordingDurationMs = 0;
let recordingAssetId = '';
let recordingVideoFilename = '';
let recordingResolution = null;
let recordingStopping = false;

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.style.display = 'none';
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function saveRecording() {
    if (!recordedChunks.length) throw new Error('No recording data was captured.');
    const mimeType = mediaRecorder.mimeType || recordedChunks[0].type || 'video/webm';
    const blob = new Blob(recordedChunks, {type: mimeType});
    const metadata = recordingTelemetry.metadata({
        assetId: recordingAssetId,
        videoFilename: recordingVideoFilename,
        durationMs: recordingDurationMs,
        mimeType,
        resolution: recordingResolution,
        sampleRateHz: audioContext.sampleRate
    });
    const metadataJson = JSON.stringify(metadata, null, 2);
    const metadataFilename = `${recordingAssetId}_metadata.json`;
    if (window.JSZip) {
        const zip = new JSZip();
        zip.file(recordingVideoFilename, blob);
        zip.file(metadataFilename, metadataJson);
        const content = await zip.generateAsync({type: 'blob'});
        downloadBlob(content, `${recordingAssetId}.zip`);
    } else {
        downloadBlob(blob, recordingVideoFilename);
        downloadBlob(new Blob([metadataJson], {type: 'application/json'}), metadataFilename);
    }
    recordedChunks = [];
}

function toggleRecording() {
    if (recordingStopping) return;
    if (!micStream) { alert('Start the mirror first before recording.'); return; }
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        if (!canvasStream || !micStream.getAudioTracks().some(track => track.readyState === 'live')) {
            alert('Recording is not available yet.'); return;
        }
        recordingStream = new MediaStream([...canvasStream.getVideoTracks(), ...micStream.getAudioTracks()]);
        try {
            mediaRecorder = new MediaRecorder(recordingStream);
            recordedChunks = [];
            mediaRecorder.ondataavailable = event => {
                if (event.data && event.data.size > 0) recordedChunks.push(event.data);
            };
            mediaRecorder.onstop = async () => {
                // Stop collecting before an asynchronous export can begin.
                recordingDurationMs = recordingDurationMs || performance.now() - recordingStartTime;
                recordingStopping = true;
                if (recordButton) recordButton.disabled = true;
                try { await saveRecording(); }
                catch (error) { console.error(error); alert('Recording export failed. Please try again.'); }
                finally {
                    recordingTelemetry = null;
                    recordingStopping = false;
                    if (recordButton) {
                        recordButton.disabled = false;
                        recordButton.innerText = 'START RECORDING';
                    }
                }
            };
            mediaRecorder.start();
            recordingStartTime = performance.now();
            recordingDurationMs = 0;
            recordingAssetId = `evo_mirror_${Date.now()}_${crypto.randomUUID()}`;
            recordingVideoFilename = `${recordingAssetId}.${mediaRecorder.mimeType.includes('mp4') ? 'mp4' : 'webm'}`;
            recordingResolution = {width: renderer.domElement.width, height: renderer.domElement.height};
            recordingTelemetry = new RecordingTelemetry(new Date().toISOString());
            // Capture fresh microphone values immediately, then approximately every 100 ms.
            processVocalTelemetry();
            if (recordButton) recordButton.innerText = 'STOP RECORDING';
        } catch (error) {
            recordingTelemetry = null;
            console.error(error);
            alert('Recording is not supported in this browser.');
        }
    } else {
        recordingDurationMs = performance.now() - recordingStartTime;
        recordingStopping = true;
        if (recordButton) { recordButton.disabled = true; recordButton.innerText = 'SAVING…'; }
        mediaRecorder.stop();
    }
}

if (recordButton) recordButton.addEventListener('click', toggleRecording);

function rgbToHex(r, g, b) {
return '#' + [r, g, b].map(v => { const s = v.toString(16); return s.length === 1 ? '0' + s : s; }).join('');
}

// Fixed missing helper function utility layer
function hslToRgb(h, s, l) {
let r, g, b;
if (s === 0) {
r = g = b = l;
} else {
const hue2rgb = (p, q, t) => {
if (t < 0) t += 1; if (t > 1) t -= 1;
if (t < 1/6) return p + (q - p) * 6 * t;
if (t < 1/2) return q;
if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
return p;
};
const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
const p = 2 * l - q;
r = hue2rgb(p, q, h + 1/3);
g = hue2rgb(p, q, h);
b = hue2rgb(p, q, h - 1/3);
}
return { r: Math.round(r * 255), g: Math.round(g * 255), b: Math.round(b * 255) };
}

function calculateDigitalRoot(n) { return n === 0 ? 0 : 1 + ((n - 1) % 9); }

function processVocalTelemetry() {
    if (!analyser) {
        // Hold the compiled state as the idle EvoSpace baseline.
        dynamicFactor = compiledComplexity;

        coreBrilliance =
            0.75 + (compiledCoreIntensity * 4.0);

        baseStarSpeed =
            0.0005 + (compiledMotion * 0.01);

        mirrorMaterial.uniforms.hueShift.value =
            compiledHue;

        mirrorMaterial.uniforms.satMul.value =
            0.75 + (compiledDensity * 0.75);

        mirrorMaterial.uniforms.lightMul.value =
            0.7 + (compiledGlow * 0.8);

        colorAccumulator = compiledHue;

        return;
    }

analyser.getByteFrequencyData(dataArray);
let totalVolume = 0;
for (let i = 0; i < dataArray.length; i++) { totalVolume += dataArray[i]; }

const liveRoot = calculateDigitalRoot(totalVolume);
const rootDisplay = document.getElementById('rootDisplay');
if (rootDisplay) rootDisplay.innerText = liveRoot;

const normalizedVol = totalVolume / (dataArray.length * 255);
const resonance = resonanceSettings;
dynamicFactor = THREE.MathUtils.lerp(dynamicFactor, normalizedVol * 3.4 * resonance.sensitivity + 0.02, 0.22);

const volumeTrigger = Math.max(6, totalVolume * 0.12);
if (totalVolume > volumeTrigger) {
let accelerationScale = 0.004 + (dynamicFactor * 0.02);
colorAccumulator = (colorAccumulator + accelerationScale) % 1.0;
baseStarSpeed = THREE.MathUtils.lerp(baseStarSpeed, 0.01 + (dynamicFactor * 0.04) * resonance.sensitivity, 0.15);

const numericRoot = calculateDigitalRoot(totalVolume);
const rootEl = document.getElementById('rootDisplay');
if (rootEl) rootEl.innerText = numericRoot;

if ([3, 6, 9].includes(numericRoot)) {
coreBrilliance = THREE.MathUtils.lerp(coreBrilliance, 4.0, 0.25);
if (rootEl) rootEl.style.color = '#00ffaa';
} else {
coreBrilliance = THREE.MathUtils.lerp(coreBrilliance, 1.0, 0.1);
if (rootEl) rootEl.style.color = '#ffd700';
}
} else {
dynamicFactor = THREE.MathUtils.lerp(dynamicFactor, 0.01, 0.1);
coreBrilliance = THREE.MathUtils.lerp(coreBrilliance, 1.0, 0.1);
baseStarSpeed = THREE.MathUtils.lerp(baseStarSpeed, 0.0005, 0.05);
}

let centroid = 0, magSum = 0;
const sr = audioContext ? (audioContext.sampleRate || 44100) : 44100;
for (let i = 0; i < dataArray.length; i++) {
const mag = dataArray[i]; const freq = i * (sr / analyser.fftSize);
centroid += freq * mag; magSum += mag;
}
let centroidNorm = 0.5;
if (magSum > 0) centroidNorm = (centroid / magSum) / (sr / 2);

const timeData = new Uint8Array(analyser.fftSize);
analyser.getByteTimeDomainData(timeData);
let sumSq = 0;
for (let i = 0; i < timeData.length; i++) {
const v = (timeData[i] - 128) / 128; sumSq += v * v;
}
const rms = Math.sqrt(sumSq / timeData.length);

const targetHue = (centroidNorm * 1.4 + colorAccumulator * 0.6 + resonance.hueOffset) % 1.0;
const currentHue = mirrorMaterial.uniforms.hueShift.value;
const newHue = THREE.MathUtils.lerp(currentHue, targetHue, 0.22);

mirrorMaterial.uniforms.hueShift.value = newHue;
colorAccumulator = newHue;

const targetSatMul = 0.85 + Math.min(1, rms * 2.2);
const targetLightMul = 0.78 + Math.min(1, rms * 1.6);
mirrorMaterial.uniforms.satMul.value = THREE.MathUtils.lerp(mirrorMaterial.uniforms.satMul.value, targetSatMul, 0.24);
mirrorMaterial.uniforms.lightMul.value = THREE.MathUtils.lerp(mirrorMaterial.uniforms.lightMul.value, targetLightMul, 0.24);

try {
const rgb = hslToRgb(newHue, Math.min(1, mirrorMaterial.uniforms.satMul.value), Math.min(0.95, mirrorMaterial.uniforms.lightMul.value * 0.72));
stars.material.color.set(rgbToHex(rgb.r, rgb.g, rgb.b));
stars.material.size = 0.45 + (rms * 0.8);
} catch(e) {}

document.getElementById('hueDisplay').innerText = `${Math.round((newHue % 1.0) * 360)}°`;
document.getElementById('resDisplay').innerText = dynamicFactor.toFixed(3);
if (recordingTelemetry && mediaRecorder?.state === 'recording' && !recordingStopping) {
    recordingTelemetry.sample(performance.now() - recordingStartTime, {
        microphoneLevel: rms,
        hueDegrees: ((newHue % 1) + 1) % 1 * 360,
        resonance: dynamicFactor,
        rootValue: liveRoot
    });
}
}

// --- 6. MASTER FLUID RUNTIME SYSTEM LOOP ---
function animate() {
requestAnimationFrame(animate);
if (statePlayback) statePlayback.tick();
processVocalTelemetry();

camera.position.x += (mouseX * 5 - camera.position.x) * 0.04;
camera.position.y += (mouseY * 5 - camera.position.y) * 0.04;
camera.lookAt(mirrorSphere.position);

const positions = starGeometry.attributes.position.array;
for (let i = 2; i < positions.length; i += 3) {
positions[i] += baseStarSpeed * 110.0;
if (positions[i] > 50) {
positions[i] = -50;
positions[i-1] = (Math.random() - 0.5) * 200; positions[i-2] = (Math.random() - 0.5) * 200;
}
}
starGeometry.attributes.position.needsUpdate = true;
stars.rotation.z += 0.0002;

mirrorSphere.rotation.y += 0.003 + (dynamicFactor * 0.015);
mirrorSphere.rotation.x += 0.001 + (dynamicFactor * 0.005);

mirrorMaterial.uniforms.time.value = Date.now() * 0.001;
mirrorMaterial.uniforms.factor.value = dynamicFactor;
mirrorMaterial.uniforms.brilliance.value = coreBrilliance;

renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix();
renderer.setSize(window.innerWidth, window.innerHeight);
});
