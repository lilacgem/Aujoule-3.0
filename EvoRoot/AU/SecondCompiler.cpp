#include <iostream>
#include <string>
#include <fstream>

extern "C" {
#include "logic.h"
}

int main() {
    std::cout << "=== AUEVO SECOND COMPILER INITIATED ===" << std::endl;

    int prior_state_version = 0;
    int prior_intensity = 0;
    float prior_focus = 0.0f;
    char prior_initial = '\0';

    std::string prior_pattern_style;
    std::string prior_color_hue;
    std::string prior_resonance;

    std::ifstream state_in("compiler2_state.txt");

    if (state_in.is_open()) {
        state_in >> prior_state_version;
        state_in >> prior_intensity;
        state_in >> prior_focus;
        state_in >> prior_initial;

        state_in.ignore();

        std::getline(state_in, prior_pattern_style);
        std::getline(state_in, prior_color_hue);
        std::getline(state_in, prior_resonance);

        state_in.close();
    }

    int state_version = prior_state_version + 1;

    int intensity;
    float focus;
    char initial;

    std::cout << "Intensity (1-10): ";
    std::cin >> intensity;

    std::cout << "Focus (0.0-1.0): ";
    std::cin >> focus;

    std::cout << "Primary initial: ";
    std::cin >> initial;

    SymbolCode legacy_output = CalculateSymbolAttributes(intensity, focus, initial);
    bool intensity_changed = (prior_intensity != legacy_output.intensity);
    bool focus_changed = (prior_focus != legacy_output.focus_ratio);
    bool initial_changed = (prior_initial != legacy_output.primary_initial);

    bool pattern_changed =
        (prior_pattern_style != legacy_output.pattern_style);

    bool color_changed =
        (prior_color_hue != legacy_output.color_hue);


    std::cout << "{" << std::endl;

    std::cout << "  \"compiler\": \"AUEVO-SecondCompiler\"," << std::endl;
    std::cout << "  \"source\": \"Compiler-1-SymbolCode\"," << std::endl;
    std::cout << "  \"lineage\": \"Compiler-1-to-Compiler-2\"," << std::endl;
    std::cout << "  \"schema\": \"EvoMirror-State/v2\"," << std::endl;
    std::cout << "  \"prior_state_version\": " << prior_state_version << "," << std::endl;
    std::cout << "  \"state_version\": " << state_version << "," << std::endl;
    std::cout << "  \"changes\": {" << std::endl;
    std::cout << "    \"intensity\": " << (intensity_changed ? "true" : "false") << "," << std::endl;
    std::cout << "    \"focus\": " << (focus_changed ? "true" : "false") << "," << std::endl;
    std::cout << "    \"initial\": " << (initial_changed ? "true" : "false") << "," << std::endl;
    std::cout << "    \"pattern_style\": " << (pattern_changed ? "true" : "false") << "," << std::endl;
    std::cout << "    \"color_hue\": " << (color_changed ? "true" : "false") << std::endl;
    std::cout << "  }," << std::endl;
    std::cout << "  \"intensity\": " << legacy_output.intensity << "," << std::endl;
    std::cout << "  \"focus_ratio\": " << legacy_output.focus_ratio << "," << std::endl;
    std::cout << "  \"primary_initial\": \"" << legacy_output.primary_initial << "\"," << std::endl;
    std::cout << "  \"pattern_style\": \"" << legacy_output.pattern_style << "\"," << std::endl;
    std::cout << "  \"color_hue\": \"" << legacy_output.color_hue << "\"," << std::endl;
    std::cout << "  \"resonance\": \"369\"" << std::endl;
    std::cout << "}" << std::endl;

    // This stops the window from closing instantly when you press Ctrl + F5
    std::cout << "\nPress Enter to exit..." << std::endl;
    std::cin.get();

    std::ofstream state_out("compiler2_state.txt");

    if (state_out.is_open()) {
        state_out << state_version << std::endl;
        state_out << legacy_output.intensity << std::endl;
        state_out << legacy_output.focus_ratio << std::endl;
        state_out << legacy_output.primary_initial << std::endl;
        state_out << legacy_output.pattern_style << std::endl;
        state_out << legacy_output.color_hue << std::endl;
        state_out << "369" << std::endl;

        state_out.close();
    }

    return 0;
}