#include "hw.hpp"
#include "vu_micro.hpp"
#include "ps2/memory.hpp"
#include "ps2/system.hpp"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>

namespace ps2 {

alignas(64) std::uint8_t g_ram[kRamSize + 64];
alignas(64) std::uint8_t g_spr[kScratchpadSize];
alignas(64) std::uint8_t g_vu0_code[4096];
alignas(64) std::uint8_t g_vu0_mem[4096];
alignas(64) std::uint8_t g_vu1_code[16384];
alignas(64) std::uint8_t g_vu1_mem[16384];

namespace {

enum class Region { Ram, Scratchpad, Io, Vu, Rom, None };

}

// A watchpoint for porting work: PS2_WATCH=base,len makes every write into
// that range of main memory print itself, guest store or bulk copy, with the
// cpu state at the time.
bool g_watch_on = false;
std::uint32_t g_watch_base = 0, g_watch_end = 0;

// CNK/Alchemy butanim obj+0x20 clear suppress (see memory.hpp).
std::uint32_t g_alchemy_o20_guard_addr = 0;
std::uint32_t g_alchemy_o20_guard_value = 0;
std::uint32_t g_alchemy_o14_guard_value = 0;
int g_alchemy_o20_guard_blocks = 0;

void alchemy_o20_guard_log(std::uint32_t a) {
    std::fprintf(stderr,
                 "[alchemy-o20] blocked clear of 0x%08X (kept live for vt+108) pc=0x%08X ra=0x%08X blocks=%d\n",
                 a, g_cpu.pc, g_cpu.r[31].w[0], g_alchemy_o20_guard_blocks);
}

void alchemy_o20_guard_arm(std::uint32_t obj_plus_20, std::uint32_t o20_value, std::uint32_t o14_value) {
    if (!obj_plus_20 || obj_plus_20 + 4u > kRamSize || !o20_value) {
        g_alchemy_o20_guard_addr = 0;
        g_alchemy_o20_guard_value = 0;
        g_alchemy_o14_guard_value = 0;
        return;
    }
    g_alchemy_o20_guard_addr = obj_plus_20;
    g_alchemy_o20_guard_value = o20_value;
    g_alchemy_o14_guard_value = o14_value;
    g_alchemy_o20_guard_blocks = 0;
    std::fprintf(stderr,
                 "[alchemy-o20] guard armed at 0x%08X value=0x%08X o14=0x%08X (suppress SW zero until disarm)\n",
                 obj_plus_20, o20_value, o14_value);
}

void alchemy_o20_guard_disarm() {
    if (g_alchemy_o20_guard_addr) {
        std::fprintf(stderr, "[alchemy-o20] guard disarmed (was 0x%08X, blocks=%d)\n",
                     g_alchemy_o20_guard_addr, g_alchemy_o20_guard_blocks);
    }
    g_alchemy_o20_guard_addr = 0;
    g_alchemy_o20_guard_value = 0;
    g_alchemy_o14_guard_value = 0;
}

void alchemy_o20_jit_before_lw(std::uint32_t obj) {
    if (!g_alchemy_o20_guard_addr || !g_alchemy_o20_guard_value || !obj) return;
    if (obj + 0x24u > kRamSize) return;
    if ((obj + 0x20u) != g_alchemy_o20_guard_addr) return;
    std::uint32_t cur = 0;
    std::memcpy(&cur, g_ram + obj + 0x20u, 4);
    if (cur != 0) return;
    std::memcpy(g_ram + obj + 0x20u, &g_alchemy_o20_guard_value, 4);
    if (g_alchemy_o14_guard_value && g_alchemy_o14_guard_value < kRamSize) {
        std::memcpy(g_ram + obj + 0x14u, &g_alchemy_o14_guard_value, 4);
    }
    static int s_jit = 0;
    if (s_jit < 8) {
        std::fprintf(stderr,
                     "[alchemy-o20] jit-restore at 0x503308 obj=0x%X +20=0x%X (was 0)\n",
                     obj, g_alchemy_o20_guard_value);
        ++s_jit;
    }
}

void init_watch() {
    if (const char *spec = std::getenv("PS2_WATCH")) {
        std::uint32_t base = 0, len = 0;
        if (std::sscanf(spec, "%x,%x", &base, &len) == 2 && len) {
            g_watch_base = base & (kRamSize - 1);
            g_watch_end = g_watch_base + len;
            g_watch_on = true;
            std::fprintf(stderr, "[watch] writes to 0x%08X..0x%08X will print\n", g_watch_base, g_watch_end);
        }
    }
}

void watch_hit(std::uint32_t a, std::uint32_t v, const char *via) {
    const std::uint8_t *at = (a < kRamSize) ? g_ram + a : ((a >> 14) == (kScratchpadBase >> 14) ? g_spr + (a & (kScratchpadSize - 1)) : nullptr);
    std::uint32_t was = 0;
    if (at) {
        const auto remaining = a < kRamSize ? kRamSize - a : kScratchpadSize - (a & (kScratchpadSize - 1));
        std::memcpy(&was, at, std::min<std::size_t>(4, remaining));
    }
    std::fprintf(stderr, "[watch] write %08X = %08X (was %08X) via %s, pc 0x%08X ra 0x%08X\n", a, v, was, via, g_cpu.pc, g_cpu.r[31].w[0]);
}

void watch_span(std::uint32_t a, std::uint32_t n, const char *via) {
    if (!g_watch_on) return;
    const std::uint32_t s = a & (kRamSize - 1), e = s + std::min(n, kRamSize - s);
    if (e <= g_watch_base || s >= g_watch_end) return;
    for (std::uint32_t k = s & ~3u; k < e; k += 4) {
        if (k < g_watch_base || k + 4 > g_watch_end) continue;
        std::uint32_t v;
        std::memcpy(&v, g_ram + k, 4);
        std::fprintf(stderr, "[watch] span from %08X: word %08X = %08X via %s, pc 0x%08X\n", a, k, v, via, g_cpu.pc);
    }
}

namespace {

struct Target {
    Region region;
    std::uint8_t *host;
    std::uint32_t address;
};

std::uint8_t *vu_memory(std::uint32_t p) {
    switch ((p >> 12) & 0xFu) {
    case 0x0: return g_vu0_code + (p & 0xFFFu);
    case 0x4: return g_vu0_mem + (p & 0xFFFu);
    case 0x8: case 0x9: case 0xA: case 0xB: return g_vu1_code + (p & 0x3FFFu);
    case 0xC: case 0xD: case 0xE: case 0xF: return g_vu1_mem + (p & 0x3FFFu);
    default: return nullptr;
    }
}

Target resolve(std::uint32_t a) {
    if ((a >> 14) == (kScratchpadBase >> 14)) return {Region::Scratchpad, g_spr + (a & (kScratchpadSize - 1)), a};
    const std::uint32_t p = physical(a);
    if (p < 0x10000000u) return {Region::Ram, g_ram + (p & (kRamSize - 1)), p};
    if (p >= 0x11000000u && p < 0x11010000u) {
        if (std::uint8_t *host = vu_memory(p)) return {Region::Vu, host, p};
    }
    if (p >= 0x10000000u && p < 0x13000000u) return {Region::Io, nullptr, p};
    if (p >= 0x1FC00000u && p < 0x20000000u) return {Region::Rom, nullptr, p};
    return {Region::None, nullptr, p};
}

void check_span(const Target &target, std::size_t bytes) {
    std::size_t remaining = 0;
    if (target.region == Region::Ram) remaining = kRamSize - (target.address & (kRamSize - 1));
    else if (target.region == Region::Scratchpad) remaining = kScratchpadSize - (target.address & (kScratchpadSize - 1));
    else if (target.region == Region::Vu) {
        const auto size = (target.address & 0x8000u) ? 16384u : 4096u;
        remaining = size - (target.address & (size - 1));
    }
    if (target.host && bytes > remaining) throw std::out_of_range("Guest memory access crosses a mapped region");
}

void unmapped(const char *what, std::uint32_t a) {
    std::fprintf(stderr, "[mem] %s at unmapped 0x%08X (pc 0x%08X)\n", what, a, g_cpu.pc);
}

template <typename T>
T read_slow(std::uint32_t a) {
    const Target t = resolve(a);
    if (t.host) {
        check_span(t, sizeof(T));
        T v;
        std::memcpy(&v, t.host, sizeof v);
        return v;
    }
    if (t.region == Region::Io) {
        if constexpr (sizeof(T) == 8) return hw::read64(t.address);
        else {
            const std::uint32_t word = hw::read32(t.address & ~3u);
            return static_cast<T>(word >> ((t.address & 3u) * 8u));
        }
    }
    if (t.region != Region::Rom) unmapped("read", a);
    return 0;
}

template <typename T>
void write_slow(std::uint32_t a, T v) {
    const Target t = resolve(a);
    if (t.host) {
        check_span(t, sizeof(T));
        if constexpr (sizeof(T) == 4) {
            if (t.region == Region::Ram &&
                alchemy_o20_guard_blocks(t.address & (kRamSize - 1), static_cast<std::uint32_t>(v))) {
                return;
            }
        }
        if (g_watch_on && t.region == Region::Ram) {
            const std::uint32_t base = t.address & (kRamSize - 1);
            if (base >= g_watch_base && base < g_watch_end) watch_hit(base, static_cast<std::uint32_t>(v), "store-slow");
        }
        std::memcpy(t.host, &v, sizeof v);
        if (t.region == Region::Vu && (t.address & 0x4000u) == 0) vu::code_changed((t.address >> 15) & 1u);
        return;
    }
    if (t.region == Region::Io) {
        if constexpr (sizeof(T) == 8) hw::write64(t.address, v);
        else hw::write32(t.address, static_cast<std::uint32_t>(v));
        return;
    }
    unmapped("write", a);
}

}

std::uint32_t physical(std::uint32_t a) {
    if (a >= 0x80000000u && a < 0xC0000000u) return a & 0x1FFFFFFFu;
    const std::uint32_t top = a >> 28;
    if (top == 2u || top == 3u) return a & 0x0FFFFFFFu;
    return a;
}

std::uint8_t slow_ld8(std::uint32_t a) { return read_slow<std::uint8_t>(a); }
std::uint16_t slow_ld16(std::uint32_t a) { return read_slow<std::uint16_t>(a); }
std::uint32_t slow_ld32(std::uint32_t a) { return read_slow<std::uint32_t>(a); }
std::uint64_t slow_ld64(std::uint32_t a) { return read_slow<std::uint64_t>(a); }

void slow_ld128(std::uint32_t a, Reg128 &out) {
    const Target t = resolve(a);
    if (t.host) { check_span(t, 16); std::memcpy(&out, t.host, 16); }
    else if (t.region == Region::Io) hw::read128(t.address, out);
    else std::memset(&out, 0, 16);
}

void slow_st8(std::uint32_t a, std::uint8_t v) { write_slow(a, v); }
void slow_st16(std::uint32_t a, std::uint16_t v) { write_slow(a, v); }
void slow_st32(std::uint32_t a, std::uint32_t v) { write_slow(a, v); }
void slow_st64(std::uint32_t a, std::uint64_t v) { write_slow(a, v); }

void slow_st128(std::uint32_t a, const Reg128 &v) {
    const Target t = resolve(a);
    if (t.host) { check_span(t, 16); std::memcpy(t.host, &v, 16); }
    else if (t.region == Region::Io) hw::write128(t.address, v);
    else unmapped("write128", a);
}

}
