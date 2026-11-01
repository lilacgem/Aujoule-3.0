#include <iostream>
#include <fstream>
#include <string>
#include <cmath>
#include <limits>
#include "state_compiler.h"

int main(int argc, char* argv[])
{
    std::cout << "=====================================\n";
    std::cout << "     AUEVO STATE COMPILER\n";
    std::cout << "=====================================\n\n";

    if (argc > 3) { std::cerr << "Usage: state-compiler [input-state] [output-json]\n"; return 1; }
    const std::string inputPath = argc > 1 ? argv[1] : "compiler2_state.txt";
    const std::string outputPath = argc > 2 ? argv[2] : "evo_state.json";
    EvoInput input{};
    std::ifstream compiler2State(inputPath);
    int version;
    char initial;
    std::string pattern, color, resonance;
    if (!(compiler2State >> version >> input.intensity >> input.focus >> initial)) {
        std::cerr << "Unable to read compiler state: " << inputPath << "\n"; return 1;
    }
    compiler2State.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    std::getline(compiler2State, pattern);
    std::getline(compiler2State, color);
    std::getline(compiler2State, resonance);
    if (!resonance.empty() && resonance.back() == '\r') resonance.pop_back();
    if (!compiler2State || version < 1 || input.intensity < 1 || input.intensity > 10 ||
        !std::isfinite(input.focus) || input.focus < 0 || input.focus > 1 || resonance != "369") {
        std::cerr << "Invalid compiler state.\n"; return 1;
    }
    std::cout << "Loaded Compiler 2 State v" << version << "\n";

    std::cout << "Activity (0.0-1.0): ";
    std::cin >> input.activity;

    std::cout << "Complexity (0.0-1.0): ";
    std::cin >> input.complexity;

    if (!std::cin || !std::isfinite(input.activity) || !std::isfinite(input.complexity) ||
        input.activity < 0 || input.activity > 1 || input.complexity < 0 || input.complexity > 1) {
        std::cerr << "Activity and complexity must be numbers from 0 to 1.\n"; return 1;
    }
    OrbState state = compileState(input);

    std::ofstream jsonFile(outputPath);

    if (jsonFile.is_open())
    {
        jsonFile << "{\n";
        jsonFile << "  \"schema\": \"EvoMirror-State/v3\",\n";
        jsonFile << "  \"resonance\": " << state.resonance << ",\n";
        jsonFile << "  \"intensity\": " << state.intensity << ",\n";
        jsonFile << "  \"focus\": " << state.focus << ",\n";

        jsonFile << "  \"orb\": {\n";
        jsonFile << "    \"glow\": " << state.glow << ",\n";
        jsonFile << "    \"density\": " << state.density << ",\n";
        jsonFile << "    \"motion\": " << state.motion << ",\n";
        jsonFile << "    \"complexity\": " << state.complexity << ",\n";
        jsonFile << "    \"coreIntensity\": "
            << state.coreIntensity << ",\n";

        jsonFile << "    \"primaryColor\": \""
            << state.primaryColor << "\",\n";

        jsonFile << "    \"secondaryColor\": \""
            << state.secondaryColor << "\",\n";

        jsonFile << "    \"coreColor\": \""
            << state.coreColor << "\"\n";

        jsonFile << "  }\n";
        jsonFile << "}\n";

        jsonFile.close();
        if (!jsonFile) { std::cerr << "Failed writing state JSON.\n"; return 1; }

        std::cout << "\nState saved to " << outputPath << "\n";
    }
    else
    {
        std::cerr << "Could not create state JSON: " << outputPath << "\n";
        return 1;
    }

    std::cout << "\n";
    std::cout << "===== EVOMIRROR COMPILED STATE =====\n";

    std::cout << "{\n";
    std::cout << "  \"schema\": \"EvoMirror-State/v3\",\n";
    std::cout << "  \"resonance\": " << state.resonance << ",\n";
    std::cout << "  \"intensity\": " << state.intensity << ",\n";
    std::cout << "  \"focus\": " << state.focus << ",\n";

    std::cout << "  \"orb\": {\n";
    std::cout << "    \"glow\": " << state.glow << ",\n";
    std::cout << "    \"density\": " << state.density << ",\n";
    std::cout << "    \"motion\": " << state.motion << ",\n";
    std::cout << "    \"complexity\": " << state.complexity << ",\n";
    std::cout << "    \"coreIntensity\": "
        << state.coreIntensity << ",\n";

    std::cout << "    \"primaryColor\": \""
        << state.primaryColor << "\",\n";

    std::cout << "    \"secondaryColor\": \""
        << state.secondaryColor << "\",\n";

    std::cout << "    \"coreColor\": \""
        << state.coreColor << "\"\n";

    std::cout << "  }\n";
    std::cout << "}\n";



    return 0;
}