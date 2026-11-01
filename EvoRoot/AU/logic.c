#include "logic.h"
#include <string.h>
#include <stdlib.h>

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
        strcpy_s(result_symbol.pattern_style, sizeof(result_symbol.pattern_style), "InnerGlow Fractal Nodes");
        if (focus >= 0.8) {
            strcpy_s(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "HIGH (Concentrated Aura)");
        }
        else {
            strcpy_s(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "MODERATE (Balanced Flow)");
        }
    }
    else if (intensity >= 7) {
        strcpy_s(result_symbol.pattern_style, sizeof(result_symbol.pattern_style), "Deep Thinking Fractal Geometry");
        if (focus >= 0.5) {
            strcpy_s(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "MODERATE (Balanced)");
        }
        else {
            strcpy_s(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "LOW (Dispersed Seed)");
        }
    }
    else {
        strcpy_s(result_symbol.pattern_style, sizeof(result_symbol.pattern_style), "Minimal Ethereal Curves");
        strcpy_s(result_symbol.symbol_density, sizeof(result_symbol.symbol_density), "LOW (Dispersed)");

        int threshold = 36 + (g_root_level / 3);
        if (void_modifier > threshold) {
            strcpy_s(result_symbol.pattern_complexity, sizeof(result_symbol.pattern_complexity), "AUEVO SEAL DNA SPILLOVER");
        }
        else if (void_modifier > 30) {
            strcpy_s(result_symbol.pattern_complexity, sizeof(result_symbol.pattern_complexity), "FRACTAL EVOLUTION");
        }
        else {
            strcpy_s(result_symbol.pattern_complexity, sizeof(result_symbol.pattern_complexity), "BASIC GEOMETRY");
        }
    }

    if (initial == 'L' || initial == 'J') {
        strcpy_s(result_symbol.color_hue, sizeof(result_symbol.color_hue), "Gold");
    }
    else if (initial == 'A' || initial == 'E') {
        strcpy_s(result_symbol.color_hue, sizeof(result_symbol.color_hue), "Teal");
    }
    else if (initial == 'S' || initial == 'V') {
        strcpy_s(result_symbol.color_hue, sizeof(result_symbol.color_hue), "Midnight");
    }
    else {
        strcpy_s(result_symbol.color_hue, sizeof(result_symbol.color_hue), "InnerGlow Neutral");
    }

    return result_symbol;
}