find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(generated "${CMAKE_CURRENT_BINARY_DIR}/generated")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/generate.py"
    "${PROJECT_SOURCE_DIR}/parser/JsonLexer.cpp"
    "${PROJECT_SOURCE_DIR}/benchmarks/auto/generate_lexer.py"
    "${PROJECT_SOURCE_DIR}/benchmarks/auto-v3/generate_lexer.py"
    "${PROJECT_SOURCE_DIR}/benchmarks/auto-v3/AutoReservationV3.hpp"
    "${PROJECT_SOURCE_DIR}/benchmarks/auto-v3/Trace.cpp")
execute_process(COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate.py"
    "${PROJECT_SOURCE_DIR}/parser/JsonLexer.cpp" "${generated}" COMMAND_ERROR_IS_FATAL ANY)

set(programs AutoTailTime AutoTailInspect AutoTailTrace AutoTailVerify)
foreach(mode time trace profile)
    if(mode STREQUAL "profile" AND NOT TARGET ParserProfile)
        continue()
    endif()
    set(library AutoTail-${mode})
    add_library(${library} STATIC "${generated}/tail.cpp" $<TARGET_OBJECTS:AutoParser>)
    target_link_libraries(${library} PUBLIC MasketJSON)
    target_include_directories(${library} PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}" "${generated}"
        "${PROJECT_SOURCE_DIR}/benchmarks/auto" "${PROJECT_SOURCE_DIR}/benchmarks/reservation")
    target_compile_definitions(${library} PUBLIC JsonLexer=AutoLexer JsonParser=AutoParser
        AUTO_V3_SPEED_BYTES=${AUTO_V3_SPEED_BUDGET}
        AUTO_V3_SPEED_QUARTERS=${AUTO_V3_SPEED_QUARTERS}
        AUTO_V3_SPEED_LOOKAHEAD=${AUTO_V3_SPEED_LOOKAHEAD})
    if(mode STREQUAL "time")
        add_executable(AutoTailTime ../reservation/Timing.cpp ../BenchmarkUtils.cpp)
        target_compile_definitions(AutoTailTime PRIVATE MATRIX_CONFIGURATION="$<CONFIG>")
        target_link_libraries(AutoTailTime PRIVATE ${library})
        add_executable(AutoTailInspect ../reservation/Inspect.cpp)
        target_link_libraries(AutoTailInspect PRIVATE ${library})
        add_executable(AutoTailVerify Verify.cpp ../auto/Compare.cpp $<TARGET_OBJECTS:AutoBaseline>)
        target_include_directories(AutoTailVerify PRIVATE "${PROJECT_SOURCE_DIR}/fuzz")
        target_link_libraries(AutoTailVerify PRIVATE ${library})
    elseif(mode STREQUAL "trace")
        target_compile_definitions(${library} PUBLIC MASKETJSON_AUTO_V3_TRACE)
        add_executable(AutoTailTrace "${generated}/trace.cpp")
        target_link_libraries(AutoTailTrace PRIVATE ${library})
    else()
        target_compile_definitions(${library} PUBLIC MASKETJSON_RESERVATION_STATS)
        add_executable(AutoTailProfile ../ParserProfile.cpp ../MemoryTracker.cpp)
        target_link_libraries(AutoTailProfile PRIVATE ${library} Threads::Threads)
        list(APPEND programs AutoTailProfile AutoProfile-balanced AutoProfile-low-memory)
    endif()
endforeach()
add_custom_target(AutoTailTools DEPENDS ${programs} AutoV3Tools)
