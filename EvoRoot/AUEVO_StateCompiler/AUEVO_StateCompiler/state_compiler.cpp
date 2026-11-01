#include "state_compiler.h"
#include <algorithm>

OrbState compileState(const EvoInput& input)
{
    OrbState state{};

    state.intensity = input.intensity;
    state.focus = input.focus;

    state.glow = std::clamp(
        input.intensity / 10.0f,
        0.0f,
        1.0f
    );

    state.density = std::clamp(
        (input.focus + input.complexity) / 2.0f,
        0.0f,
        1.0f
    );

    state.motion = std::clamp(
        input.activity,
        0.0f,
        1.0f
    );

    state.complexity = std::clamp(
        input.complexity,
        0.0f,
        1.0f
    );

    state.coreIntensity = std::clamp(
        (state.glow + input.focus) / 2.0f,
        0.0f,
        1.0f
    );

    // Initial EvoSpace Orb palette
    state.primaryColor = "#D62BB7";
    state.secondaryColor = "#27BDE2";
    state.coreColor = "#FFD98A";

    // Canonical AUEVO prototype resonance
    state.resonance = 369;

    return state;
}