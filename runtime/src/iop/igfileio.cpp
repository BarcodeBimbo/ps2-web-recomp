#include "igfileio.hpp"

#include "iop.hpp"
#include "kernel.hpp"
#include "sif.hpp"

#include "ps2/disc.hpp"
#include "../hw.hpp"
#include "../kernel.hpp"
#include "ps2/memory.hpp"
#include "ps2/system.hpp"

#include <algorithm>
#include <csetjmp>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <unordered_map>
#include <vector>
#include <zlib.h>

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#endif

namespace ps2::iop::igfileio {
namespace {

using ps2::store;
using ps2::watch_span;
using ps2::g_ram;
using ps2::kRamSize;

constexpr std::uint32_t kGfcSig = 0x00008008u;
bool g_ui_igb_parse_attempted = false;
// Soft-armed BUTANIM igObject (slot+0x58 at arm time). Finalize may replace the
// slot pointer — keep this so we can detect vt+108 completion via obj+0xFF and
// restore the slot if the fail path cleared it.
std::uint32_t g_butanim_soft_obj = 0;
std::uint32_t g_butanim_plant_size = 0;
// Captured obj+0x20 at soft-arm time. vt+108 (0x5032E0) only runs the full
// 0x51C100 ingest path when *(obj+0x20)+0x24≠0. Something clears +0x20 between
// soft-arm and vt+108; restore it so the ingest path sticks and prims >> 2.
std::uint32_t g_butanim_soft_o20 = 0;
// Captured obj+0x14 at soft-arm (stream pointer) for completeness.
std::uint32_t g_butanim_soft_o14 = 0;
// Require +0xFF to rise after soft-arm; recycled heap objs may already have
// stale +0xFF=1 which previously released the intro hold before guest FCE0.
bool g_butanim_saw_ff_clear = false;
// Latch only when vt+108 ran while shared scratch still held butanim bytes
// (vt+108 sets +0xFF even when obj+0x20==0 and no real ingest happened).
bool g_butanim_parsed_ok = false;
// Track how many times we restored +20 to avoid infinite loops.
int g_butanim_o20_restore_count = 0;

struct Block {
    std::uint32_t compressed = 0;
    std::uint32_t offset = 0;
    std::uint32_t next = 0;
};

struct File {
    std::uint32_t crc = 0;
    std::uint32_t size = 0;
    std::uint32_t first = 0;
    std::string name;
};

struct Index {
    bool ready = false;
    std::uint32_t gob_sector = 0;
    std::uint32_t gob_size = 0;
    std::vector<Block> blocks;
    std::vector<File> files;
    std::unordered_map<std::uint32_t, std::size_t> by_crc;
    std::unordered_map<std::string, std::size_t> by_name;
};

Index g_index;
std::unordered_map<int, std::vector<std::uint8_t>> g_open; // fd -> bytes
std::unordered_map<int, std::uint32_t> g_pos;
int g_next_fd = 1;

std::uint32_t be32(const std::uint8_t *p) {
    return (std::uint32_t(p[0]) << 24) | (std::uint32_t(p[1]) << 16) | (std::uint32_t(p[2]) << 8) | std::uint32_t(p[3]);
}

std::string lower_path(std::string s) {
    for (char &ch : s) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    return s;
}

std::string normalize_name(std::string s) {
    s = lower_path(std::move(s));
    for (char &ch : s) if (ch == '/') ch = '\\';
    // sceCdSearchFile paths often include ";1" version suffixes.
    if (const auto semi = s.find(';'); semi != std::string::npos) s.resize(semi);
    // Strip cdrom0: prefix if present.
    if (const auto colon = s.find(':'); colon != std::string::npos) s = s.substr(colon + 1);
    while (!s.empty() && (s[0] == '.' || s[0] == '\\')) s.erase(s.begin());
    return s;
}

std::uint32_t crc32_path(const std::string &path) {
    const std::string n = normalize_name(path);
    return static_cast<std::uint32_t>(::crc32(0L, reinterpret_cast<const Bytef *>(n.data()), static_cast<uInt>(n.size())));
}

bool load_index() {
    if (g_index.ready) return true;
    if (!disc::is_open()) return false;
    auto gfc = disc::find("cdrom0:\\ASSETS.GFC;1");
    if (!gfc) gfc = disc::find("cdrom0:\\ASSETS.GFC");
    auto gob = disc::find("cdrom0:\\ASSETS.GOB;1");
    if (!gob) gob = disc::find("cdrom0:\\ASSETS.GOB");
    if (!gfc || !gob) return false;
    const auto &gfc_e = *gfc;
    const auto &gob_e = *gob;
    std::vector<std::uint8_t> data((gfc_e.size + disc::kSector - 1) / disc::kSector * disc::kSector);
    if (!disc::read(gfc_e.sector, static_cast<std::uint32_t>(data.size() / disc::kSector), data.data())) return false;
    data.resize(gfc_e.size);
    if (data.size() < 16 || be32(data.data()) != kGfcSig) return false;
    const std::uint32_t gob_size = be32(data.data() + 4);
    const std::uint32_t nblocks = be32(data.data() + 8);
    const std::uint32_t nfiles = be32(data.data() + 12);
    std::size_t off = 16;
    if (off + nblocks * 12ull + nblocks * 4ull + nfiles * 12ull > data.size()) return false;
    Index idx;
    idx.gob_sector = gob_e.sector;
    idx.gob_size = gob_e.size ? gob_e.size : gob_size;
    idx.blocks.resize(nblocks);
    for (std::uint32_t i = 0; i < nblocks; ++i) {
        idx.blocks[i].compressed = be32(data.data() + off);
        idx.blocks[i].offset = be32(data.data() + off + 4);
        idx.blocks[i].next = be32(data.data() + off + 8);
        off += 12;
    }
    off += nblocks * 4ull; // adlers
    idx.files.resize(nfiles);
    for (std::uint32_t i = 0; i < nfiles; ++i) {
        idx.files[i].crc = be32(data.data() + off);
        idx.files[i].size = be32(data.data() + off + 4);
        idx.files[i].first = be32(data.data() + off + 8);
        off += 12;
    }
    // CNK extended name table is 72 bytes/file when present.
    if (off + nfiles * 72ull <= data.size()) {
        for (std::uint32_t i = 0; i < nfiles; ++i) {
            const char *n = reinterpret_cast<const char *>(data.data() + off);
            idx.files[i].name.assign(n, strnlen(n, 64));
            off += 72;
        }
    }
    for (std::size_t i = 0; i < idx.files.size(); ++i) {
        idx.by_crc[idx.files[i].crc] = i;
        if (idx.files[i].name.empty()) continue;
        const std::string n = normalize_name(idx.files[i].name);
        idx.by_name[n] = i;
        // Alias without leading "ps2\" / "common\" so CDVD probes like
        // \GFX\UI\BUTANIM.IGB resolve to .\ps2\gfx\ui\butanim.igb.
        auto alias = [&](std::string s) {
            if (!s.empty()) idx.by_name.emplace(std::move(s), i);
        };
        if (n.rfind("ps2\\", 0) == 0) alias(n.substr(4));
        if (n.rfind("common\\", 0) == 0) alias(n.substr(7));
        const auto slash = n.find_last_of('\\');
        if (slash != std::string::npos) alias(n.substr(slash + 1));
    }
    g_index = std::move(idx);
    g_index.ready = true;
    if (kernel::g_trace_modules || g_options.trace_iop_modules)
        std::fprintf(stderr, "[igfileio] GFC ready: %zu files, %zu blocks, gob sector 0x%X\n", g_index.files.size(),
                     g_index.blocks.size(), g_index.gob_sector);
    return true;
}

bool inflate_cluster(const std::uint8_t *src, std::uint32_t size, std::vector<std::uint8_t> &out) {
    if (size < 5) return false;
    if (std::memcmp(src, "STBL0", 5) == 0) {
        out.assign(src + 5, src + size);
        return true;
    }
    if (std::memcmp(src, "STBLz", 5) != 0) return false;
    z_stream zs{};
    if (inflateInit2(&zs, 15) != Z_OK) return false;
    zs.next_in = const_cast<Bytef *>(src + 5);
    zs.avail_in = size - 5;
    out.resize(std::max<std::uint32_t>(size * 4u, 256u));
    int rc = Z_OK;
    while (rc != Z_STREAM_END) {
        if (zs.total_out >= out.size()) out.resize(out.size() * 2);
        zs.next_out = out.data() + zs.total_out;
        zs.avail_out = static_cast<uInt>(out.size() - zs.total_out);
        rc = inflate(&zs, Z_NO_FLUSH);
        if (rc != Z_OK && rc != Z_STREAM_END) {
            inflateEnd(&zs);
            return false;
        }
    }
    out.resize(zs.total_out);
    inflateEnd(&zs);
    return true;
}

bool extract_file(const File &file, std::vector<std::uint8_t> &out) {
    if (!g_index.ready) return false;
    out.clear();
    out.reserve(file.size);
    std::uint32_t block = file.first;
    std::vector<std::uint8_t> cluster;
    std::vector<std::uint8_t> piece;
    unsigned guard = 0;
    while (block != 0x7FFFu && block < g_index.blocks.size() && guard++ < g_index.blocks.size() + 2) {
        const Block &b = g_index.blocks[block];
        const std::uint32_t sector = g_index.gob_sector + b.offset / disc::kSector;
        const std::uint32_t skip = b.offset % disc::kSector;
        const std::uint32_t need = b.compressed + skip;
        const std::uint32_t count = (need + disc::kSector - 1) / disc::kSector;
        cluster.resize(static_cast<std::size_t>(count) * disc::kSector);
        if (!disc::read(sector, count, cluster.data())) return false;
        if (!inflate_cluster(cluster.data() + skip, b.compressed, piece)) return false;
        out.insert(out.end(), piece.begin(), piece.end());
        block = b.next;
    }
    if (out.size() > file.size) out.resize(file.size);
    return out.size() == file.size || !out.empty();
}

std::uint32_t word_at(std::uint32_t args, std::uint32_t size, unsigned i) {
    if (args == sif::g_hle_send_addr && (i + 1) * 4u <= sif::g_hle_send.size()) {
        std::uint32_t v = 0;
        std::memcpy(&v, sif::g_hle_send.data() + i * 4u, 4);
        return v;
    }
    if ((i + 1) * 4u > size) return 0;
    std::uint32_t v = 0;
    std::memcpy(&v, g_ram + ((args + 4u * i) & (kRamSize - 1)), 4);
    return v;
}

std::string name_from_words(std::uint32_t args, std::uint32_t size, unsigned start_word) {
    std::string s;
    for (unsigned i = start_word; (i + 1) * 4u <= size / 4u * 4u && (i + 1) * 4u <= size; ++i) {
        const std::uint32_t w = word_at(args, size, i);
        for (int b = 0; b < 4; ++b) {
            const char ch = static_cast<char>((w >> (8 * b)) & 0xFF);
            if (!ch) return s;
            s.push_back(ch);
        }
    }
    // Also accept a pointer-to-string in word0/1.
    return s;
}

void store_ret(std::uint32_t ret, std::uint32_t ret_size, std::uint32_t a, std::uint32_t b = 0) {
    if (ret_size >= 4) store<std::uint32_t>(g_ram + (ret & (kRamSize - 1)), a);
    if (ret_size >= 8) store<std::uint32_t>(g_ram + ((ret + 4) & (kRamSize - 1)), b);
}

bool open_asset(const std::string &path, int &fd) {
    std::vector<std::uint8_t> data;
    if (!read_asset(path, data)) return false;
    fd = g_next_fd++;
    g_open[fd] = std::move(data);
    g_pos[fd] = 0;
    return true;
}

} // namespace

bool ensure_index() { return load_index(); }

bool read_asset(const std::string &path, std::vector<std::uint8_t> &out) {
    if (!ensure_index()) return false;
    const std::string n = normalize_name(path);
    auto it = g_index.by_name.find(n);
    if (it == g_index.by_name.end()) {
        // Drop platform prefix / try basename for CDVD-style probes.
        std::string alt = n;
        if (alt.rfind("ps2\\", 0) == 0) alt = alt.substr(4);
        else if (alt.rfind("common\\", 0) == 0) alt = alt.substr(7);
        it = g_index.by_name.find(alt);
        if (it == g_index.by_name.end()) {
            const auto slash = n.find_last_of('\\');
            if (slash != std::string::npos) it = g_index.by_name.find(n.substr(slash + 1));
        }
    }
    if (it == g_index.by_name.end()) {
        const std::uint32_t crc = crc32_path(path);
        auto jt = g_index.by_crc.find(crc);
        if (jt == g_index.by_crc.end()) return false;
        return extract_file(g_index.files[jt->second], out);
    }
    return extract_file(g_index.files[it->second], out);
}

bool read_asset_by_crc(std::uint32_t crc, std::vector<std::uint8_t> &out) {
    if (!ensure_index()) return false;
    auto it = g_index.by_crc.find(crc);
    if (it == g_index.by_crc.end()) return false;
    return extract_file(g_index.files[it->second], out);
}

namespace {

std::uint32_t g_stblz_last_key = 0;
bool g_host_fonts_extracted = false;
bool g_deferred_font_bind = false;

void rearm_walker_slot(std::uint32_t first, std::uint32_t want, std::uint32_t planted) {
    // Walker layout at 0x6F5B20 (stride 0x18): flag, first, current, … size/remain.
    // current==0x7FFF means "chain exhausted" — reset to first so inflate can run.
    if (0x006F5B20u < kRamSize) g_ram[0x006F5B20u] = 1;
    if (0x006F5B24u + 4 <= kRamSize) std::memcpy(g_ram + 0x006F5B24u, &first, 4);
    if (0x006F5B28u + 4 <= kRamSize) std::memcpy(g_ram + 0x006F5B28u, &first, 4);
    if (0x006F5B30u + 8 <= kRamSize) {
        std::memcpy(g_ram + 0x006F5B30u, &want, 4);
        std::memcpy(g_ram + 0x006F5B34u, &want, 4);
    }
    if (0x006F5AC0u + 4 <= kRamSize) std::memcpy(g_ram + 0x006F5AC0u, &planted, 4);
    const std::uint32_t gp = ps2::g_cpu.r[28].w[0];
    const std::uint32_t flag = gp - 31596u;
    if (gp && flag < kRamSize) {
        g_ram[flag] = 1;
        watch_span(flag, 1, "igfileio:walker-en");
        std::fprintf(stderr, "[igfileio] walker enable @0x%X (gp=0x%X)\n", flag, gp);
    }
}

// CNK parks the WRONG fonts cluster (block N instead of block0) in scratch, so
// guest zlib never produces the leading 64KB and UI draw never starts. When the
// load-slot CRC resolves, replace scratch with STBL0 of the file's first
// cluster so the guest fast path can copy it and continue the chain.
// Also re-arms when the walker exhausts (cur=0x7FFF) with STBL0 still sitting
// — otherwise the asset is dead forever after one pass.
// NOTE: 0x7430C0 is the FileIO ctx BASE (method 19 arg), NOT a scene igctx
// pointer — never use it as a "done" gate.
bool try_repair_first_cluster() {
    if (g_host_fonts_extracted) return false;
    constexpr std::uint32_t kPtr = 0x006F5AA8u, kCap = 0x006F5AB0u, kWant = 0x006F5B30u, kCrc = 0x007B3638u;
    constexpr std::uint32_t kFirst = 0x006F5B24u, kCur = 0x006F5B28u;
    if (kPtr + 4 > kRamSize || kCap + 4 > kRamSize || kWant + 4 > kRamSize || kCrc + 4 > kRamSize) return false;
    std::uint32_t ptr = 0, cap = 0, want = 0, crc = 0;
    std::memcpy(&ptr, g_ram + kPtr, 4);
    std::memcpy(&cap, g_ram + kCap, 4);
    std::memcpy(&want, g_ram + kWant, 4);
    std::memcpy(&crc, g_ram + kCrc, 4);
    // After walker exhaust, guest often zeros want/cap while STBL + CRC remain.
    if (!ptr || !crc || ptr >= kRamSize) return false;
    const bool is_stblz = std::memcmp(g_ram + ptr, "STBLz", 5) == 0;
    const bool is_stbl0 = std::memcmp(g_ram + ptr, "STBL0", 5) == 0;
    const bool is_stbl = std::memcmp(g_ram + ptr, "STBL", 4) == 0;
    if (!is_stblz && !is_stbl0 && !is_stbl) return false;
    if (!ensure_index()) return false;
    auto it = g_index.by_crc.find(crc);
    if (it == g_index.by_crc.end()) {
        static int s_miss = 0;
        if (s_miss < 4) {
            std::fprintf(stderr, "[igfileio] repair: crc 0x%08X not in GFC index\n", crc);
            ++s_miss;
        }
        return false;
    }
    const File &file = g_index.files[it->second];
    if (file.first >= g_index.blocks.size()) return false;
    if (!want || want != file.size) {
        static int s_sz = 0;
        if (s_sz < 4) {
            std::fprintf(stderr, "[igfileio] repair: want=%u cap=%u -> file.size=%u\n", want, cap, file.size);
            ++s_sz;
        }
        want = file.size;
    }
    // Scratch capacity: guest often parks a tiny/wrong cap (observed 32768 while
    // STBL0 needs 65541). Prefer enough room for one inflated 64KB cluster when
    // the pointer is in RAM; never write past kRamSize.
    {
        constexpr std::uint32_t kNeed = 5u + 0x10000u; // STBL0 + 64KiB
        const std::uint32_t room = (ptr < kRamSize) ? (kRamSize - ptr) : 0;
        std::uint32_t prefer = kNeed;
        if (prefer > 0x20000u) prefer = 0x20000u;
        if (prefer > room) prefer = room;
        if (!cap || cap < prefer || cap > kRamSize || ptr + cap > kRamSize) cap = prefer;
    }
    std::uint32_t walk_first = 0, walk_cur = 0;
    if (kFirst + 4 <= kRamSize) std::memcpy(&walk_first, g_ram + kFirst, 4);
    if (kCur + 4 <= kRamSize) std::memcpy(&walk_cur, g_ram + kCur, 4);
    const bool exhausted = walk_cur == 0x7FFFu;
    const bool wrong_first = walk_first != file.first;
    // Already holding correct STBL0 with a live cursor — leave it alone.
    if (is_stbl0 && !exhausted && !wrong_first && g_stblz_last_key == (crc ^ want ^ ptr)) return false;

    const Block &b0 = g_index.blocks[file.first];
    std::vector<std::uint8_t> raw(b0.compressed);
    {
        const std::uint32_t sector = g_index.gob_sector + b0.offset / disc::kSector;
        const std::uint32_t skip = b0.offset % disc::kSector;
        const std::uint32_t need = b0.compressed + skip;
        const std::uint32_t count = (need + disc::kSector - 1) / disc::kSector;
        std::vector<std::uint8_t> cluster(static_cast<std::size_t>(count) * disc::kSector);
        if (!disc::read(sector, count, cluster.data())) return false;
        std::memcpy(raw.data(), cluster.data() + skip, b0.compressed);
    }
    // STBLz that already matches block0 and has a live cursor needs no rewrite.
    if (is_stblz && !exhausted && !wrong_first) {
        const std::uint32_t cmp_n = std::min<std::uint32_t>(b0.compressed, 128u);
        if (b0.compressed <= cap && std::memcmp(g_ram + ptr, raw.data(), cmp_n) == 0) return false;
    }
    const std::uint32_t key = crc ^ want ^ ptr;
    // Guest frequently clobbers our STBL0 back to a wrong STBLz while igctx is
    // still empty. Treat "not STBL0" as dirty and re-plant even if the key matches.
    const bool dirty = !is_stbl0;
    if (key == g_stblz_last_key && !exhausted && !wrong_first && !dirty) return false;
    if ((exhausted || dirty) && !wrong_first && key == g_stblz_last_key) {
        static int s_rearm_cool = 0;
        if (s_rearm_cool > 0) {
            --s_rearm_cool;
            return false;
        }
        s_rearm_cool = dirty ? 90 : 45; // don't thrash STBL0 over the logo path
    }
    if (b0.compressed > cap) return false;

    std::vector<std::uint8_t> inflated;
    std::uint32_t planted = b0.compressed;
    const char *kind = "STBLz";
    if (inflate_cluster(raw.data(), b0.compressed, inflated) && 5u + inflated.size() <= cap) {
        std::memcpy(g_ram + ptr, "STBL0", 5);
        std::memcpy(g_ram + ptr + 5, inflated.data(), inflated.size());
        planted = 5u + static_cast<std::uint32_t>(inflated.size());
        kind = "STBL0";
    } else {
        std::memcpy(g_ram + ptr, raw.data(), b0.compressed);
    }
    watch_span(ptr, planted, "igfileio:stblz-repair");
    rearm_walker_slot(file.first, want, planted);
    g_stblz_last_key = key;
    std::fprintf(stderr, "[igfileio] repaired first-cluster crc=0x%08X @0x%X (%u bytes %s, cur=first=%u%s%s)\n",
                 crc, ptr, planted, kind, file.first,
                 exhausted ? " rearm-exhausted" : "",
                 wrong_first ? " fix-first" : "");
    return true;
}

bool alchemy_stbl_pending() {
    // STBL0 planted + fonts CRC known ⇒ walker/bind may still need kicks.
    // 0x7430C0 is FileIO ctx base (not scene igctx) — do not gate on it.
    // Opt out once gob attach stuck: PS2_ALCHEMY_PENDING_UNTIL_ATTACH unset
    // keeps pending even after F0BC so TIM0/FINISH keep firing.
    constexpr std::uint32_t kPtr = 0x006F5AA8u, kCrc = 0x007B3638u;
    if (kPtr + 4 > kRamSize || kCrc + 4 > kRamSize) return false;
    std::uint32_t ptr = 0, crc = 0;
    std::memcpy(&ptr, g_ram + kPtr, 4);
    std::memcpy(&crc, g_ram + kCrc, 4);
    if (!ptr || !crc || ptr >= kRamSize || ptr + 5 > kRamSize) return false;
    return std::memcmp(g_ram + ptr, "STBL0", 5) == 0;
}

// Shared Alchemy UI stream assemble (CNK: stream+0x48 → 0xBD1000).
std::uint32_t butanim_assemble_dst() {
    std::uint32_t lg = 0;
    std::memcpy(&lg, g_ram + 0x006F2540u, 4);
    if (!lg || lg + 8u * 96u + 0x50u >= kRamSize) return 0;
    for (std::uint32_t i = 0; i < 8u; ++i) {
        const std::uint32_t slot = lg + i * 96u;
        const char *spath = reinterpret_cast<const char *>(g_ram + slot + 8u);
        if (!(std::strstr(spath, "butanim") || std::strstr(spath, "BUTANIM"))) continue;
        std::uint32_t stream = 0;
        std::memcpy(&stream, g_ram + slot + 0x4Cu, 4);
        if (!stream || stream + 0x4Cu >= kRamSize) return 0;
        std::uint32_t dst = 0;
        std::memcpy(&dst, g_ram + stream + 0x48u, 4);
        return dst;
    }
    return 0;
}

bool assemble_holds_butanim() {
    constexpr std::uint32_t kPlant = 0x01B00000u;
    const std::uint32_t dst = butanim_assemble_dst();
    if (!dst || dst + 8u > kRamSize || kPlant + 8u > kRamSize) return false;
    return std::memcmp(g_ram + dst, g_ram + kPlant, 8) == 0;
}

// Restore obj+0x20 if it was cleared since soft-arm. vt+108 needs *(+0x20)+0x24≠0
// to run the 0x51C100 ingest path. Must be called BEFORE vt+108 runs.
// Returns true if restoration happened.
bool try_restore_butanim_o20() {
    if (!g_butanim_soft_obj || g_butanim_soft_obj + 0x100u > kRamSize) return false;
    if (!g_butanim_soft_o20 || g_butanim_soft_o20 >= kRamSize) return false;
    // Already restored enough times — don't thrash.
    if (g_butanim_o20_restore_count >= 12) return false;

    std::uint32_t cur_o20 = 0;
    std::memcpy(&cur_o20, g_ram + g_butanim_soft_obj + 0x20u, 4);

    // +0x20 still live — nothing to do.
    if (cur_o20 != 0) return false;

    // +0xFF already set means vt+108 already ran with +0x20=0, skipping 0x51C100.
    // Clear +0xFF so the next guest tick can retry vt+108 with restored +0x20.
    // This is safe: we are NOT re-arming status (that crashed ra=0x110224).
    const bool ff_set = g_ram[g_butanim_soft_obj + 0xffu] != 0;
    if (ff_set && g_butanim_o20_restore_count < 4) {
        // Clear +0xFF so guest vt+108 path can run again with live +0x20.
        g_ram[g_butanim_soft_obj + 0xffu] = 0;
        g_butanim_saw_ff_clear = true; // Re-arm our own detection.
    }

    // Restore +0x20 from soft-arm capture.
    std::memcpy(g_ram + g_butanim_soft_obj + 0x20u, &g_butanim_soft_o20, 4);
    // Also restore +0x14 if captured.
    if (g_butanim_soft_o14 && g_butanim_soft_o14 < kRamSize) {
        std::memcpy(g_ram + g_butanim_soft_obj + 0x14u, &g_butanim_soft_o14, 4);
    }
    ++g_butanim_o20_restore_count;

    // Verify the attach chain: *(obj+0x20)+0x24 should be non-zero for 0x51C100.
    std::uint32_t attach = 0;
    if (g_butanim_soft_o20 + 0x28u <= kRamSize) {
        std::memcpy(&attach, g_ram + g_butanim_soft_o20 + 0x24u, 4);
    }

    static int s_log = 0;
    if (s_log < 12) {
        std::fprintf(stderr,
                     "[igfileio] restored butanim obj+0x20=0x%X +0x14=0x%X (was 0, +0xFF=%d→%d, "
                     "*(+0x20)+0x24=0x%X, count=%d)\n",
                     g_butanim_soft_o20, g_butanim_soft_o14, ff_set ? 1 : 0,
                     g_ram[g_butanim_soft_obj + 0xffu], attach, g_butanim_o20_restore_count);
        ++s_log;
    }
    return true;
}

void poll_butanim_parse_complete() {
    if (g_ui_igb_parse_attempted || g_butanim_parsed_ok) return;
    if (!g_butanim_soft_obj || g_butanim_soft_obj + 0x100u > kRamSize) return;

    // BEFORE checking +0xFF: restore +0x20 if it was cleared. This gives vt+108
    // a chance to run the 0x51C100 ingest path on its next iteration.
    try_restore_butanim_o20();

    if (!g_ram[g_butanim_soft_obj + 0xffu]) {
        g_butanim_saw_ff_clear = true;
        return;
    }
    std::uint32_t o20 = 0;
    std::memcpy(&o20, g_ram + g_butanim_soft_obj + 0x20u, 4);
    // vt+108 (0x5032E0) sets +0xFF even when +0x20==0 (skips 0x51C100 ingest).
    // Only release intro once +0x20 is live AND scratch still holds butanim.
    if (g_butanim_saw_ff_clear && o20 != 0 && assemble_holds_butanim()) {
        g_butanim_parsed_ok = true;
        g_ui_igb_parse_attempted = true;
        std::fprintf(stderr,
                     "[igfileio] UI parse complete (butanim obj=0x%X +0xFF +20=0x%X plant ok, release intro)\n",
                     g_butanim_soft_obj, o20);
        return;
    }
    const bool plant_ok = assemble_holds_butanim();
    if (g_butanim_saw_ff_clear && !plant_ok) {
        // Clobbered scratch stamped +0xFF — clear so a later guest pass can retry.
        g_ram[g_butanim_soft_obj + 0xffu] = 0;
        static int s_false = 0;
        if (s_false < 4) {
            std::fprintf(stderr,
                         "[igfileio] butanim +0xFF with wrong scratch; clear and keep intro hold\n");
            ++s_false;
        }
    } else if (g_butanim_saw_ff_clear && plant_ok && o20 == 0) {
        // vt+108 ran with good bytes but skipped 0x51C100 (+20==0). +20 was
        // restored above; if it got cleared again, wait and let the next
        // guest tick retry. Do NOT re-arm status (crashed ra 0x110224).
        static int s_weak = 0;
        if (s_weak < 8) {
            std::fprintf(stderr,
                         "[igfileio] butanim vt+108 weak (+20=0 after restore, plant ok); holding\n");
            ++s_weak;
        }
    }
}

// FINISH's guest path DisableIntc(TIM0/TIM1) and leaves Alchemy WaitSema pumps
// parked even though MODE still has compare/overflow IE and work is queued.
// Re-arm those causes (and wake if STAT already latched) while a GFC cluster
// is still waiting in the Alchemy scratch slot.
void rearm_alchemy_timer_intc() {
    if (!alchemy_stbl_pending()) return;
    // Restore obj+0x20 aggressively on every timer rearm tick, before vt+108 can
    // run with +20=0. This is the earliest hook during guest FCE0 processing.
    if (g_butanim_soft_obj && g_butanim_soft_o20 && !g_ui_igb_parse_attempted) {
        try_restore_butanim_o20();
    }
    // Ensure INTC masks + keep TIM0/1 actually counting. Do NOT rewrite COMP:
    // forcing comp=count+N with reset-on-compare caused a TIM0 IRQ storm.
    for (int n : {0, 1}) hw::timer_keep_counting(n);
    for (unsigned cause : {9u, 10u}) {
        if (hw::intc_set_mask(cause, true))
            std::fprintf(stderr, "[igfileio] re-armed INTC cause %u (Alchemy STBL pending)\n", cause);
    }
    // Guest often masks GS FINISH (IMR bit 0x200) while the Alchemy gate still
    // needs FINISH IRQs to advance 705C00. Also keep VSINT (0x800) live — with
    // it masked, the prio-0 thread parks forever on WaitSema(2) and never reaches
    // the GOB pump. Clear both while STBL is pending.
    {
        // FINISH=bit1→IMR 0x200, VSINT=bit3→IMR 0x800 (see gs.cpp raise()).
        const std::uint64_t imr = hw::gs_imr();
        constexpr std::uint64_t kNeed = 0xA00ull;
        if (imr & kNeed) {
            hw::gs_set_imr(imr & ~kNeed);
            static int s_imr = 0;
            if (s_imr < 4) {
                std::fprintf(stderr, "[igfileio] unmasked GS FINISH/VSINT (IMR 0x%llX)\n",
                             static_cast<unsigned long long>(imr));
                ++s_imr;
            }
        }
    }
    // Guest may have cleared the walker enable bytes while parking on WaitSema.
    // Put them back so translated inflate/walker code can observe work pending —
    // but once we host-extracted the full fonts file, leave the flag clear so
    // the EE does not think a GOB walk is still outstanding.
    if (!g_host_fonts_extracted) {
        if (0x006F5B20u < kRamSize && !g_ram[0x006F5B20u]) g_ram[0x006F5B20u] = 1;
        {
            const std::uint32_t gp = ps2::g_cpu.r[28].w[0];
            const std::uint32_t flag = gp - 31596u;
            if (gp && flag < kRamSize && !g_ram[flag]) g_ram[flag] = 1;
        }
    }
}

} // namespace

void kick_finish_gate_once() {
    // Delay helper at 0x422FA0 does tgt++ then WaitSema(45) until ctr+offset >= tgt
    // (offset @6542D8, usually 2). When FINISH lags, gap sticks at 2-3 and thread 1
    // never climbs back into 0x10xxxx Alchemy. Pulling tgt→ctr exits the wait.
    if (!alchemy_stbl_pending()) return;
    constexpr std::uint32_t kCtr = 0x00705C00u, kTgt = 0x006542A0u, kSema = 0x00705C18u;
    std::uint64_t ctr = 0, tgt = 0;
    std::uint32_t sema = 0;
    std::memcpy(&ctr, g_ram + kCtr, 8);
    std::memcpy(&tgt, g_ram + kTgt, 8);
    std::memcpy(&sema, g_ram + kSema, 4);
    if (!sema || sema > 255u) return;

    // Host-calls of the walker/pump hang: run_guest sets EXL so WaitSema cannot
    // block and the guest spins forever. Instead keep the FINISH WaitSema(45)
    // gate clamped so thread 1 can drive Alchemy (and eventually the walker)
    // itself once STBL0 is planted (ctr past early boot).
    if (ctr > 200u) {
        if (tgt > ctr) {
            std::memcpy(g_ram + kTgt, &ctr, 8);
            static int s_clamp = 0;
            if (s_clamp < 8) {
                std::fprintf(stderr, "[igfileio] finish-clamp %llu <- %llu\n",
                             static_cast<unsigned long long>(ctr), static_cast<unsigned long long>(tgt));
                ++s_clamp;
            }
        }
        ps2::kernel::host_signal_sema(static_cast<int>(sema));
        std::uint32_t s47 = 0, lock = 0;
        std::memcpy(&s47, g_ram + 0x00705C10u, 4);
        std::memcpy(&lock, g_ram + 0x00705F18u, 4);
        for (int id : {static_cast<int>(s47), static_cast<int>(lock), 16, 47, 50, 2})
            if (id > 0 && id < 256) ps2::kernel::host_signal_sema(id);
        return;
    }

    static int s_stuck = 0;
    const bool deep_gap = ctr < tgt && (tgt - ctr) >= 2u;
    if (!deep_gap) {
        s_stuck = 0;
        return;
    }
    if (++s_stuck < 20) return;
    std::memcpy(g_ram + kTgt, &ctr, 8);
    ps2::kernel::host_signal_sema(static_cast<int>(sema));
    static int s_log = 0;
    if (s_log < 8) {
        std::fprintf(stderr, "[igfileio] finish-target-pull %llu <- %llu\n",
                     static_cast<unsigned long long>(ctr), static_cast<unsigned long long>(tgt));
        ++s_log;
    }
    s_stuck = 0;
}

void kick_alchemy_timer_lock() {
    // TIM0 handler iSignalSemas the lock at 0x705F18 (observed id 16). When
    // that lock is held and STBL is pending, pulse it so 0x427470 can finish
    // arming the compare timer for the WaitSema delay helper.
    if (!alchemy_stbl_pending()) return;
    constexpr std::uint32_t kLock = 0x00705F18u;
    if (kLock + 4 > kRamSize) return;
    std::uint32_t id = 0;
    std::memcpy(&id, g_ram + kLock, 4);
    if (!id || id > 255u) return;
    static int s_pulse = 0;
    // Once the FINISH gate is past early boot, both prio-1/2 threads sit on this
    // lock — pulse every tick so 0x427470 can arm TIM0 delays.
    std::uint32_t gate_ctr = 0;
    std::memcpy(&gate_ctr, g_ram + 0x00705C00u, 4);
    const int period = (g_host_fonts_extracted || gate_ctr > 200u) ? 1 : 8;
    if ((++s_pulse % period) != 0) return;
    if (ps2::kernel::host_signal_sema(static_cast<int>(id))) {
        static int s_log = 0;
        if (s_log < 12) {
            std::fprintf(stderr, "[igfileio] pulsed Alchemy timer-lock sema %u\n", id);
            ++s_log;
        }
    }
}

void kick_alchemy_tim0_irq() {
    // Alchemy delay arm leaves 705DF8 = remaining compare hits. The TIM0 INTC
    // handler (0x426EF0) only iSignalSemas the waiter list at 705F10 once that
    // counter hits 0 — so we need real IRQs. Guest often rewrites COMP to a
    // far value before our +8 pulse can fire; raise TIM0 directly while DF8
    // still has work so the handler can drain and wake the delay list (47).
    // Do NOT raise when DF8==0 just because the free-list pointer is non-null:
    // that spams iSignalSema and desyncs the FINISH gate (705C18 / sema 45).
    // After fonts extract, throttle DF8 drains (was a storm) but still service
    // armed delays so WaitSema(47/50) in 0x427234 can complete.
    if (!alchemy_stbl_pending()) return;
    if (0x00705DF8u + 4 > kRamSize || 0x00705F10u + 4 > kRamSize) return;
    std::uint32_t df8 = 0, list = 0;
    std::memcpy(&df8, g_ram + 0x00705DF8u, 4);
    std::memcpy(&list, g_ram + 0x00705F10u, 4);
    if (!df8) return; // only drain an armed delay; final IRQ handled below
    if (g_host_fonts_extracted) {
        static int s_post = 0;
        if ((++s_post % 4) != 0) return;
    }
    hw::timer_keep_counting(0);
    hw::timer_arm_compare_pulse(0);
    hw::intc_set_mask(9u, true);
    hw::intc_raise(9u);
    static int s_log = 0;
    if (s_log < 40) {
        std::fprintf(stderr, "[igfileio] forced TIM0 IRQ (df8=%u list=0x%X)\n", df8, list);
        ++s_log;
    }
}

void kick_alchemy_tim0_complete() {
    // After DF8 drains to 0 the next TIM0 IRQ takes the iSignalSema path. Raise
    // one extra when DF8==0, the waiter list is armed, and the FINISH gate is
    // healthy so we do not reopen a gap>=3 treadmill.
    // Post-extract: thread 1 parks on WaitSema(50) in the TIM0 delay helper
    // (0x427234) — keep completing those IRQs or the frame path stalls again.
    if (!alchemy_stbl_pending()) return;
    std::uint32_t df8 = 0, list = 0;
    std::memcpy(&df8, g_ram + 0x00705DF8u, 4);
    std::memcpy(&list, g_ram + 0x00705F10u, 4);
    if (df8 || !list) return;
    std::uint64_t ctr = 0, tgt = 0;
    std::memcpy(&ctr, g_ram + 0x00705C00u, 8);
    std::memcpy(&tgt, g_ram + 0x006542A0u, 8);
    if (!g_host_fonts_extracted && tgt > ctr + 1) return;
    static int s_cool = 0;
    if (++s_cool < (g_host_fonts_extracted ? 2 : 4)) return;
    s_cool = 0;
    hw::intc_set_mask(9u, true);
    hw::intc_raise(9u);
    static int s_log = 0;
    if (s_log < 12) {
        std::fprintf(stderr, "[igfileio] TIM0 complete IRQ (list=0x%X gate %llu/%llu)\n", list,
                     static_cast<unsigned long long>(ctr), static_cast<unsigned long long>(tgt));
        ++s_log;
    }
}

void kick_alchemy_delay_semas() {
    // Sema at 705C18 is shared with the FINISH gate — never host-signal it here.
    // Nudge delay slot 705C10 (46/47/50) and main-thread sema 2 when fonts are
    // host-extracted (thread 2 parks forever on WaitSema(2)).
    if (!alchemy_stbl_pending()) return;
    std::uint64_t ctr = 0, tgt = 0;
    std::memcpy(&ctr, g_ram + 0x00705C00u, 8);
    std::memcpy(&tgt, g_ram + 0x006542A0u, 8);
    if (tgt > ctr + 2) return;
    static int s_cool = 0;
    if (++s_cool < 8) return;
    s_cool = 0;
    std::uint32_t s47 = 0;
    std::memcpy(&s47, g_ram + 0x00705C10u, 4);
    for (int id : {static_cast<int>(s47), 47, 50}) {
        if (id > 0 && id < 256) ps2::kernel::host_signal_sema(id);
    }
    if (g_host_fonts_extracted) ps2::kernel::host_signal_sema(2);
    hw::timer_arm_compare_pulse(0);
    static int s_log = 0;
    if (s_log < 8) {
        std::fprintf(stderr, "[igfileio] pulsed delay sema slot s47=%u%s\n", s47,
                     g_host_fonts_extracted ? " +sema2" : "");
        ++s_log;
    }
}

bool prepare_guest_walker_dest() {
    // Do NOT force arm635138=-1: 0x242480 with arm==-1 is TEARDOWN (freelist
    // walk at 0x239A80), not inflate. Prep 0x242D20 sets -1 itself when done.
    // Dest retarget is owned by gob-extract (prefers heap-via-slot over scratch).
    if (!alchemy_stbl_pending()) return false;
    constexpr std::uint32_t kDest = 0x006F5AB8u;
    std::uint32_t dest = 0;
    std::memcpy(&dest, g_ram + kDest, 4);
    static int s_log = 0;
    if (s_log < 4) {
        std::uint32_t arm_now = 0, head = 0;
        std::memcpy(&arm_now, g_ram + 0x00635138u, 4);
        if (dest && dest + 4 <= kRamSize) std::memcpy(&head, g_ram + dest, 4);
        std::fprintf(stderr, "[igfileio] guest-walker dest=0x%X head=0x%X arm635138=0x%X flag=%u\n",
                     dest, head, arm_now, static_cast<unsigned>(g_ram[0x006F5B20u]));
        ++s_log;
    }
    return false;
}

bool try_kick_alchemy_font_tick() {
    // ready==1 means "loaders finished — tear them down" (0x109C28 destroys
    // loadgates). Do NOT poke ready early: that frees our scratch dest and
    // hangs the freelist at 0x239A80. Instead clear loadgate+24016 (+0x5DD0) so
    // per-frame 0x10F560 keeps calling guest 0x10FCE0 on tid1 after soft-arm
    // (end-of-walk otherwise sets +5DD0 and permanently skips the pump).
    // +24008: set when CDVD finds UI IGBs; 0x10F560 → 0x23AF50 delay. Do NOT
    // clear the flag (IO spam at 0x428970). With CDVD-GFC, keep signaling so
    // the delay returns and CDVD completion can clear +24008 itself.
    // Alchemy/CNK only — Hitman/NFS never plant STBL0 here.
    if (!alchemy_stbl_pending()) return false;
    // Restore obj+0x20 BEFORE guest FCE0/vt+108 runs. vt+108 needs *(+0x20)+0x24≠0
    // to run the 0x51C100 ingest path; something clears +0x20 between soft-arm and
    // the guest tick. Restoring it here gives the next guest FCE0 iteration a live
    // pointer so 0x51C100 ingest sticks and prims >> 2.
    try_restore_butanim_o20();
    // Do NOT re-stick gob+912: guest writes 0xCA/202 as a real intermediate;
    // forcing 1 fought the native path (seen under PS2_ALCHEMY_NO_BIND too).
    std::uint32_t lg = 0;
    std::memcpy(&lg, g_ram + 0x006F2540u, 4);
    if (!lg || lg + 24025u > kRamSize) return false;
    bool changed = false;
    if (g_ram[lg + 24016u] != 0) {
        g_ram[lg + 24016u] = 0;
        changed = true;
    }
    // Default-on with CDVD-GFC (unless PS2_ALCHEMY_NO_CDVD_GFC).
    // Do NOT clear +24008 — that IO-spams at 0x428970. Guest must clear it.
    if (g_ram[lg + 24008u] != 0 && !std::getenv("PS2_ALCHEMY_NO_CDVD_GFC")) {
        for (int id : {16, 54, 55}) ps2::kernel::host_signal_sema(id);
        static int s_sig = 0;
        if (s_sig < 3) {
            std::fprintf(stderr, "[igfileio] signal 16/54/55 while +24008 set (GFC UI)\n");
            ++s_sig;
        }
        // Keep +24008 set (clearing it IO-spams at 0x428970). Sema signals
        // above wake the waiter so 0x10FAF0/0x10FCE0 can run between sectors.
    }
    if (changed) {
        static int s_log = 0;
        if (s_log < 6) {
            std::fprintf(stderr, "[igfileio] cleared loadgate+24016 @0x%X (enable font tick)\n", lg);
            ++s_log;
        }
    }
    // BUTANIM parse gate (CNK shared scratch BD1000):
    // - Soft-arm sets obj+45 but must NOT release the intro hold (that clobbered
    //   butanim bytes with INTROTXR before vt+108 ran → prims stuck at 2).
    // - Latch parse-attempted only when soft-armed obj+0xFF is set (vt+108 done).
    // - While pending: keep +5DD0 clear, restore slot/obj/+45 if finalize failed
    //   (status=4/obj=0), and re-copy butanim plant if intro already landed.
    // Do NOT host_call FCE0 — wrong EE tid → jalr null @ ra 0x51ACEC.
    {
        poll_butanim_parse_complete();
        if (!g_ui_igb_parse_attempted && g_butanim_soft_obj && g_butanim_soft_obj + 0x100u <= kRamSize) {
            constexpr std::uint32_t kPlantButanim = 0x01B00000u;
            constexpr std::uint32_t kPlantIntro = 0x01B80000u;
            std::uint32_t butanim_slot = 0, butanim_i = 0;
            for (std::uint32_t i = 0; i < 8u; ++i) {
                const std::uint32_t slot = lg + i * 96u;
                if (slot + 0x5Cu >= kRamSize) break;
                const char *spath = reinterpret_cast<const char *>(g_ram + slot + 8u);
                if (!(std::strstr(spath, "butanim") || std::strstr(spath, "BUTANIM"))) continue;
                butanim_slot = slot;
                butanim_i = i;
                break;
            }
            if (butanim_slot) {
                std::uint32_t stream = 0, dst = 0, st = 0, obj = 0;
                std::memcpy(&stream, g_ram + butanim_slot + 0x4Cu, 4);
                std::memcpy(&st, g_ram + butanim_slot + 0x54u, 4);
                std::memcpy(&obj, g_ram + butanim_slot + 0x58u, 4);
                if (stream && stream + 0x4Cu < kRamSize) std::memcpy(&dst, g_ram + stream + 0x48u, 4);
                // Intro landed on shared scratch before butanim vt+108 — put butanim back.
                if (dst >= 0x00100000u && dst + 16u <= kRamSize && kPlantIntro + 16u <= kRamSize &&
                    kPlantButanim + 16u <= kRamSize &&
                    std::memcmp(g_ram + dst, g_ram + kPlantIntro, 8) == 0 &&
                    std::memcmp(g_ram + kPlantButanim, g_ram + kPlantIntro, 8) != 0) {
                    // Only the butanim plant size — never 0x6F5A2C (that tracks the
                    // latest virt ingest and becomes intro's ~400KB after clobber).
                    std::uint32_t nbytes = g_butanim_plant_size ? g_butanim_plant_size : 0x1098u;
                    if (nbytes >= 0x100u && nbytes <= 0x10000u && dst + nbytes <= kRamSize &&
                        kPlantButanim + nbytes <= kRamSize) {
                        std::memcpy(g_ram + dst, g_ram + kPlantButanim, nbytes);
                        watch_span(dst, nbytes, "igfileio:butanim-restore");
                        static int s_rest = 0;
                        if (s_rest < 4) {
                            std::fprintf(stderr,
                                         "[igfileio] restored butanim plant -> 0x%X (%u B; intro had clobbered)\n",
                                         dst, nbytes);
                            ++s_rest;
                        }
                    }
                }
                // Keep +5DD0 clear and wake tid1 so guest 0x10F560→0x10FCE0 can
                // run. Do NOT force status back to 1 after finalize has advanced
                // the slot (status 3/4) — that re-entered 0x110100 on a mutated
                // object and jalr'd heap junk @0x974768 (ra 0x110224).
                if (g_ram[lg + 24016u] != 0) {
                    g_ram[lg + 24016u] = 0;
                    changed = true;
                }
                static int s_pump = 0;
                if (s_pump < 4) {
                    std::fprintf(stderr,
                                 "[igfileio] butanim pump-wait slot%u st=%u obj=0x%X soft=0x%X +45=%u "
                                 "(+5DD0 clear, no host FCE0)\n",
                                 butanim_i, st, obj, g_butanim_soft_obj,
                                 (g_butanim_soft_obj && g_butanim_soft_obj + 46u < kRamSize)
                                     ? g_ram[g_butanim_soft_obj + 45u]
                                     : 0);
                    ++s_pump;
                }
            }
            // Wake tid1 if parked in 0x10F560's registry delay (often sema 50).
            for (int id : {47, 50, 16, 54, 55}) ps2::kernel::host_signal_sema(id);
        }
    }
    return changed;
}

bool try_host_call_alchemy_walker() {
    // Prefer pump 0x23ED50 once its vtable slot is live. Never host_call
    // 0x242480 while arm==-1 (teardown → freelist hang).
    if (!alchemy_stbl_pending()) return false;
    static bool s_pump_done = false, s_prep_done = false;
    if (s_pump_done) return false;
    std::uint64_t ctr = 0, tgt = 0;
    std::memcpy(&ctr, g_ram + 0x00705C00u, 8);
    std::memcpy(&tgt, g_ram + 0x006542A0u, 8);
    if (tgt > ctr + 2) return false;
    // Pump jalr uses *(**(0x6F58C8)+88). Skip while null.
    std::uint32_t pump_obj = 0, vt = 0, slot = 0;
    std::memcpy(&pump_obj, g_ram + 0x006F58C8u, 4);
    if (pump_obj && pump_obj + 4 <= kRamSize) std::memcpy(&vt, g_ram + pump_obj, 4);
    if (vt && vt + 92 <= kRamSize) std::memcpy(&slot, g_ram + vt + 88u, 4);
    const std::uint32_t gp = 0x006F9BF0u;
    if (slot && slot >= 0x00100000u && slot < kRamSize) {
        // 0x23ED50 is not an entry — real trampoline is 0x23ED40 → 0x23DF20.
        std::fprintf(stderr, "[igfileio] host-call Alchemy pump 0x23ED40 slot=0x%X gp=0x%X\n", slot, gp);
        s_pump_done = true;
        const std::uint32_t rc = ps2::kernel::host_call(0x0023ED40u, 0, gp);
        std::uint32_t cur = 0, ctx = 0;
        std::memcpy(&cur, g_ram + 0x006F5B28u, 4);
        std::memcpy(&ctx, g_ram + 0x007430C0u, 4);
        std::fprintf(stderr, "[igfileio] pump returned 0x%X walk_cur=%u igctx=0x%X\n", rc, cur, ctx);
        return true;
    }
    if (s_prep_done) return false;
    std::fprintf(stderr, "[igfileio] host-call Alchemy prep 0x242D20 (pump slot=0x%X) gp=0x%X\n", slot, gp);
    s_prep_done = true;
    const std::uint32_t rc = ps2::kernel::host_call(0x00242D20u, 0, gp);
    std::uint32_t cur = 0, ctx = 0, arm = 0;
    std::memcpy(&cur, g_ram + 0x006F5B28u, 4);
    std::memcpy(&ctx, g_ram + 0x007430C0u, 4);
    std::memcpy(&arm, g_ram + 0x00635138u, 4);
    std::fprintf(stderr, "[igfileio] prep returned 0x%X walk_cur=%u igctx=0x%X arm635138=0x%X\n",
                 rc, cur, ctx, arm);
    return true;
}

bool try_host_step_gob_cluster() {
    // Guest walker never runs (threads parked on TIM0/FINISH). Dest 0x7AF300
    // still holds live heap — retarget to high scratch and host-inflate the
    // whole fonts GOB chain (CRC at 0x7B3638) so remain hits 0.
    if (!alchemy_stbl_pending()) return false;
    static bool s_done = false;
    if (s_done) return false;
    std::uint64_t ctr = 0, tgt = 0;
    std::memcpy(&ctr, g_ram + 0x00705C00u, 8);
    std::memcpy(&tgt, g_ram + 0x006542A0u, 8);
    if (tgt > ctr + 2) return false;
    if (!ensure_index()) return false;
    std::uint32_t crc = 0, dest = 0, want = 0;
    std::memcpy(&crc, g_ram + 0x007B3638u, 4);
    std::memcpy(&dest, g_ram + 0x006F5AB8u, 4);
    std::memcpy(&want, g_ram + 0x006F5B30u, 4);
    auto it = g_index.by_crc.find(crc);
    if (it == g_index.by_crc.end()) return false;
    const File &file = g_index.files[it->second];
    std::vector<std::uint8_t> out;
    if (!extract_file(file, out) || out.empty()) return false;
    if (!want) want = file.size;
    if (out.size() > want) out.resize(want);
    std::uint32_t head = 0;
    if (dest && dest + 4 <= kRamSize) std::memcpy(&head, g_ram + dest, 4);
    // 0x7AF300 holds live game state — overwriting it jalr's null. Always use
    // high scratch for host extract; freelist-escape covers teardown frees.
    constexpr std::uint32_t kScratch = 0x01A00000u;
    const char *where = "dest";
    if (!dest || dest >= kRamSize || dest == 0x007AF300u || dest + out.size() > kRamSize ||
        (head >= 0x00100000u && head < kRamSize)) {
        dest = kScratch;
        if (dest + out.size() > kRamSize) return false;
        std::memcpy(g_ram + 0x006F5AB8u, &dest, 4);
        where = "scratch";
    }
    // GFC extract is the STBL0 body (no magic). Repair buffer uses "STBL0"
    // (5 bytes). Prepend that when missing; never clobber the live ptr buffer.
    std::uint32_t wrote = static_cast<std::uint32_t>(out.size());
    if (out.size() >= 5 && std::memcmp(out.data(), "STBL0", 5) != 0) {
        if (dest + 5u + out.size() <= kRamSize) {
            std::memcpy(g_ram + dest, "STBL0", 5);
            std::memcpy(g_ram + dest + 5u, out.data(), out.size());
            wrote = static_cast<std::uint32_t>(out.size() + 5u);
        } else {
            std::memcpy(g_ram + dest, out.data(), out.size());
        }
    } else {
        std::memcpy(g_ram + dest, out.data(), out.size());
    }
    watch_span(dest, wrote, "igfileio:gob-extract");
    // Do NOT memcpy full STBL0 over the live ptr buffer — that overflows the
    // 65541B repair allocation and jalr's null (ra 0x239E98).
    // Full file planted. Keep walk flag set. Leave cur at first (not 7FFF) so
    // post-bind pump/guest can still observe a live walk; remain=0 signals the
    // bytes are already host-inflated. Do NOT poke ready@+96.
    std::uint32_t first = 0;
    std::memcpy(&first, g_ram + 0x006F5B24u, 4);
    const std::uint32_t zero = 0;
    if (first) std::memcpy(g_ram + 0x006F5B28u, &first, 4); // cur = first (not exhausted)
    std::memcpy(g_ram + 0x006F5B34u, &zero, 4);             // remain
    std::memcpy(g_ram + 0x006F5AC0u, &wrote, 4);
    g_host_fonts_extracted = true;
    s_done = true;
    std::fprintf(stderr, "[igfileio] gob-extract CRC=0x%08X -> 0x%X (%zu bytes, %s)\n", crc, dest, out.size(),
                 where);
    // Wake delay / gate / main waiters so guest can observe remain==0.
    std::uint32_t s45 = 0, s47 = 0;
    std::memcpy(&s45, g_ram + 0x00705C18u, 4);
    std::memcpy(&s47, g_ram + 0x00705C10u, 4);
    for (int id : {2, static_cast<int>(s47), 47, 50})
        if (id > 0 && id < 256) ps2::kernel::host_signal_sema(id);
    if (s45 > 0 && s45 < 256) ps2::kernel::host_signal_sema(static_cast<int>(s45));
    // Post into the prio-0 queue at 0x707868 (see consumer 0x43D7E0 / producer
    // 0x43D990): write_idx @+4, type @ base+8+widx*2, payload @ base+9+widx*2.
    // Producer uses type=0; type=1 takes the alternate handler path.
    if (0x00707868u + 0x400 <= kRamSize) {
        std::uint32_t widx = 0;
        std::memcpy(&widx, g_ram + 0x0070786Cu, 4);
        widx &= 0x1FFu;
        const std::uint32_t slot = 0x00707868u + (widx << 1);
        if (slot + 10 <= kRamSize) {
            g_ram[slot + 8] = 1; // type
            g_ram[slot + 9] = 0; // payload
            widx = (widx + 1u) & 0x1FFu;
            std::memcpy(g_ram + 0x0070786Cu, &widx, 4);
        }
        ps2::kernel::host_signal_sema(2);
        std::fprintf(stderr, "[igfileio] posted sema2 queue type=1 widx=%u\n", widx);
    }
    // Walker exhaust 0x242000 host-call hangs — leave behind PS2_ALCHEMY_EXHAUST.
    if (std::getenv("PS2_ALCHEMY_EXHAUST")) {
        const std::uint32_t gp = 0x006F9BF0u;
        std::fprintf(stderr, "[igfileio] host-call walker exhaust 0x242000\n");
        const std::uint32_t rc = ps2::kernel::host_call(0x00242000u, 0x7FFFu, gp);
        std::fprintf(stderr, "[igfileio] walker exhaust returned 0x%X\n", rc);
    }
    return true;
}

bool try_host_copy_stbl0_to_dest() {
    // Legacy env-gated path — prefer try_host_step_gob_cluster.
    return try_host_step_gob_cluster();
}

int inflate_loose_stblz_scratch() {
    // CNK parks additional STBLz clusters outside the fonts slot (observed at
    // 0x787000+). Inflate those in place to STBL0 when the payload fits so the
    // guest memcpy fast-path can run without EE zlib.
    if (!ensure_index()) return 0;
    static std::uint32_t s_last = 0;
    int n = 0;
    constexpr std::uint32_t kBegin = 0x00760000u, kEnd = 0x007A0000u;
    for (std::uint32_t a = kBegin; a + 64 < kEnd; a += 0x800u) {
        if (std::memcmp(g_ram + a, "STBLz", 5) != 0) continue;
        if (a == s_last) continue;
        // Guess compressed size from next STBL or page boundary.
        std::uint32_t csize = 0x800u;
        for (std::uint32_t b = a + 0x200u; b < a + 0x12000u && b + 5 < kEnd; b += 0x200u) {
            if (std::memcmp(g_ram + b, "STBL", 4) == 0) {
                csize = b - a;
                break;
            }
            csize = b - a + 0x200u;
        }
        if (csize < 16 || a + csize > kRamSize) continue;
        std::vector<std::uint8_t> inflated;
        if (!inflate_cluster(g_ram + a, csize, inflated)) continue;
        if (5u + inflated.size() > csize && a + 5u + inflated.size() > kEnd) continue;
        // Only rewrite when inflated fits in the same scratch window.
        if (5u + inflated.size() <= std::max(csize, 0x10000u) && a + 5u + inflated.size() <= kRamSize) {
            std::memcpy(g_ram + a, "STBL0", 5);
            std::memcpy(g_ram + a + 5, inflated.data(), inflated.size());
            watch_span(a, 5u + static_cast<std::uint32_t>(inflated.size()), "igfileio:loose-stbl0");
            std::fprintf(stderr, "[igfileio] loose STBLz->STBL0 @0x%X (%zu bytes)\n", a, inflated.size());
            s_last = a;
            ++n;
            if (n >= 2) break; // at most two per service tick
        }
    }
    return n;
}

bool service_pending_stblz() {
    // Defer STBL0 plant until the FINISH gate has started (ctr>200). Planting
    // during early module load races object construction (null vtable calls).
    std::uint32_t gate_ctr = 0;
    std::memcpy(&gate_ctr, g_ram + 0x00705C00u, 4);
    // EARLY restoration: restore obj+0x20 before anything else runs, so we have
    // the best chance of catching it before vt+108 runs with +20=0. This runs
    // on every service tick, not just when polling for parse completion.
    if (g_butanim_soft_obj && g_butanim_soft_o20 && !g_ui_igb_parse_attempted) {
        try_restore_butanim_o20();
    }
    const bool repaired = (gate_ctr > 200u) && try_repair_first_cluster();
    // Loose STBLz→STBL0 guess-sizing corrupts neighbors → jalr 0 (ra 0x12D8F4).
    if (gate_ctr > 200u && std::getenv("PS2_ALCHEMY_LOOSE")) inflate_loose_stblz_scratch();
    rearm_alchemy_timer_intc();
    // FINISH gap>=3 with STBL armed is a proven deadlock (ctr+3 forever). Pull
    // the target back by default — that only SignalSemas the gate waiter.
    static int s_wait = 0;
    if (repaired) s_wait = 0;
    kick_finish_gate_once(); // has its own deep-gap sticky counter
    // Drain Alchemy TIM0 delay IRQs every service tick once STBL is planted.
    kick_alchemy_tim0_irq();
    kick_alchemy_tim0_complete();
    if (++s_wait >= 8) {
        // Keep TIM0 armed (count+8, no reset-on-compare).
        hw::timer_arm_compare_pulse(0);
        // 0x427470 WaitSemas the timer-lock at 0x705F18 before arming TIM0 —
        // pulse that lock so arming can proceed. Delay-sema pulse (47/50) only
        // when FINISH gate gap<=1 — never sema 45 (FINISH gate).
        kick_alchemy_timer_lock();
        kick_alchemy_delay_semas();
        // Retarget dest; enable font tick; optional extract/walk behind env.
        // NEVER poke ready@+96=1 here — that means "destroy loaders" and frees
        // scratch into the 0x239A80 freelist hang.
        prepare_guest_walker_dest();
        try_kick_alchemy_font_tick();
        // Pump trampoline needs a channel index in a1 — leave behind WALK env.
        if (std::getenv("PS2_ALCHEMY_WALK")) try_host_call_alchemy_walker();
        // Soft extract + cur=7FFF; freelist-escape handles scratch frees.
        if (!std::getenv("PS2_ALCHEMY_NO_EXTRACT")) try_host_step_gob_cluster();
        // Staged font bind (lookups + 0x23EEF0). Safe with VEH; opt out via
        // PS2_ALCHEMY_NO_BIND. Full 0x10F2F0 AVs — staged path does not.
        if (g_host_fonts_extracted && !std::getenv("PS2_ALCHEMY_NO_BIND")) {
            static bool s_bind_queued = false;
            if (!s_bind_queued && !g_deferred_font_bind) {
                std::uint32_t lg = 0, dest = 0;
                std::memcpy(&lg, g_ram + 0x006F2540u, 4);
                std::memcpy(&dest, g_ram + 0x006F5AB8u, 4);
                if (lg && lg < kRamSize && dest && dest < kRamSize) {
                    s_bind_queued = true;
                    g_deferred_font_bind = true;
                    std::fprintf(stderr, "[igfileio] queued deferred font-bind lg=0x%X dest=0x%X\n", lg, dest);
                }
            }
        }
        // ready@+96 tears down loaders (0x109C28). Without a successful bind
        // that jalr's null (ra 0x506648). Only release when igctx is live, or
        // when PS2_ALCHEMY_READY is set explicitly.
        if (g_host_fonts_extracted && !std::getenv("PS2_ALCHEMY_NO_READY")) {
            std::uint32_t ctx = 0;
            std::memcpy(&ctx, g_ram + 0x007430C0u, 4);
            if (ctx != 0 || std::getenv("PS2_ALCHEMY_READY")) {
                static bool s_ready = false;
                if (!s_ready) {
                    std::uint32_t dest = 0;
                    std::memcpy(&dest, g_ram + 0x006F5AB8u, 4);
                    if (dest >= 0x01A00000u && dest < 0x01C00000u) {
                        const std::uint32_t zero = 0;
                        std::memcpy(g_ram + 0x006F5AB8u, &zero, 4);
                        for (std::uint32_t off : {23240u, 23248u, 23256u, 23224u, 23232u}) {
                            std::uint32_t v = 0;
                            std::memcpy(&v, g_ram + 0x006F0000u + off, 4);
                            if (v >= 0x01A00000u && v < 0x01C00000u)
                                std::memcpy(g_ram + 0x006F0000u + off, &zero, 4);
                        }
                        if (0x006F5B20u < kRamSize) g_ram[0x006F5B20u] = 0;
                        std::fprintf(stderr, "[igfileio] nulled scratch dest was 0x%X before ready\n", dest);
                    }
                    std::uint32_t obj = 0;
                    std::memcpy(&obj, g_ram + 0x006F35B8u, 4);
                    if (obj && obj + 100u <= kRamSize) {
                        std::uint32_t ready = 0;
                        std::memcpy(&ready, g_ram + obj + 96u, 4);
                        if (ready != 1u) {
                            const std::uint32_t one = 1u;
                            std::memcpy(g_ram + obj + 96u, &one, 4);
                            std::fprintf(stderr, "[igfileio] ready-release obj=0x%X %u→1 (igctx=0x%X)\n",
                                         obj, ready, ctx);
                        }
                        s_ready = true;
                    }
                }
            }
        }
        if (std::getenv("PS2_ALCHEMY_EC00")) {
            static bool s_ec = false;
            if (!s_ec && g_host_fonts_extracted) {
                s_ec = true;
                const std::uint32_t gp = 0x006F9BF0u;
                std::fprintf(stderr, "[igfileio] host-call 0x23EC00(a0=0x6F59F0)\n");
                const std::uint32_t rc = ps2::kernel::host_call(0x0023EC00u, 0x006F59F0u, gp);
                std::fprintf(stderr, "[igfileio] 0x23EC00 returned 0x%X\n", rc);
            }
        }
        s_wait = 0;
    }
    return repaired;
}

bool alchemy_asset_pending() { return alchemy_stbl_pending(); }

#if defined(_WIN32)
thread_local std::jmp_buf g_bind_jmp;
thread_local bool g_bind_veh_armed = false;
LONG CALLBACK alchemy_bind_veh(EXCEPTION_POINTERS *ep) {
    if (!g_bind_veh_armed) return EXCEPTION_CONTINUE_SEARCH;
    const DWORD code = ep->ExceptionRecord->ExceptionCode;
    if (code != EXCEPTION_ACCESS_VIOLATION && code != EXCEPTION_ILLEGAL_INSTRUCTION)
        return EXCEPTION_CONTINUE_SEARCH;
    g_bind_veh_armed = false;
    std::longjmp(g_bind_jmp, 1);
    return EXCEPTION_CONTINUE_SEARCH;
}
#endif

bool poll_deferred_work() {
    if (!g_deferred_font_bind) return false;
    g_deferred_font_bind = false;
    std::uint32_t lg = 0, dest = 0;
    std::memcpy(&lg, g_ram + 0x006F2540u, 4);
    std::memcpy(&dest, g_ram + 0x006F5AB8u, 4);
    if (!lg || lg >= kRamSize || !dest || dest >= kRamSize) return false;
    const std::uint32_t gp = 0x006F9BF0u;
    // Stage 0x10F2F0: three 0x23D7B0 lookups then 0x23EEF0 binder.
    std::uint32_t slot = 0;
    std::memcpy(&slot, g_ram + lg + 4u, 4);
    const std::uint8_t walk_en = (0x006F2084u < kRamSize) ? g_ram[0x006F2084u] : 0;
    std::fprintf(stderr, "[igfileio] staged bind lg=0x%X slot=0x%X dest=0x%X walk_en=%u\n", lg, slot, dest, walk_en);
    std::fflush(stderr);
    std::uint32_t rc = 0;
    auto guarded = [&](auto &&fn) -> std::uint32_t {
#if defined(_WIN32)
        PVOID veh = AddVectoredExceptionHandler(1, alchemy_bind_veh);
        g_bind_veh_armed = true;
        std::uint32_t out = 0;
        if (setjmp(g_bind_jmp) == 0) {
            out = fn();
            g_bind_veh_armed = false;
        } else {
            std::fprintf(stderr, "[igfileio] staged bind ACCESS_VIOLATION\n");
            ps2::kernel::host_call_cleanup();
            out = 0;
        }
        if (veh) RemoveVectoredExceptionHandler(veh);
        return out;
#else
        return fn();
#endif
    };
    // 0x23D7B0 walks slot+4 count, names at slot+8+4*i, objs at slot+32+4*i.
    // Retail CNK only registers cd+gob (count=2). Binder also looks up "host"
    // at 0x611A98 — forge a third entry by cloning cd so the lookup hits.
    if (slot + 44u < kRamSize && !std::getenv("PS2_ALCHEMY_NO_HOST_FORGE")) {
        std::uint32_t count = 0, cd = 0;
        std::memcpy(&count, g_ram + slot + 4u, 4);
        std::memcpy(&cd, g_ram + slot + 32u, 4);
        if (count == 2u && cd && cd + 64u < kRamSize) {
            constexpr std::uint32_t kHostObj = 0x01BFFC00u; // high scratch, 64B
            std::memcpy(g_ram + kHostObj, g_ram + cd, 64);
            // Name pointer: reuse the literal "host" already in .rodata.
            const std::uint32_t host_name = 0x00611A98u;
            std::memcpy(g_ram + slot + 16u, &host_name, 4);
            std::memcpy(g_ram + slot + 40u, &kHostObj, 4);
            count = 3;
            std::memcpy(g_ram + slot + 4u, &count, 4);
            std::fprintf(stderr, "[igfileio] forged host provider obj=0x%X (cloned cd 0x%X)\n", kHostObj, cd);
        }
    }
    const std::uint32_t r18 = guarded([&] {
        return ps2::kernel::host_call(0x0023D7B0u, slot, gp, 200000u, 0x00611AD0u);
    });
    std::fprintf(stderr, "[igfileio] lookup0 0x23D7B0 -> 0x%X\n", r18);
    if (!r18) return true;
    const std::uint32_t r20 = guarded([&] {
        return ps2::kernel::host_call(0x0023D7B0u, slot, gp, 200000u, 0x00611AA8u);
    });
    std::fprintf(stderr, "[igfileio] lookup1 0x23D7B0(+6824) -> 0x%X\n", r20);
    std::uint32_t r10 = guarded([&] {
        return ps2::kernel::host_call(0x0023D7B0u, slot, gp, 200000u, 0x00611A98u);
    });
    std::fprintf(stderr, "[igfileio] lookup2 0x23D7B0(+6808) -> 0x%X\n", r10);
    if (!r10) {
        r10 = r20 ? r20 : r18;
        std::fprintf(stderr, "[igfileio] host lookup still miss; alias t2=0x%X\n", r10);
    }
    if (std::getenv("PS2_ALCHEMY_BIND_PROBE_ONLY")) {
        std::fprintf(stderr, "[igfileio] probe-only; skip 0x23EEF0\n");
        return true;
    }
    // Keep walk_en as-is: walk_en=1 → F0BC attach (gob+912=1). Clearing it
    // made 0x240350 wipe gob+912 and zero the fonts dest pointer (ptr=0).
    // Do NOT retarget ptr to extract scratch — scratch head is raw GOB bytes,
    // STBL0 lives at the repair buffer (0x762390).
    std::uint8_t flag_before = (r18 + 1428u < kRamSize) ? g_ram[r18 + 1428u] : 0;
    // 0x23EEF0(a0=r18, a1=0x611AD8, a2=r20, a3=0, t0=0, t1=gp-32468, t2=r10)
    const std::uint32_t t1 = gp - 32468u;
    rc = guarded([&] {
        return ps2::kernel::host_call_t(0x0023EEF0u, r18, 0x00611AD8u, r20, 0, 0, t1, r10, gp, 5000000u);
    });
    std::uint8_t flag_after = (r18 + 1428u < kRamSize) ? g_ram[r18 + 1428u] : 0;
    std::uint32_t ctx = 0, alloc = 0, gob912 = 0;
    std::memcpy(&ctx, g_ram + 0x007430C0u, 4);
    std::memcpy(&alloc, g_ram + 0x006F0000u + 22992u, 4);
    if (r18 + 916u <= kRamSize) std::memcpy(&gob912, g_ram + r18 + 912u, 4);
    std::fprintf(stderr,
                 "[igfileio] staged 0x23EEF0 returned 0x%X igctx=0x%X alloc=0x%X gob+1428 %u→%u gob+912=0x%X\n",
                 rc, ctx, alloc, flag_before, flag_after, gob912);
    // F0BC (walk_en=1 → 0x2422E0 returns 6) already ran jump_table[6] and set
    // gob+912=1, then returned 0. Calling 0x240350 afterwards re-enters 0x243E40
    // with a stale +23880 and CLEARS gob+912 — undo that mistake. Only run
    // 0x240350 when binder did NOT leave a live attach status.
    const bool f0bc_attached = (gob912 == 1u);
    if (!flag_after && r18 + 1428u < kRamSize) {
        g_ram[r18 + 1428u] = 1;
        flag_after = 1;
        std::fprintf(stderr, "[igfileio] set gob+1428 for post-bind\n");
    }
    if (r18) {
        std::uint32_t meta = 0;
        std::memcpy(&meta, g_ram + r18 + 4u, 4);
        std::uint32_t fn172 = 0;
        if (meta && meta + 176u < kRamSize) std::memcpy(&fn172, g_ram + meta + 172u, 4);
        std::fprintf(stderr, "[igfileio] post-bind meta=0x%X fn172=0x%X f0bc=%d\n", meta, fn172,
                     f0bc_attached ? 1 : 0);
        if (fn172) {
            const std::uint32_t pr = guarded([&] {
                return ps2::kernel::host_call(fn172, r18, gp, 2000000u, 0x00611AC0u);
            });
            std::fprintf(stderr, "[igfileio] post-bind meta+172 -> 0x%X\n", pr);
        }
        if (!f0bc_attached) {
            // F118-style path: 0x240350(gob,1) drives 0x243E40 → 0x2403C0.
            if (0x006F2084u < kRamSize) g_ram[0x006F2084u] = 0;
            const std::uint32_t p350 = guarded([&] {
                return ps2::kernel::host_call(0x00240350u, r18, gp, 2000000u, 1u);
            });
            std::fprintf(stderr, "[igfileio] post-bind 0x240350 -> 0x%X\n", p350);
        } else {
            // F0BC attach stuck gob+912=1; 0x240350 / F0F4 drive clobber it.
            std::fprintf(stderr, "[igfileio] skip 0x240350 (F0bc gob+912=1)\n");
        }
        const std::uint32_t p920 = guarded([&] {
            return ps2::kernel::host_call(0x0023D920u, slot, gp, 2000000u, 0u, 0x00611AD0u);
        });
        std::fprintf(stderr, "[igfileio] post-bind 0x23D920 -> 0x%X\n", p920);
        // Pump once. meta+8 (0x23ED50) jalr's null (ra 0x23ED9C) — skip.
        const std::uint32_t pump = guarded([&] {
            return ps2::kernel::host_call(0x0023ED40u, 0, gp, 2000000u);
        });
        std::fprintf(stderr, "[igfileio] post-bind pump 0x23ED40 -> 0x%X\n", pump);
        // Font-tick work path 0x10FA10 (taken when +24016 clear). Drive it once
        // now that gob attach stuck.
        if (lg && lg + 24025u < kRamSize) {
            g_ram[lg + 24016u] = 0;
            const std::uint32_t tick = guarded([&] {
                return ps2::kernel::host_call(0x0010FA10u, lg, gp, 2000000u);
            });
            std::fprintf(stderr, "[igfileio] post-bind tick 0x10FA10 -> 0x%X\n", tick);
        }
        std::memcpy(&ctx, g_ram + 0x007430C0u, 4);
        if (r18 + 916u <= kRamSize) std::memcpy(&gob912, g_ram + r18 + 912u, 4);
        std::fprintf(stderr, "[igfileio] post-bind done igctx=0x%X gob+912=0x%X\n", ctx, gob912);
        // ready@+96: with F0BC attach (gob+912=1) + freelist-escape, try once.
        // Opt out via PS2_ALCHEMY_NO_READY. Force earlier via PS2_ALCHEMY_READY.
        if ((f0bc_attached || gob912 == 1u) && !std::getenv("PS2_ALCHEMY_NO_READY")) {
            static bool s_ready_bind = false;
            if (!s_ready_bind) {
                std::uint32_t obj = 0;
                std::memcpy(&obj, g_ram + 0x006F2540u, 4);
                if (obj && obj + 100u < kRamSize && g_ram[obj + 96u] == 0) {
                    g_ram[obj + 96u] = 1;
                    s_ready_bind = true;
                    std::fprintf(stderr, "[igfileio] ready-release after F0BC attach obj=0x%X\n", obj);
                }
            }
        }
    }
    return true;
}

bool ui_igb_parse_attempted() {
    poll_butanim_parse_complete();
    return g_ui_igb_parse_attempted;
}

void note_ui_igb_soft_arm(std::uint32_t obj, bool butanim) {
    // Virt-GFC / Alchemy soft-arm only. Ignore empty or OOB objects.
    if (!butanim || !obj || obj + 0x100u > kRamSize) return;
    if (!g_butanim_soft_obj) {
        g_butanim_soft_obj = obj;
        // Drop stale completion so intro hold cannot release on recycled +0xFF.
        g_ram[obj + 0xffu] = 0;
        g_butanim_saw_ff_clear = true;
        g_ui_igb_parse_attempted = false;
        g_butanim_parsed_ok = false;
        g_butanim_o20_restore_count = 0;
        std::uint32_t o14 = 0, o20 = 0, o8 = 0;
        std::memcpy(&o8, g_ram + obj + 8u, 4);
        std::memcpy(&o14, g_ram + obj + 0x14u, 4);
        std::memcpy(&o20, g_ram + obj + 0x20u, 4);
        // Capture +0x14/+0x20 for restoration. vt+108's 0x51C100 ingest path
        // requires *(obj+0x20)+0x24≠0; something clears +0x20 before guest
        // FCE0/vt+108 runs. We restore it so the ingest sticks and prims >> 2.
        g_butanim_soft_o14 = o14;
        g_butanim_soft_o20 = o20;
        std::fprintf(stderr,
                     "[igfileio] noted butanim soft-arm obj=0x%X (cleared +0xFF) +8=%u +14=0x%X +20=0x%X "
                     "assemble_butanim=%d\n",
                     obj, o8, o14, o20, assemble_holds_butanim() ? 1 : 0);
    }
}

void note_butanim_plant_size(std::uint32_t nbytes) {
    if (nbytes >= 0x100u && nbytes <= 0x10000u) g_butanim_plant_size = nbytes;
}

void reset() {
    g_index = {};
    g_open.clear();
    g_pos.clear();
    g_next_fd = 1;
    g_stblz_last_key = 0;
    g_host_fonts_extracted = false;
    g_deferred_font_bind = false;
    g_ui_igb_parse_attempted = false;
    g_butanim_soft_obj = 0;
    g_butanim_plant_size = 0;
    g_butanim_soft_o14 = 0;
    g_butanim_soft_o20 = 0;
    g_butanim_saw_ff_clear = false;
    g_butanim_parsed_ok = false;
    g_butanim_o20_restore_count = 0;
}

bool handle(std::uint32_t method, std::uint32_t args, std::uint32_t size, std::uint32_t ret, std::uint32_t ret_size) {
    const auto word = [&](unsigned i) { return word_at(args, size, i); };
    if (g_options.trace_iop_modules) {
        std::fprintf(stderr, "[igfileio] method %u args 0x%X size %u ret 0x%X/%u", method, args, size, ret, ret_size);
        for (unsigned i = 0; i < std::min(size / 4u, 8u); ++i) std::fprintf(stderr, " %08X", word(i));
        std::fprintf(stderr, "\n");
    }

    // Method 19: Alchemy FileIO driver init/register ("…ileIO.irx").
    // Guest passes EE ctx base (CNK: 0x7430C0) — that is the FileIO object,
    // NOT a scene igctx pointer. Do NOT seed it: writing a fake header caused
    // jalr-null (ra 0x506648) and skipped staged bind. Keep a cheap ack;
    // index loads lazily on first open/read.
    if (method == 19) {
        std::fprintf(stderr, "[igfileio] init ctx=0x%X (lazy index)\n", word(0));
        store_ret(ret, ret_size, 0, 0);
        return true;
    }

    // Common FILEIO-shaped methods used by Alchemy wrappers (open/close/read/seek/size).
    if (method == 0 || method == 2) { // open / open2
        std::string path = name_from_words(args, size, 1);
        if (path.empty()) {
            const std::uint32_t p = word(0);
            if (p > 0x1000 && p < kRamSize) path = reinterpret_cast<const char *>(g_ram + (p & (kRamSize - 1)));
        }
        int fd = -1;
        const bool ok = !path.empty() && open_asset(path, fd);
        if (g_options.trace_iop_modules)
            std::fprintf(stderr, "[igfileio] open \"%s\" -> %d\n", path.c_str(), ok ? fd : -1);
        store_ret(ret, ret_size, ok ? static_cast<std::uint32_t>(fd) : static_cast<std::uint32_t>(-1));
        return true;
    }
    if (method == 1) { // close
        const int fd = static_cast<int>(word(0));
        g_open.erase(fd);
        g_pos.erase(fd);
        store_ret(ret, ret_size, 0);
        return true;
    }
    if (method == 3 || method == 4) { // read
        const int fd = static_cast<int>(word(0));
        const std::uint32_t dst = word(1);
        const std::uint32_t want = word(2);
        auto it = g_open.find(fd);
        if (it == g_open.end()) {
            store_ret(ret, ret_size, static_cast<std::uint32_t>(-1));
            return true;
        }
        auto &pos = g_pos[fd];
        const std::uint32_t n = std::min(want, static_cast<std::uint32_t>(it->second.size() - std::min<std::size_t>(pos, it->second.size())));
        if (n && dst < kRamSize) {
            std::memcpy(g_ram + (dst & (kRamSize - 1)), it->second.data() + pos, n);
            watch_span(dst, n, "igfileio:read");
            pos += n;
        }
        store_ret(ret, ret_size, n);
        return true;
    }
    if (method == 5) { // seek
        const int fd = static_cast<int>(word(0));
        const std::int32_t off = static_cast<std::int32_t>(word(1));
        const int whence = static_cast<int>(word(2));
        auto it = g_open.find(fd);
        if (it == g_open.end()) {
            store_ret(ret, ret_size, static_cast<std::uint32_t>(-1));
            return true;
        }
        std::int64_t pos = g_pos[fd];
        if (whence == 0) pos = off;
        else if (whence == 1) pos += off;
        else if (whence == 2) pos = static_cast<std::int64_t>(it->second.size()) + off;
        if (pos < 0) pos = 0;
        if (pos > static_cast<std::int64_t>(it->second.size())) pos = static_cast<std::int64_t>(it->second.size());
        g_pos[fd] = static_cast<std::uint32_t>(pos);
        store_ret(ret, ret_size, static_cast<std::uint32_t>(pos));
        return true;
    }
    if (method == 6) { // size
        const int fd = static_cast<int>(word(0));
        auto it = g_open.find(fd);
        store_ret(ret, ret_size, it == g_open.end() ? 0u : static_cast<std::uint32_t>(it->second.size()));
        return true;
    }

    // Unknown method: succeed with zeros so CallRpc does not hang WaitSema.
    store_ret(ret, ret_size, 0, 0);
    return true;
}

}
