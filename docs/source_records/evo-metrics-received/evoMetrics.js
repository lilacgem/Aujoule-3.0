// --- [ EVO METRICS ENGINE ] ---
// Root formula preserved from logic.h / logic.c. Extended with the
// leftover-carry gate system and shape parameters that make the math
// visible in the seal itself, not just computed behind the scenes.

const ROOT_FREQ = 360;
const EVO_FREQ = 369;
const OFFSET = 9;
const EVO_MODIFIER = 369.0;

const VOID = 0;
const ENERGY = 1;
const GENESIS_LEVEL = VOID + ENERGY; // C = A + B = 1

const CONSTRAINT_DIGITS = [1, 2, 4, 5, 7, 8];
const SACRED_DIGITS = [3, 6, 9];

/**
 * Digital root: repeatedly sum a number's digits until one digit remains.
 * e.g. 44 -> 4+4 -> 8
 */
function digitalRoot(n) {
    const abs = Math.abs(Math.round(n));
    if (abs === 0) return 0;
    const r = abs % 9;
    return r === 0 ? 9 : r;
}

function isResonanceGate(level) {
    return SACRED_DIGITS.includes(digitalRoot(level));
}

/**
 * The original root formula, unchanged:
 *   evolutionDelta = (intensity * focus) + (newVariable * 369)
 * intensity: real voice spectral energy (bass+mid+high average, 0-1)
 * focus: real camera brightness (luma average, 0-1)
 * newVariable: grows slowly with session count
 */
function calculateEvolutionDelta({ intensity, focus, newVariable }) {
    return (intensity * focus) + (newVariable * EVO_MODIFIER);
}

/**
 * Splits a number into its leading digits (leftover) and its final digit
 * (used). Single-digit numbers have no leftover - the whole thing is used.
 * This is the exact mechanic behind: 13 -> leftover 1, used 3.
 */
function splitLeftoverAndUsed(n) {
    const abs = Math.abs(Math.round(n));
    const str = String(abs);
    if (str.length <= 1) {
        return { leftover: 0, used: abs };
    }
    const used = Number(str[str.length - 1]);
    const leftoverRaw = Math.floor(abs / 10);
    const leftover = leftoverRaw <= 9 ? leftoverRaw : digitalRoot(leftoverRaw);
    return { leftover, used };
}

/**
 * One full step of evolution for a session.
 *   - storedLeftover: the leftover carried from this identity's last round
 *   - evolutionDelta: this round's real, formula-derived number
 * Returns the new level, whether a gate opened, and the leftover to store
 * for next time. No reset logic - the level always keeps climbing forward.
 */
function stepEvolution(storedLeftover, evolutionDelta) {
    const sessionNumber = Math.max(1, Math.round(Math.abs(evolutionDelta) * 100));
    const reduced = digitalRoot(sessionNumber);
    const newLevel = storedLeftover + reduced;
    const { leftover: nextLeftover } = splitLeftoverAndUsed(sessionNumber);
    const gate = isResonanceGate(newLevel);

    return {
        sessionNumber,
        newLevel,
        nextLeftover,
        digitalRootOfLevel: digitalRoot(newLevel),
        isGate: gate
    };
}

/**
 * Maps the current level's digital root into the seal's actual shape.
 * Constraint digits (1,2,4,5,7,8) become the torus knot's winding count -
 * the shape literally gets more complex/constrained. A gate (3,6,9)
 * collapses the shape to a plain, unknotted ring: p=1, q=1.
 * p and q are always 1-9, so the geometry can never break.
 */
function getSealShapeParams(level) {
    const root = digitalRoot(level);
    if (SACRED_DIGITS.includes(root)) {
        return { p: 1, q: 1, isGate: true };
    }
    // q takes a neighboring constraint digit for variety, never 0
    const idx = CONSTRAINT_DIGITS.indexOf(root);
    const q = CONSTRAINT_DIGITS[(idx + 2) % CONSTRAINT_DIGITS.length];
    return { p: root, q, isGate: false };
}

/**
 * Full pipeline for one seal-generation event. Call this with real
 * session signals and the identity's prior stored state.
 */
function generateSeal({ voiceEnergy, cameraBrightness, sessionCount, priorLeftover }) {
    const intensity = Math.min(1, Math.max(0, voiceEnergy));
    const focus = Math.min(1, Math.max(0, cameraBrightness));
    const newVariable = Math.min(1, sessionCount * 0.01);

    const evolutionDelta = calculateEvolutionDelta({ intensity, focus, newVariable });
    const step = stepEvolution(priorLeftover ?? GENESIS_LEVEL, evolutionDelta);
    const shape = getSealShapeParams(step.newLevel);

    return {
        evolutionDelta: Number(evolutionDelta.toFixed(4)),
        g_root_level: step.newLevel,
        digital_root: step.digitalRootOfLevel,
        next_leftover: step.nextLeftover,
        is_gate: step.isGate,
        shape,
        message: step.isGate
            ? 'Resonance: Golden Glow Active. A gate has opened.'
            : 'Growth in progress. Following the natural cycle.'
    };
}

/**
 * Finds this identity's most recent leftover and session count from
 * the existing seal history, so evolution persists across visits.
 */
function getPriorEvolutionState(existingDatabase, sovereignId) {
    const priorEntries = existingDatabase.filter(
        entry => entry.identity_metadata?.sovereign_id === sovereignId
    );

    if (priorEntries.length === 0) {
        return { priorLeftover: GENESIS_LEVEL, sessionCount: 0 };
    }

    const lastEntry = priorEntries[priorEntries.length - 1];
    const priorLeftover = lastEntry.evo_metrics?.next_leftover ?? GENESIS_LEVEL;

    return { priorLeftover, sessionCount: priorEntries.length };
}

module.exports = {
    generateSeal,
    getPriorEvolutionState,
    calculateEvolutionDelta,
    stepEvolution,
    splitLeftoverAndUsed,
    getSealShapeParams,
    digitalRoot,
    isResonanceGate,
    ROOT_FREQ,
    EVO_FREQ,
    OFFSET,
    GENESIS_LEVEL,
    CONSTRAINT_DIGITS,
    SACRED_DIGITS
};
