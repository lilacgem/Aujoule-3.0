#ifndef AUEVO_STATE_COMPILER_H
#define AUEVO_STATE_COMPILER_H

struct EvoInput
{
    int intensity;
    float focus;
    float activity;
    float complexity;
};

struct OrbState
{
    int intensity;
    float focus;

    float glow;
    float density;
    float motion;
    float complexity;
    float coreIntensity;

    const char* primaryColor;
    const char* secondaryColor;
    const char* coreColor;

    int resonance;
};

OrbState compileState(const EvoInput& input);

#endif