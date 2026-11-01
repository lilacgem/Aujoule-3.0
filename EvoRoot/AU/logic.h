#ifndef LOGIC_H
#define LOGIC_H

typedef struct {
    int intensity;
    float focus_ratio;
    char primary_initial;
    char pattern_style[40];
    char symbol_density[40];
    char color_hue[40];
    char pattern_complexity[40];
} SymbolCode;

SymbolCode CalculateSymbolAttributes(int intensity, float focus, char initial);

#endif