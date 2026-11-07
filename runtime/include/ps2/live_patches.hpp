#pragma once
#include <array>
#include <atomic>
#include <cstdint>

namespace ps2 {
// One browser producer and one emulation consumer. Only the emulation thread
// writes guest RAM; publishing a command never edits a vector on another thread.
class LivePatches {
    struct Patch { std::uint32_t address{}, bytes{}; std::uint64_t value{}; bool enabled{}; };
    struct Slot { std::atomic<unsigned> state{0}; Patch pending{}, active{}; };
    std::array<Slot, 128> slots_{};
public:
    bool publish(unsigned slot, std::uint32_t address, unsigned bytes, std::uint64_t value, bool enabled) {
        if (slot >= slots_.size()) return false;
        if (enabled && ((bytes != 1 && bytes != 2 && bytes != 4 && bytes != 8) ||
                        address > 0x02000000u - bytes || address % bytes)) return false;
        auto &s = slots_[slot];
        unsigned ready = 0;
        if (!s.state.compare_exchange_strong(ready, 2, std::memory_order_acquire)) return false;
        s.pending = {address, bytes, value, enabled};
        s.state.store(1, std::memory_order_release);
        return true;
    }
    template<class Write> void apply(Write write) {
        for (auto &s : slots_) {
            if (s.state.load(std::memory_order_acquire) == 1) {
                s.active = s.pending;
                s.state.store(0, std::memory_order_release);
            }
            if (s.active.enabled) write(s.active.address, s.active.bytes, s.active.value);
        }
    }
};
}
