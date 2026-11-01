#include "logic.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

int g_root_level = 55;

SymbolCode CalculateSymbolAttributes(int intensity, float focus, char initial) {
    SymbolCode result_symbol;

    // Clear out memory safely first
    memset(&result_symbol, 0, sizeof(SymbolCode));

    result_symbol.intensity = intensity;
    result_symbol.focus_ratio = focus;
    result_symbol.primary_initial = initial;

    int void_modifier = 0;

    if (intensity >= 7) {
        g_root_level += 9;
    }
    else {
        g_root_level -= 3;
    }

    if (g_root_level < 0) g_root_level = 0;
    if (g_root_level > 100) g_root_level = 100;

    if (intensity < 4 || initial == 'L' || initial == 'T') {
        void_modifier = rand() % 100;
    }

    if (intensity == 10) {
        snprintf(result_symbol.pattern_style, sizeof(result_symbol.pattern_style), "%s", "InnerGlow Fractal Nodes");
        if (focus >= 0.8) {
            snprintf(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "%s", "HIGH (Concentrated Aura)");
        }
        else {
            snprintf(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "%s", "MODERATE (Balanced Flow)");
        }
    }
    else if (intensity >= 7) {
        snprintf(result_symbol.pattern_style, sizeof(result_symbol.pattern_style), "%s", "Deep Thinking Fractal Geometry");
        if (focus >= 0.5) {
            snprintf(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "%s", "MODERATE (Balanced)");
        }
        else {
            snprintf(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "%s", "LOW (Dispersed Seed)");
        }
    }
    else {
        snprintf(result_symbol.pattern_style, sizeof(result_symbol.pattern_style), "%s", "Minimal Ethereal Curves");
        snprintf(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "%s", "LOW (Dispersed)");

        int threshold = 36 + (g_root_level / 3);
        if (void_modifier > threshold) {
            snprintf(result_symbol.pattern_complexity, sizeof(result_symbol.pattern_complexity), "%s", "AUEVO SEAL DNA SPILLOVER");
        }
        else if (void_modifier > 30) {
            snprintf(result_symbol.pattern_complexity, sizeof(result_symbol.pattern_complexity), "%s", "FRACTAL EVOLUTION");
        }
        else {
            snprintf(result_symbol.pattern_complexity, sizeof(result_symbol.pattern_complexity), "%s", "BASIC GEOMETRY");
        }
    }

    if (initial == 'L' || initial == 'J') {
        snprintf(result_symbol.color_hue, sizeof(result_symbol.color_hue), "%s", "Gold");
    }
    else if (initial == 'A' || initial == 'E') {
        snprintf(result_symbol.color_hue, sizeof(result_symbol.color_hue), "%s", "Teal");
    }
    else if (initial == 'S' || initial == 'V') {
        snprintf(result_symbol.color_hue, sizeof(result_symbol.color_hue), "%s", "Midnight");
    }
    else {
        snprintf(result_symbol.color_hue, sizeof(result_symbol.color_hue), "%s", "InnerGlow Neutral");
    }

    return result_symbol;
}