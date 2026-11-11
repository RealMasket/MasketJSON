"""Build the private lexer from the v3 controller and the production token loop."""

import re
import subprocess
import sys
from pathlib import Path

source, destination = map(Path, sys.argv[1:])
v3 = Path(__file__).resolve().parents[1] / "auto-v3"


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Tail experiment source anchor changed: {old}")
    return text.replace(old, new, 1)


subprocess.run(
    [sys.executable, str(v3 / "generate_lexer.py"), str(source), str(destination)],
    check=True,
)
controller = (v3 / "AutoReservationV3.hpp").read_text(encoding="utf-8-sig")
controller = replace_once(controller, "void grow(bool eof) {",
    "template<class AdjustHint>\n    void grow(bool eof, AdjustHint adjustHint) {")
controller = replace_once(controller, "const auto hint=choose", "auto hint=choose")
controller = replace_once(controller, "        const Kind kind=hint.tailApplied",
    "        adjustHint(hint,capacity,limit);\n        const Kind kind=hint.tailApplied")
(destination / "AutoReservationWithTail.hpp").write_bytes(
    controller.replace("AutoReserveV3", "AutoReserveTail").encode()
)

lexer = (destination / "speed.cpp").read_text(encoding="utf-8-sig")
lexer = replace_once(lexer, '#include "AutoReservationV3.hpp"', '#include "TailProbe.hpp"')
lexer = lexer.replace("AutoReserveV3", "AutoReserveTail")
# Delay creation of the error message until the main scan needs it.
lexer, errors = re.subn(
    r"throw (LexerException\(.*?\));",
    r"TailProbe::reject([&] { return \1; });",
    lexer, flags=re.S,
)
if errors == 0 or "throw LexerException(" in lexer:
    raise ValueError("Lexer error path was not converted to lazy formatting")

loop_start = lexer.index("    while (!isAtEnd())", lexer.index("    auto append"))
loop_end = lexer.index("    tokenPosition = position;\n    tokenLine = line;", loop_start)
loop = lexer[loop_start:loop_end]
count_loop, tokens = re.subn(
    r"append\((.*?)\);",
    r"(void)(\1);" "\n            if (++count == slots)\n"
    "                return TailProbe::Count{TailProbe::Status::TokenLimit, position - start, count};",
    loop, flags=re.S,
)
if tokens != 9:
    raise ValueError("Production token loop changed")

probe = """    auto countSuffix = [&](size_t slots) -> TailProbe::Count {
        const size_t start = position;
        const TailProbe::CursorCheckpoint restore(
            std::tie(position, line, column, tokenPosition, tokenLine, tokenColumn));
        size_t count = 0;
        try {
""" + "".join("        " + line if line.strip() else line
              for line in count_loop.splitlines(keepends=True)) + """            return {TailProbe::Status::Fits, position - start, count + 1};
        } catch (const TailProbe::InvalidInput&) {
            return {TailProbe::Status::Invalid, position - start, count};
        }
    };
"""
lexer = replace_once(lexer, "    auto append = [&](Token token) {",
    probe + "    auto append = [&](Token token) {")
lexer = replace_once(lexer, "controller.grow(token.type==Parser::TokenType::EndOfFile);",
    """controller.grow(token.type == Parser::TokenType::EndOfFile,
                [&](auto& hint, size_t capacity, size_t limit) {
                    TailProbe::adjust(hint, capacity, limit, position, source.size() - position, countSuffix);
                });""")
(destination / "tail.cpp").write_bytes(lexer.encode())

trace = (v3 / "Trace.cpp").read_text(encoding="utf-8-sig")
trace = trace.replace('#include "AutoReservationV3.hpp"', '#include "TailProbe.hpp"')
trace = trace.replace("AutoReserveV3", "AutoReserveTail")
trace = replace_once(trace, "status,error_fingerprint", "status,error_fingerprint,"
    "probe_status,probe_bytes,probe_tokens,probe_original_request,probe_ordinary_floor")
trace = replace_once(trace, "AutoReserveTail::Journal journal;",
    "TailProbe::observation = {};\n                AutoReserveTail::Journal journal;")
trace = replace_once(trace, "                    std::cout<<MatrixData::csv",
    """                    const auto probe = growth && TailProbe::observation.position == d.position
                        ? TailProbe::observation : TailProbe::Observation{};
                    std::cout<<MatrixData::csv""")
trace = replace_once(trace, "<<error.hex()<<'\\n';",
    """<<error.hex()<<','<<TailProbe::name(probe.count.status)<<','<<probe.count.scannedBytes<<','
                        <<probe.count.tokens<<','<<probe.originalRequest<<','<<probe.ordinaryFloor<<'\\n';""")
trace = replace_once(trace, "<<AutoReserveTail::name(d.kind,d.state)",
    '<<(probe.count.status == TailProbe::Status::Fits ? "confirmed_suffix" : AutoReserveTail::name(d.kind,d.state))')
(destination / "trace.cpp").write_bytes(trace.encode())
