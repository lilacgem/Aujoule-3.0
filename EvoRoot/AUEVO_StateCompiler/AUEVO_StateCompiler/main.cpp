#include <iostream>
#include <fstream>
#include <string>
#include "state_compiler.h"

int main()
{
    std::cout << "=====================================\n";
    std::cout << "     AUEVO STATE COMPILER\n";
    std::cout << "=====================================\n\n";

    EvoInput input{};

    std::ifstream compiler2State(
        R"("C:\Users\1lisajevolving\EvoRoot\AU\Debug\compiler2_state.txt")");

    if (compiler2State.is_open()) {
        int compiler2Version;
        int compiler2Intensity;
        float compiler2Focus;
        char compiler2Initial;
        std::string compiler2Pattern;
        std::string compiler2Color;
        std::string compiler2Resonance;

        compiler2State >> compiler2Version;
        compiler2State >> compiler2Intensity;
        compiler2State >> compiler2Focus;
        compiler2State >> compiler2Initial;

        compiler2State.ignore();

        std::getline(compiler2State, compiler2Pattern);
        std::getline(compiler2State, compiler2Color);
        std::getline(compiler2State, compiler2Resonance);

        input.intensity = compiler2Intensity;
        input.focus = compiler2Focus;

        compiler2State.close();

        std::cout << "Loaded Compiler 2 State v"
            << compiler2Version << "\n";
    }

    std::cout << "Activity (0.0-1.0): ";
    std::cin >> input.activity;

    std::cout << "Complexity (0.0-1.0): ";
    std::cin >> input.complexity;

    OrbState state = compileState(input);

    std::ofstream jsonFile("evo_state.json");

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

        std::cout << "\nState saved to evo_state.json\n";
    }
    else
    {
        std::cout << "\nERROR: Could not create evo_state.json\n";
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

    std::cout << "\nPress Enter to exit.";

    std::cin.ignore();
    std::cin.get();

    return 0;
}