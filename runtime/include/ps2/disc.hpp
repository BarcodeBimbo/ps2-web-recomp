#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace ps2::disc {

inline constexpr std::uint32_t kSector = 2048;

struct Entry {
    std::uint32_t sector;
    std::uint32_t size;
    bool directory;
};

using Reader = std::function<std::size_t(std::uint64_t offset, void *out, std::size_t size)>;
using Probe = std::function<bool(std::uint64_t offset, std::size_t size)>;

bool open(const std::string &path);
bool open(const std::string &name, std::uint64_t size, Reader reader, Probe probe = {});
bool is_open();
bool read(std::uint32_t sector, std::uint32_t count, void *out);
bool ready(std::uint32_t sector, std::uint32_t count);
std::optional<Entry> find(const std::string &path);
// Mount host bytes as a virtual ISO file (high LBA). Used when Alchemy assets
// live in GFC/GOB but the guest probes them via sceCdSearchFile.
std::optional<Entry> mount_memory(const std::string &path, std::vector<std::uint8_t> data);
// Resolve a virtual (GFC-mounted) LBA back to its host bytes / path / base LBA.
bool virtual_payload(std::uint32_t sector, std::string *path = nullptr, std::vector<std::uint8_t> *bytes = nullptr,
                     std::uint32_t *base_out = nullptr);
std::uint32_t layer1_start();
std::uint64_t sector_count();

}
