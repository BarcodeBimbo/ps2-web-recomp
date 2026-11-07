#include "ps2/generated.hpp"
#include "ps2/memory.hpp"
#include "ps2/system.hpp"

#include <cstdlib>
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <set>
#include <string>
#include <vector>

namespace ps2 {

namespace {

std::vector<UnitInfo> g_units;
std::vector<const UnitInfo *> g_index;
std::uint32_t g_origin = 0;
std::uint32_t g_unit_size = 1;
std::set<std::uint32_t> g_misses;
std::set<std::string> g_module_misses;

constexpr std::uint32_t kModuleMagic = 0x32524E53u;
constexpr std::uint32_t kXffMagic = 0x32666678u;

struct Instance {
    std::uint32_t base;
    const ModuleInfo *module;
};

const ModuleInfo *g_modules = nullptr;
std::uint32_t g_module_count = 0;
std::uint32_t g_module_span = 0;
std::vector<Instance> g_instances;

bool loaded_at(const ModuleInfo &m, std::uint32_t base) {
    if (m.fixed_base) {
        if (base != m.fixed_base) return false;
    } else if (ld32(base + (ld32(base) == kXffMagic ? 0x14u : 0x2Cu)) != m.size) {
        return false;
    }
    for (std::uint32_t k = 0; k < m.check_count; ++k)
        if (ld32(base + m.checks[2 * k]) != m.checks[2 * k + 1]) return false;
    return true;
}

// The word a call checks turns with each call, so every translated code word
// is proven again within check_count calls: one word per call keeps calls
// cheap while even a one word change of the image is caught in time.
std::uint32_t g_spot_cursor = 0;

const Instance *in_place(const Instance &i) {
    static const bool full = std::getenv("PS2_WINDOW_FULL") != nullptr;
    if (full || !i.module->fixed_base) return loaded_at(*i.module, i.base) ? &i : nullptr;
    if (!i.module->check_count) return &i;
    const std::uint32_t c = g_spot_cursor++ % i.module->check_count;
    return ld32(i.base + i.module->checks[2 * c]) == i.module->checks[2 * c + 1] ? &i : nullptr;
}

Instance make_instance(std::uint32_t base, const ModuleInfo *m) {
    return {base, m};
}

const Instance *instance_for(std::uint32_t pc) {
    for (std::size_t k = 0; k < g_instances.size(); ++k) {
        const Instance &i = g_instances[k];
        if (pc - i.base >= i.module->size) continue;
        if (in_place(i)) return &i;
        g_instances.erase(g_instances.begin() + static_cast<std::ptrdiff_t>(k));
        break;
    }
    if (!g_module_count || pc >= kRamSize) return nullptr;
    // A code window rewritten by the game holds fixed base modules, each an
    // image of one content. The one whose check words are in place serves it.
    for (std::uint32_t k = 0; k < g_module_count; ++k) {
        const ModuleInfo &m = g_modules[k];
        if (m.fixed_base && pc - m.fixed_base < m.size && loaded_at(m, m.fixed_base)) {
            g_instances.push_back(make_instance(m.fixed_base, &m));
            return &g_instances.back();
        }
    }
    for (std::uint32_t at = pc & ~15u; pc - at < g_module_span; at -= 16) {
        if (ld32(at) == kModuleMagic || ld32(at) == kXffMagic) {
            for (std::uint32_t k = 0; k < g_module_count; ++k)
                if (pc - at < g_modules[k].size && loaded_at(g_modules[k], at)) {
                    g_instances.push_back(make_instance(at, &g_modules[k]));
                    return &g_instances.back();
                }
            return nullptr;
        }
        if (at < 16) break;
    }
    return nullptr;
}

const UnitInfo *module_unit(const ModuleInfo &m, std::uint32_t offset) {
    for (std::uint32_t k = 0; k < m.count; ++k)
        if (offset - m.units[k].base < m.units[k].size) return &m.units[k];
    return nullptr;
}

const UnitInfo *unit_for(std::uint32_t pc) {
    const std::uint32_t slot = (pc - g_origin) / g_unit_size;
    if (pc < g_origin || slot >= g_index.size()) return nullptr;
    const UnitInfo *unit = g_index[slot];
    return unit && pc >= unit->base && pc - unit->base < unit->size ? unit : nullptr;
}

void record_miss(std::uint32_t pc) {
    if (const Instance *m = instance_for(pc)) {
        char token[96];
        std::snprintf(token, sizeof token, "%s:%x", m->module->name, pc - m->base);
        if (!g_module_misses.insert(token).second || g_options.misses_path.empty()) return;
        std::ofstream(g_options.misses_path, std::ios::app) << token << "\n";
        return;
    }
    if (!g_misses.insert(pc).second || g_options.misses_path.empty()) return;
    std::ofstream out(g_options.misses_path, std::ios::app);
    out << std::hex << pc << "\n";
}

}

void register_units(const UnitInfo *units, std::uint32_t count) {
    g_index.clear();
    g_origin = 0;
    g_unit_size = 1;
    if (!count) { g_units.clear(); return; }
    g_units.assign(units, units + count);
    if (g_units.empty()) return;
    std::sort(g_units.begin(), g_units.end(), [](const UnitInfo &a, const UnitInfo &b) { return a.base < b.base; });
    g_origin = g_units.front().base;
    g_unit_size = g_units.front().size;
    g_index.assign((g_units.back().base - g_origin) / g_unit_size + 1, nullptr);
    for (const UnitInfo &u : g_units) g_index[(u.base - g_origin) / g_unit_size] = &u;
}

void register_modules(const ModuleInfo *modules, std::uint32_t count) {
    g_module_span = 0;
    g_modules = modules;
    g_module_count = count;
    g_instances.clear();
    for (std::uint32_t k = 0; k < count; ++k) g_module_span = std::max(g_module_span, modules[k].size);
}

bool has_code(std::uint32_t pc) {
    if (pc & 3u) return false;
    const UnitInfo *u = unit_for(pc);
    if (u && u->entries[(pc - u->base) >> 2] != 0) return true;
    const Instance *m = instance_for(pc);
    const UnitInfo *mu = m ? module_unit(*m->module, pc - m->base) : nullptr;
    return mu && mu->entries[(pc - m->base - mu->base) >> 2] != 0;
}

void dispatch(Cpu &c, std::uint32_t, std::uint32_t depth) {
    const std::uint32_t pc = c.pc;
    if (pc & kUnwind) return;
    if (pc == kHandlerReturn || pc == kIdle) return;
    const UnitInfo *u = unit_for(pc);
    const std::uint16_t id = u ? u->entries[(pc - u->base) >> 2] : 0;
    if (!id) {
        if (const Instance *m = instance_for(pc)) {
            const std::uint32_t base = m->base;
            const UnitInfo *mu = module_unit(*m->module, pc - base);
            const std::uint16_t entry = mu ? mu->entries[(pc - base - mu->base) >> 2] : 0;
            if (entry) {
                c.base = base;
                mu->function(c, entry, depth);
                return;
            }
        }
        record_miss(pc);
        if (pc <= kRamSize - 16 && !(pc & 3u))
            std::fprintf(stderr, "[ee] missing instruction words: %08X %08X %08X %08X\n", ld32(pc), ld32(pc+4), ld32(pc+8), ld32(pc+12));
        char reason[64];
        std::snprintf(reason, sizeof reason, "missing code at 0x%08X (ra 0x%08X)", pc, c.r[31].w[0]);
        std::fprintf(stderr, "[ee] no translated code at 0x%08X (ra 0x%08X)\n", pc, c.r[31].w[0]);
        for (int i = 1; i < 32; i += 4)
            std::fprintf(stderr, "[ee]   r%-2d %08X %08X %08X %08X\n", i, c.r[i].w[0], c.r[i + 1].w[0], c.r[i + 2].w[0], i + 3 < 32 ? c.r[i + 3].w[0] : 0u);
        halt(reason);
        c.pc = pc | kUnwind;
        return;
    }
    u->function(c, id, depth);
}

void call(Cpu &c, std::uint32_t target, std::uint32_t depth) {
    c.pc = target;
    if (depth >= kMaxDepth) return;
    dispatch(c, 0, depth);
}

void bad_entry(Cpu &c, std::uint32_t unit_base) {
    std::fprintf(stderr, "[ee] bad entry into unit 0x%08X for pc 0x%08X\n", unit_base, c.pc);
    halt("bad entry");
    c.pc |= kUnwind;
}

void stop(Cpu &c, std::uint32_t pc, const char *what) {
    std::fprintf(stderr, "[ee] stopped at 0x%08X: %s\n", pc, what);
    halt(what);
    c.pc = pc | kUnwind;
}

void probe(Cpu &c, std::uint32_t pc) {
    // CNK vt+108 just-in-time: at 0x503308 guest does `lw a0,0x20(s0)`.
    // If Alchemy o20 guard is armed and soft-arm captured a live +0x20 but the
    // field was cleared via a non-st32 path, restore before the load.
    // Requires recomp --probes including 0x503308; store-guard covers the SW path.
    if (pc == 0x00503308u && g_alchemy_o20_guard_addr) {
        const std::uint32_t obj = c.r[16].w[0]; // s0 = obj after 0x502FC
        if (obj && obj + 0x24u <= kRamSize && (obj + 0x20u) == g_alchemy_o20_guard_addr) {
            std::uint32_t cur = 0;
            std::memcpy(&cur, g_ram + obj + 0x20u, 4);
            if (cur == 0) {
                // Pull last soft-arm capture via try_restore if linked; else log only.
                std::fprintf(stderr,
                             "[probe] 0x503308 o20=0 on obj=0x%X (guard live) — store-guard should have blocked\n",
                             obj);
            }
        }
    }
    std::fprintf(stderr, "[probe] 0x%08X a0 %08X a1 %08X a2 %08X a3 %08X ra %08X v0 %08X\n", pc, c.r[4].w[0], c.r[5].w[0], c.r[6].w[0],
                 c.r[7].w[0], c.r[31].w[0], c.r[2].w[0]);
}

void breakpoint(Cpu &c, std::uint32_t pc) {
    std::fprintf(stderr, "[ee] break at 0x%08X (ra 0x%08X)\n", pc, c.r[31].w[0]);
}

void trap(Cpu &c, std::uint32_t pc) {
    std::fprintf(stderr, "[ee] trap at 0x%08X (ra 0x%08X)\n", pc, c.r[31].w[0]);
}

}
