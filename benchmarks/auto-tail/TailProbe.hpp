#pragma once

#include "AutoReservationWithTail.hpp"
#include <tuple>

namespace TailProbe {
inline constexpr size_t maxSuffixBytes = 256 * 1024;
inline thread_local bool counting = false;

enum class Status { NotRun, Fits, TokenLimit, Invalid };
struct InvalidInput {};

template<class Diagnostic>
[[noreturn]] void reject(Diagnostic makeDiagnostic)
{
    if (counting)
        throw InvalidInput{};
    throw makeDiagnostic();
}

class CursorCheckpoint {
    using Cursor = std::tuple<size_t&, size_t&, size_t&, size_t&, size_t&, size_t&>;
    Cursor fields;
    std::tuple<size_t, size_t, size_t, size_t, size_t, size_t> saved;
    bool wasCounting = counting;
public:
    explicit CursorCheckpoint(Cursor cursor) : fields(cursor), saved(cursor)
    {
        counting = true;
    }
    CursorCheckpoint(const CursorCheckpoint&) = delete;
    CursorCheckpoint& operator=(const CursorCheckpoint&) = delete;
    ~CursorCheckpoint()
    {
        fields = saved;
        counting = wasCounting;
    }
};

struct Count {
    Status status = Status::NotRun;
    size_t scannedBytes = 0;
    size_t tokens = 0;
};

#ifdef MASKETJSON_AUTO_V3_TRACE
struct Observation {
    size_t position = 0;
    size_t originalRequest = 0;
    size_t ordinaryFloor = 0;
    Count count;
};
inline thread_local Observation observation;
inline const char* name(Status status)
{
    switch (status) {
    case Status::Fits: return "fits";
    case Status::TokenLimit: return "token_limit";
    case Status::Invalid: return "invalid";
    default: return "not_run";
    }
}
#endif

template<class CountSuffix>
void adjust(AutoReserveTail::Hint& hint, size_t capacity, size_t limit,
            size_t position, size_t remaining, CountSuffix countSuffix)
{
    if (!hint.floorRaised || !hint.tailApplied
            || remaining == 0 || remaining > maxSuffixBytes)
        return;

    const size_t ordinary = AutoReserve::bounds(
        AutoReserve::Goal::Speed, capacity, limit, false).lower;
    const size_t pending = capacity + 1;
    if (ordinary <= pending || ordinary >= hint.request)
        return;

    const auto result = countSuffix(ordinary - pending);
#ifdef MASKETJSON_AUTO_V3_TRACE
    observation = {position, hint.request, ordinary, result};
#else
    (void)position;
#endif
    if (result.status == Status::Fits) {
        // The count includes EOF. Every remaining token fits in this allocation.
        hint.request = ordinary;
        hint.tailBound = ordinary;
        hint.floorOverride = ordinary > hint.byteUpper;
    }
}
}
