#include "Compare.hpp"
#include "../reservation/Data.hpp"

#include <iostream>
#include <string_view>

int main(int argc, char** argv)
{
    try {
        if (argc < 2)
            throw std::invalid_argument("Usage: AutoTailVerify [--invalid] INPUT...");
        const bool invalid = std::string_view(argv[1]) == "--invalid";
        const int first = invalid ? 2 : 1;
        if (argc == first)
            throw std::invalid_argument("Expected at least one input");
        AutoCheck::selfTest();
        for (int i = first; i < argc; ++i) {
            if (AutoCheck::compare(MatrixData::read(argv[i])) == invalid)
                throw std::runtime_error("Fixture acceptance differs from the expected outcome");
        }
        std::cout << "Tail probe matches production tokens, values and diagnostics\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
