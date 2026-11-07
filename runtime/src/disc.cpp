#include "ps2/disc.hpp"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <map>
#include <set>
#include <vector>

namespace ps2::disc {

namespace {

std::FILE *g_file = nullptr;
Reader g_reader;
Probe g_probe;
std::uint64_t g_size = 0;
std::uint32_t g_layer1 = 0;
std::map<std::string, Entry> g_index;
std::set<std::uint64_t> g_directories;
std::map<std::uint32_t, std::vector<std::uint8_t>> g_virtual; // base LBA → sector-padded bytes
std::map<std::uint32_t, std::string> g_virtual_path;           // base LBA → path key
std::uint32_t g_virt_lba = 0;
constexpr std::uint32_t kVirtBase = 0xF0000000u;

std::uint32_t u32(const std::uint8_t *p) {
    std::uint32_t v;
    std::memcpy(&v, p, 4);
    return v;
}

std::string upper(std::string s) {
    for (char &c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

void walk(std::uint32_t base, std::uint32_t lba, std::uint32_t size, const std::string &prefix, int depth) {
    const std::uint64_t sector = std::uint64_t(base) + lba;
    if (depth > 16 || size > (32u << 20) || sector * kSector + size > g_size ||
        g_index.size() >= 100000 || !g_directories.insert(sector).second) return;
    std::vector<std::uint8_t> data((size + kSector - 1) / kSector * kSector);
    if (!read(base + lba, static_cast<std::uint32_t>(data.size() / kSector), data.data())) return;
    std::size_t off = 0;
    while (off < size) {
        const std::uint8_t length = data[off];
        if (!length) {
            off = (off / kSector + 1) * kSector;
            continue;
        }
        if (length < 34 || length > size - off) return;
        const std::uint8_t *rec = &data[off];
        if (33u + rec[32] > length) return;
        off += length;
        const std::uint8_t name_len = rec[32];
        std::string name(reinterpret_cast<const char *>(rec + 33), name_len);
        if (name_len == 1 && (name[0] == 0 || name[0] == 1)) continue;
        const auto semi = name.find(';');
        if (semi != std::string::npos) name = name.substr(0, semi);
        const std::string path = prefix + upper(name);
        const bool dir = rec[25] & 2;
        const Entry entry{base + u32(rec + 2), u32(rec + 10), dir};
        if ((std::uint64_t(base) + u32(rec + 2)) * kSector + entry.size > g_size) return;
        g_index[path] = entry;
        if (dir) walk(base, u32(rec + 2), u32(rec + 10), path + "/", depth + 1);
    }
}

void index_layer(std::uint32_t pvd_sector, std::uint32_t base) {
    std::uint8_t pvd[kSector];
    if (!read(pvd_sector, 1, pvd) || std::memcmp(pvd, "\x01" "CD001", 6) != 0) return;
    walk(base, u32(pvd + 158), u32(pvd + 166), "", 0);
}

}

bool open(const std::string &path) {
    g_file = std::fopen(path.c_str(), "rb");
    if (!g_file) return false;
#if defined(_WIN32)
    _fseeki64(g_file, 0, SEEK_END);
    const std::uint64_t size = static_cast<std::uint64_t>(_ftelli64(g_file));
#else
    fseeko(g_file, 0, SEEK_END);
    const std::uint64_t size = static_cast<std::uint64_t>(ftello(g_file));
#endif
    std::FILE *file = g_file;
    return open(path, size, [file](std::uint64_t offset, void *out, std::size_t bytes) {
#if defined(_WIN32)
        _fseeki64(file, static_cast<long long>(offset), SEEK_SET);
#else
        fseeko(file, static_cast<off_t>(offset), SEEK_SET);
#endif
        return std::fread(out, 1, bytes, file);
    });
}

bool open(const std::string &name, std::uint64_t size, Reader reader, Probe probe) {
    g_reader = std::move(reader);
    g_probe = std::move(probe);
    g_size = size;
    g_index.clear();
    g_directories.clear();
    g_virtual.clear();
    g_virtual_path.clear();
    g_virt_lba = 0;
    g_layer1 = 0;
    index_layer(16, 0);
    std::uint8_t pvd[kSector]{};
    if (!read(16, 1, pvd) || std::memcmp(pvd, "\x01" "CD001", 6) != 0) { g_reader = {}; return false; }
    const std::uint32_t layer0 = u32(pvd + 80);
    for (std::uint32_t s = layer0; std::uint64_t(s) < std::uint64_t(layer0) + 64 && static_cast<std::uint64_t>(s) * kSector < g_size; ++s) {
        std::uint8_t probe[kSector];
        if (read(s, 1, probe) && std::memcmp(probe, "\x01" "CD001", 6) == 0) {
            g_layer1 = s - 16;
            index_layer(s, g_layer1);
            break;
        }
    }
    std::fprintf(stderr, "[disc] %s: %zu files, %llu sectors, layer 1 at %u\n", name.c_str(), g_index.size(),
                 static_cast<unsigned long long>(g_size / kSector), g_layer1);
    return true;
}

bool is_open() { return static_cast<bool>(g_reader); }

bool read(std::uint32_t sector, std::uint32_t count, void *out) {
    auto *dst = static_cast<std::uint8_t *>(out);
    const std::size_t want = static_cast<std::size_t>(count) * kSector;
    if (sector >= kVirtBase) {
        for (const auto &[base, bytes] : g_virtual) {
            const std::uint32_t nsec = static_cast<std::uint32_t>((bytes.size() + kSector - 1) / kSector);
            if (sector < base || sector >= base + nsec) continue;
            std::memset(dst, 0, want);
            const std::size_t off = static_cast<std::size_t>(sector - base) * kSector;
            const std::size_t n = std::min(want, bytes.size() > off ? bytes.size() - off : 0);
            if (n) std::memcpy(dst, bytes.data() + off, n);
            static int s_vr = 0;
            if (s_vr < 12) {
                std::fprintf(stderr, "[disc] virtual read lba=0x%X count=%u off=%zu n=%zu\n", sector, count, off,
                             n);
                ++s_vr;
            }
            return true;
        }
        static int s_miss = 0;
        if (s_miss < 6) {
            std::fprintf(stderr, "[disc] virtual read MISS lba=0x%X count=%u\n", sector, count);
            ++s_miss;
        }
        std::memset(dst, 0, want);
        return count == 0;
    }
    if (!g_reader) return false;
    const std::size_t got = g_reader(static_cast<std::uint64_t>(sector) * kSector, out, want);
    if (got < want) std::memset(dst + got, 0, want - got);
    return got > 0 || !count;
}

bool ready(std::uint32_t sector, std::uint32_t count) {
    if (sector >= kVirtBase) return true;
    return !g_probe || g_probe(static_cast<std::uint64_t>(sector) * kSector, static_cast<std::size_t>(count) * kSector);
}

std::optional<Entry> find(const std::string &raw) {
    std::string path = raw;
    const auto colon = path.find(':');
    if (colon != std::string::npos) path = path.substr(colon + 1);
    std::replace(path.begin(), path.end(), '\\', '/');
    const auto semi = path.find(';');
    if (semi != std::string::npos) path = path.substr(0, semi);
    while (!path.empty() && path.front() == '/') path.erase(path.begin());
    auto it = g_index.find(upper(path));
    if (it == g_index.end()) return std::nullopt;
    return it->second;
}

std::optional<Entry> mount_memory(const std::string &path, std::vector<std::uint8_t> data) {
    std::string key = path;
    const auto colon = key.find(':');
    if (colon != std::string::npos) key = key.substr(colon + 1);
    std::replace(key.begin(), key.end(), '\\', '/');
    const auto semi = key.find(';');
    if (semi != std::string::npos) key = key.substr(0, semi);
    while (!key.empty() && key.front() == '/') key.erase(key.begin());
    key = upper(key);
    if (auto it = g_index.find(key); it != g_index.end() && it->second.sector >= kVirtBase)
        return it->second;
    if (!g_virt_lba) g_virt_lba = kVirtBase;
    const std::uint32_t size = static_cast<std::uint32_t>(data.size());
    const std::uint32_t nsec = (size + kSector - 1) / kSector;
    if (!nsec) return std::nullopt;
    data.resize(static_cast<std::size_t>(nsec) * kSector, 0);
    const std::uint32_t base = g_virt_lba;
    g_virt_lba += nsec;
    std::fprintf(stderr, "[disc] virtual mount %s lba=0x%X size=%u head=", key.c_str(), base, size);
    for (std::size_t i = 0; i < std::min<std::size_t>(16, data.size()); ++i)
        std::fprintf(stderr, "%02X", data[i]);
    std::fprintf(stderr, "\n");
    g_virtual[base] = std::move(data);
    g_virtual_path[base] = key;
    Entry e{base, size, false};
    g_index[key] = e;
    return e;
}

bool virtual_payload(std::uint32_t sector, std::string *path, std::vector<std::uint8_t> *bytes,
                     std::uint32_t *base_out) {
    if (sector < kVirtBase) return false;
    for (const auto &[base, data] : g_virtual) {
        const std::uint32_t nsec = static_cast<std::uint32_t>((data.size() + kSector - 1) / kSector);
        if (sector < base || sector >= base + nsec) continue;
        if (base_out) *base_out = base;
        if (path) {
            auto it = g_virtual_path.find(base);
            *path = it != g_virtual_path.end() ? it->second : std::string{};
        }
        if (bytes) {
            auto it = g_virtual_path.find(base);
            std::uint32_t logical = static_cast<std::uint32_t>(data.size());
            if (it != g_virtual_path.end()) {
                if (auto e = find(it->second)) logical = e->size;
            }
            bytes->assign(data.begin(), data.begin() + std::min<std::size_t>(logical, data.size()));
        }
        return true;
    }
    return false;
}

std::uint32_t layer1_start() { return g_layer1; }
std::uint64_t sector_count() { return g_size / kSector; }

}
