#include "elf.hpp"

#include <cstring>
#include <algorithm>
#include <fstream>
#include <iterator>
#include <stdexcept>

namespace recomp {

namespace {

template <typename T>
T read(const std::vector<std::uint8_t> &data, std::size_t offset) {
    if (offset > data.size() || sizeof(T) > data.size() - offset) throw std::runtime_error("truncated ELF file");
    T value;
    std::memcpy(&value, data.data() + offset, sizeof(T));
    return value;
}

}

Image Image::load(const std::string &path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) throw std::runtime_error("cannot open " + path);
    file.seekg(0, std::ios::end);
    const auto length = file.tellg();
    if (length < 0 || length > (512ll << 20)) throw std::runtime_error("ELF exceeds input size limit");
    file.seekg(0);
    const std::vector<std::uint8_t> data{std::istreambuf_iterator<char>(file), {}};
    if (data.size() < 52 || std::memcmp(data.data(), "\x7f" "ELF\x01\x01", 6) != 0)
        throw std::runtime_error(path + " is not a little endian ELF32 file");

    Image image;
    image.entry_ = read<std::uint32_t>(data, 24);
    const auto phoff = read<std::uint32_t>(data, 28);
    const auto shoff = read<std::uint32_t>(data, 32);
    const auto phentsize = read<std::uint16_t>(data, 42), phnum = read<std::uint16_t>(data, 44);
    const auto shentsize = read<std::uint16_t>(data, 46), shnum = read<std::uint16_t>(data, 48);

    if ((phnum && phentsize < 32) || (shnum && shentsize < 40) ||
        std::uint64_t(phoff) + std::uint64_t(phnum) * phentsize > data.size() ||
        (shoff && std::uint64_t(shoff) + std::uint64_t(shnum) * shentsize > data.size()))
        throw std::runtime_error("invalid ELF header table");
    std::uint64_t allocated = 0;
    for (std::uint32_t i = 0; i < phnum; ++i) {
        const std::size_t ph = std::size_t(phoff) + std::size_t(i) * phentsize;
        if (read<std::uint32_t>(data, ph) != 1) continue;
        const auto offset = read<std::uint32_t>(data, ph + 4), vaddr = read<std::uint32_t>(data, ph + 8);
        const auto filesz = read<std::uint32_t>(data, ph + 16), memsz = read<std::uint32_t>(data, ph + 20);
        const auto flags = read<std::uint32_t>(data, ph + 24);
        if (std::uint64_t(offset) + filesz > data.size() || filesz > memsz ||
            std::uint64_t(vaddr) + memsz > 0x100000000ull)
            throw std::runtime_error("invalid ELF segment bounds");
        allocated += memsz;
        if (allocated > (256ull << 20)) throw std::runtime_error("ELF segments exceed memory limit");
        // An executable segment with no file contents is a code window: the
        // game rewrites it at runtime, so it holds no code to translate here
        // and any call into it walks to the images the game puts there.
        if (!filesz && (flags & 1u)) continue;
        Segment segment{vaddr, std::vector<std::uint8_t>(memsz), (flags & 1u) != 0, filesz};
        std::memcpy(segment.bytes.data(), data.data() + offset, filesz);
        image.segments_.push_back(std::move(segment));
    }

    std::uint64_t symbols_read = 0;
    const auto shstrndx = read<std::uint16_t>(data, 50);
    for (std::uint32_t i = 0; shoff && i < shnum; ++i) {
        const std::size_t sh = std::size_t(shoff) + std::size_t(i) * shentsize;
        if (read<std::uint32_t>(data, sh + 4) == 1 && shstrndx < shnum) {
            const std::size_t name = std::size_t(read<std::uint32_t>(data, std::size_t(shoff) + std::size_t(shstrndx) * shentsize + 16)) + read<std::uint32_t>(data, sh);
            if (name + 6 <= data.size() && std::memcmp(data.data() + name, ".text", 6) == 0) {
                const auto address = read<std::uint32_t>(data, sh + 12), size = read<std::uint32_t>(data, sh + 20);
                image.text_ = {address, address + size};
            }
        }
        if (read<std::uint32_t>(data, sh + 4) != 2) continue;
        const auto symoff = read<std::uint32_t>(data, sh + 16), symsize = read<std::uint32_t>(data, sh + 20);
        const auto link = read<std::uint32_t>(data, sh + 24);
        if (link >= shnum || std::uint64_t(symoff) + symsize > data.size() || symsize % 16)
            throw std::runtime_error("invalid ELF symbol table");
        symbols_read += symsize / 16;
        if (symbols_read > 1000000) throw std::runtime_error("ELF symbol count exceeds limit");
        const std::size_t strheader = std::size_t(shoff) + std::size_t(link) * shentsize;
        const auto stroff = read<std::uint32_t>(data, strheader + 16);
        const auto strsize = read<std::uint32_t>(data, strheader + 20);
        if (std::uint64_t(stroff) + strsize > data.size()) throw std::runtime_error("invalid ELF string table");
        for (std::size_t s = symoff; s < std::size_t(symoff) + symsize; s += 16) {
            const auto name = read<std::uint32_t>(data, s), value = read<std::uint32_t>(data, s + 4);
            if ((data[s + 12] & 15u) != 2u || !value) continue;
            if (name >= strsize) throw std::runtime_error("invalid ELF symbol name");
            const char *begin = reinterpret_cast<const char *>(data.data() + stroff + name);
            const char *end = static_cast<const char *>(std::memchr(begin, 0, std::min<std::size_t>(strsize - name, 65536)));
            if (!end) throw std::runtime_error("unterminated ELF symbol name");
            image.symbols_[value] = std::string(begin, end);
        }
    }
    return image;
}

Image Image::raw(std::uint32_t address, std::vector<std::uint8_t> bytes, std::pair<std::uint32_t, std::uint32_t> text) {
    Image image;
    const auto initialized_size = static_cast<std::uint32_t>(bytes.size());
    image.segments_.push_back(Segment{address, std::move(bytes), true, initialized_size});
    image.text_ = text;
    return image;
}

std::optional<std::uint32_t> Image::word(std::uint32_t address) const {
    for (const auto &segment : segments_) {
        if (address >= segment.address && std::uint64_t(address - segment.address) + 4 <= segment.bytes.size()) {
            std::uint32_t value;
            std::memcpy(&value, segment.bytes.data() + (address - segment.address), 4);
            return value;
        }
    }
    return std::nullopt;
}

bool Image::executable(std::uint32_t address) const {
    // Zero-filled memory is data until the game loads code there. Translating its
    // initial zeroes would mask a fixed-address overlay loaded into that space.
    for (const auto &segment : segments_)
        if (segment.executable && address >= segment.address && address - segment.address < segment.initialized_size)
            return true;
    return false;
}

}
