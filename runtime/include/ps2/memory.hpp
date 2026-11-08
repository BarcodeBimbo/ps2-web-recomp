#pragma once

#include "cpu.hpp"

#include <cstdint>
#include <cstring>

namespace ps2 {

inline constexpr std::uint32_t kRamSize = 32u << 20;
inline constexpr std::uint32_t kScratchpadBase = 0x70000000u;
inline constexpr std::uint32_t kScratchpadSize = 16u << 10;

extern std::uint8_t g_ram[];
extern std::uint8_t g_spr[];

extern bool g_watch_on;
extern std::uint32_t g_watch_base, g_watch_end;
void watch_hit(std::uint32_t a, std::uint32_t v, const char *via);
void watch_span(std::uint32_t a, std::uint32_t n, const char *via);
void init_watch();

// CNK/Alchemy quarantine: while armed, guest SW of 0 to this EE address is
// dropped so vt+108 (0x5032E0) still sees *(obj+0x20) for 0x51C100 ingest.
// Armed only from igfileio butanim soft-arm — Hitman/NFS disc path never sets it.
extern std::uint32_t g_alchemy_o20_guard_addr;
extern std::uint32_t g_alchemy_o20_guard_value;
extern std::uint32_t g_alchemy_o14_guard_value;
extern int g_alchemy_o20_guard_blocks;
void alchemy_o20_guard_log(std::uint32_t a);
void alchemy_o20_guard_arm(std::uint32_t obj_plus_20, std::uint32_t o20_value, std::uint32_t o14_value = 0);
void alchemy_o20_guard_disarm();
// Just-in-time restore at vt+108 `lw a0,0x20(s0)` (PC 0x503308). Safe no-op if unarmed.
void alchemy_o20_jit_before_lw(std::uint32_t obj);

template <typename T>
inline bool watched(std::uint32_t a, std::uint32_t v) {
    if (g_watch_on && a >= g_watch_base && a < g_watch_end) [[unlikely]] watch_hit(a, v, "store");
    return false;
}

// Returns true when the store must be suppressed (caller skips the write).
inline bool alchemy_o20_guard_blocks(std::uint32_t a, std::uint32_t v) {
    if (!g_alchemy_o20_guard_addr || v != 0) [[likely]] return false;
    // Guest may use KSEG0/KSEG1 mirrors; guard is armed with low phys addr.
    const std::uint32_t phys = a & (kRamSize - 1);
    if (phys != g_alchemy_o20_guard_addr) return false;
    ++g_alchemy_o20_guard_blocks;
    if (g_alchemy_o20_guard_blocks <= 8) alchemy_o20_guard_log(phys);
    return true;
}

// True when a multi-word store would write zeros over the guarded +0x20 word.
inline bool alchemy_o20_guard_blocks_span(std::uint32_t a, std::size_t n, const std::uint8_t *bytes) {
    if (!g_alchemy_o20_guard_addr || !bytes || n < 4) [[likely]] return false;
    const std::uint32_t phys = a & (kRamSize - 1);
    const std::uint32_t g = g_alchemy_o20_guard_addr;
    if (phys + n <= g || phys >= g + 4u) return false;
    const std::size_t off = g - phys;
    std::uint32_t word = 0;
    std::memcpy(&word, bytes + off, 4);
    if (word != 0) return false;
    ++g_alchemy_o20_guard_blocks;
    if (g_alchemy_o20_guard_blocks <= 8) alchemy_o20_guard_log(g);
    return true;
}

std::uint8_t slow_ld8(std::uint32_t a);
std::uint16_t slow_ld16(std::uint32_t a);
std::uint32_t slow_ld32(std::uint32_t a);
std::uint64_t slow_ld64(std::uint32_t a);
void slow_ld128(std::uint32_t a, Reg128 &out);
void slow_st8(std::uint32_t a, std::uint8_t v);
void slow_st16(std::uint32_t a, std::uint16_t v);
void slow_st32(std::uint32_t a, std::uint32_t v);
void slow_st64(std::uint32_t a, std::uint64_t v);
void slow_st128(std::uint32_t a, const Reg128 &v);

template <typename T>
inline T *fast(std::uint32_t a) {
    if (a <= kRamSize - sizeof(T)) [[likely]] return reinterpret_cast<T *>(g_ram + a);
    if ((a >> 14) == (kScratchpadBase >> 14) && (a & (kScratchpadSize - 1)) <= kScratchpadSize - sizeof(T)) return reinterpret_cast<T *>(g_spr + (a & (kScratchpadSize - 1)));
    return nullptr;
}

template <typename T>
inline T load(const void *p) {
    T v;
    std::memcpy(&v, p, sizeof v);
    return v;
}

template <typename T>
inline void store(void *p, T v) { std::memcpy(p, &v, sizeof v); }

inline std::uint8_t ld8(std::uint32_t a) {
    if (auto *p = fast<std::uint8_t>(a)) return *p;
    return slow_ld8(a);
}

inline std::uint16_t ld16(std::uint32_t a) {
    if (auto *p = fast<std::uint16_t>(a)) return load<std::uint16_t>(p);
    return slow_ld16(a);
}

inline std::uint32_t ld32(std::uint32_t a) {
    if (auto *p = fast<std::uint32_t>(a)) return load<std::uint32_t>(p);
    return slow_ld32(a);
}

inline std::uint64_t ld64(std::uint32_t a) {
    if (auto *p = fast<std::uint64_t>(a)) return load<std::uint64_t>(p);
    return slow_ld64(a);
}

inline void ld128(std::uint32_t a, Reg128 &out) {
    if (auto *p = fast<Reg128>(a)) { std::memcpy(&out, p, 16); return; }
    slow_ld128(a, out);
}

inline void st8(std::uint32_t a, std::uint8_t v) {
    watched<std::uint8_t>(a, v);
    if (auto *p = fast<std::uint8_t>(a)) { *p = v; return; }
    slow_st8(a, v);
}

inline void st16(std::uint32_t a, std::uint16_t v) {
    watched<std::uint16_t>(a, v);
    if (auto *p = fast<std::uint16_t>(a)) { store(p, v); return; }
    slow_st16(a, v);
}

inline void st32(std::uint32_t a, std::uint32_t v) {
    if (alchemy_o20_guard_blocks(a, v)) [[unlikely]] return;
    watched<std::uint32_t>(a, v);
    if (auto *p = fast<std::uint32_t>(a)) { store(p, v); return; }
    slow_st32(a, v);
}

inline void st64(std::uint32_t a, std::uint64_t v) {
    std::uint8_t raw[8];
    std::memcpy(raw, &v, 8);
    if (alchemy_o20_guard_blocks_span(a, 8, raw)) [[unlikely]] return;
    watched<std::uint32_t>(a, static_cast<std::uint32_t>(v));
    if (auto *p = fast<std::uint64_t>(a)) { store(p, v); return; }
    slow_st64(a, v);
}

inline void st128(std::uint32_t a, const Reg128 &v) {
    std::uint8_t raw[16];
    std::memcpy(raw, &v, 16);
    if (alchemy_o20_guard_blocks_span(a, 16, raw)) [[unlikely]] return;
    watched<std::uint32_t>(a, v.w[0]);
    if (auto *p = fast<Reg128>(a)) { std::memcpy(p, &v, 16); return; }
    slow_st128(a, v);
}

inline std::uint64_t mask_below(std::uint32_t bits) { return bits >= 64 ? ~0ull : (1ull << bits) - 1; }

inline void lwl(Reg128 &rt, std::uint32_t a) {
    const std::uint32_t shift = (3u - (a & 3u)) * 8u;
    const std::uint32_t mem = ld32(a & ~3u);
    const std::uint32_t v = (mem << shift) | (rt.w[0] & static_cast<std::uint32_t>(mask_below(shift)));
    rt.sd[0] = static_cast<std::int32_t>(v);
}

inline void lwr(Reg128 &rt, std::uint32_t a) {
    const std::uint32_t shift = (a & 3u) * 8u;
    const std::uint32_t mem = ld32(a & ~3u);
    const std::uint32_t v = (mem >> shift) | (rt.w[0] & ~static_cast<std::uint32_t>(mask_below(32 - shift)));
    if (shift == 0) rt.sd[0] = static_cast<std::int32_t>(v);
    else rt.w[0] = v;
}

inline void ldl(Reg128 &rt, std::uint32_t a) {
    const std::uint32_t shift = (7u - (a & 7u)) * 8u;
    const std::uint64_t mem = ld64(a & ~7u);
    rt.d[0] = (mem << shift) | (rt.d[0] & mask_below(shift));
}

inline void ldr(Reg128 &rt, std::uint32_t a) {
    const std::uint32_t shift = (a & 7u) * 8u;
    const std::uint64_t mem = ld64(a & ~7u);
    rt.d[0] = (mem >> shift) | (rt.d[0] & ~mask_below(64 - shift));
}

inline void swl(const Reg128 &rt, std::uint32_t a) {
    const std::uint32_t shift = (3u - (a & 3u)) * 8u;
    const std::uint32_t mem = ld32(a & ~3u);
    st32(a & ~3u, (rt.w[0] >> shift) | (mem & ~static_cast<std::uint32_t>(mask_below(32 - shift))));
}

inline void swr(const Reg128 &rt, std::uint32_t a) {
    const std::uint32_t shift = (a & 3u) * 8u;
    const std::uint32_t mem = ld32(a & ~3u);
    st32(a & ~3u, (rt.w[0] << shift) | (mem & static_cast<std::uint32_t>(mask_below(shift))));
}

inline void sdl(const Reg128 &rt, std::uint32_t a) {
    const std::uint32_t shift = (7u - (a & 7u)) * 8u;
    const std::uint64_t mem = ld64(a & ~7u);
    st64(a & ~7u, (rt.d[0] >> shift) | (mem & ~mask_below(64 - shift)));
}

inline void sdr(const Reg128 &rt, std::uint32_t a) {
    const std::uint32_t shift = (a & 7u) * 8u;
    const std::uint64_t mem = ld64(a & ~7u);
    st64(a & ~7u, (rt.d[0] << shift) | (mem & mask_below(shift)));
}

}
