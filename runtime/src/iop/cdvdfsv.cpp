#include "kernel.hpp"
#include "sif.hpp"
#include "igfileio.hpp"

#include "ps2/disc.hpp"
#include "ps2/memory.hpp"
#include "ps2/system.hpp"
#include "../kernel.hpp"

#include "ps2/state.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <map>
#include <string>
#include <vector>

namespace ps2::iop::kernel {

namespace {

std::uint32_t ee32(std::uint32_t a) { return load<std::uint32_t>(ps2::g_ram + (a & (ps2::kRamSize - 1))); }
void set_ee32(std::uint32_t a, std::uint32_t v) { store<std::uint32_t>(ps2::g_ram + (a & (ps2::kRamSize - 1)), v); }

std::uint8_t bcd(int v) { return static_cast<std::uint8_t>(((v / 10) << 4) | (v % 10)); }

bool g_streaming = false;
std::uint32_t g_stream_pos = 0;
// sceCdDiskReady FSV path (0x8000059A/59C + N-cmd 0x0E). ISO HLE keeps the
// drive ready; mode is honored so NotReady(6) can return if this ever clears.
bool g_fsv_drive_ready = true;
// sceCdRead is single-flight (_CdCheckNCmd). Stash readee/curReadPos targets
// here so the FsvRead job (4 payload words) can still finish retail-style.
std::uint32_t g_read_eeaddr1 = 0, g_read_eeaddr2 = 0;
[[maybe_unused]] std::uint32_t g_read_args = 0;
std::uint64_t g_next_virt_complete = 0;
// Hold INTROTXR virt reads until BUTANIM post-ingest FCE0 has run (shared scratch).
int g_butanim_hold = 0;

std::uint64_t delay(std::uint32_t sectors, std::uint32_t sector = 0) {
    // Virtual GFC mounts share an EE bounce buffer (CNK: 0x750CC0). Pace
    // completions so the EE _CdAlignReadBuffer / copy-out can run between
    // sectors; real disc keeps the short DVD-ish delay.
    if (sector >= 0xF0000000u)
        // ~1 frame of EE time between virt sector completes.
        return usec_to_cycles(16000) + static_cast<std::uint64_t>(sectors) * usec_to_cycles(1000);
    return usec_to_cycles(400) + static_cast<std::uint64_t>(sectors) * usec_to_cycles(200);
}

// Match retail cdvdfsv cdvd_readee: payload to dst, zeroed readee to eeaddr1
// (_rd_intr_data for _CdAlignReadBuffer), and byte count to eeaddr2 (curReadPos).
// Without curReadPos/readee the EE callback still runs but sceCdGetReadPos stays
// 0 and Alchemy's loadgate slots stick at +76=3 forever.
void read_to_ee(std::uint32_t sector, std::uint32_t count, std::uint32_t dst, std::uint32_t eeaddr1,
                std::uint32_t eeaddr2) {
    std::uint32_t nbytes = count * disc::kSector;
    std::uint32_t write_dst = dst;
    // For virt mounts: on the first sector of each file, collapse the whole
    // file into one EE write at a high scratch address and rewrite the live
    // sceCdRead args (count/dst) + bounce global so the EE copy-out path sees
    // a single full-file transfer instead of a bounce race.
    static std::map<std::uint32_t, std::uint32_t> s_planted; // base → ee addr
    if (sector >= 0xF0000000u) {
        std::string path;
        std::vector<std::uint8_t> full;
        std::uint32_t base = 0;
        if (disc::virtual_payload(sector, &path, &full, &base) && !full.empty()) {
            if (!s_planted.count(base)) {
                // Fixed wells so butanim/intro never clobber each other.
                std::uint32_t well = 0;
                if (path.find("BUTANIM") != std::string::npos || path.find("butanim") != std::string::npos)
                    well = 0x01B00000u;
                else if (path.find("INTROTXR") != std::string::npos || path.find("introtxr") != std::string::npos)
                    well = 0x01B80000u;
                else {
                    static std::uint32_t s_scratch = 0x01B40000u;
                    well = s_scratch;
                    s_scratch += static_cast<std::uint32_t>((full.size() + 0xFFF) & ~0xFFFu);
                }
                if (well && well + full.size() < 0x01F00000u) {
                    s_planted[base] = well;
                    std::fprintf(stderr, "[cdvdfsv] planted virt %s (%zu B) at EE 0x%X\n", path.c_str(), full.size(),
                                 well);
                }
            }
            auto it = s_planted.find(base);
            // Side-channel plant: keep a pristine full-file copy in the well.
            // Do NOT retarget sceCdRead dst/count to the plant — follow-up
            // sector reads would then mirror into the plant base and clobber
            // the header (seen: butanim well ended up with intro magic).
            if (it != s_planted.end() && sector == base) {
                std::memcpy(ps2::g_ram + it->second, full.data(), full.size());
                ps2::watch_span(it->second, static_cast<std::uint32_t>((full.size() + 15u) & ~15u),
                                "cdvd:virt-full");
                std::fprintf(stderr, "[cdvdfsv] virt FULL-file plant %s -> 0x%X (%zu B) dst kept 0x%X\n",
                             path.c_str(), it->second, full.size(), dst);
                if (it->second == 0x01B00000u) g_butanim_hold = 800;
            } else if (it != s_planted.end()) {
                // Refresh plant slice only; retail bounce path still uses dst.
                const std::uint32_t off = (sector - base) * disc::kSector;
                if (off < full.size()) {
                    const std::uint32_t n =
                        static_cast<std::uint32_t>(std::min<std::size_t>(count * disc::kSector, full.size() - off));
                    std::memcpy(ps2::g_ram + it->second + off, full.data() + off, n);
                }
            }
            // Always deliver this request to the caller's bounce dst.
            write_dst = dst;
            // Host-assemble into Alchemy stream scratch while +24008 stays set
            // (EE copy-out is parked on WaitSema). Mirror this sector into
            // loadgate slot stream+0x48 at the file-relative offset.
            if (it != s_planted.end()) {
                const std::uint32_t off = (sector - base) * disc::kSector;
                const std::uint32_t n =
                    static_cast<std::uint32_t>(std::min<std::size_t>(count * disc::kSector, full.size() - off));
                std::uint32_t lg = 0;
                if (0x006F2540u + 4u <= ps2::kRamSize) lg = ee32(0x006F2540u);
                if (lg && n && off < full.size()) {
                    for (std::uint32_t i = 0; i < 8u; ++i) {
                        const std::uint32_t slot = lg + i * 96u;
                        if (slot + 0x50u >= ps2::kRamSize) break;
                        const char *spath = reinterpret_cast<const char *>(ps2::g_ram + slot + 8u);
                        bool match = false;
                        if (path.find("butanim") != std::string::npos || path.find("BUTANIM") != std::string::npos)
                            match = std::strstr(spath, "butanim") || std::strstr(spath, "BUTANIM");
                        else if (path.find("introtxr") != std::string::npos ||
                                 path.find("INTROTXR") != std::string::npos)
                            match = std::strstr(spath, "introtxr") || std::strstr(spath, "INTROTXR");
                        if (!match) continue;
                        const std::uint32_t stream = ee32(slot + 0x4Cu);
                        if (!stream || stream + 0x4Cu >= ps2::kRamSize) continue;
                        const std::uint32_t sb = ee32(stream + 0x48u);
                        if (sb < 0x00100000u || sb + off + n > ps2::kRamSize) continue;
                        std::memcpy(ps2::g_ram + sb + off, full.data() + off, n);
                        ps2::watch_span(sb + off, n, "cdvd:stream-sector");
                        static int s_sec = 0;
                        if (s_sec < 8) {
                            std::fprintf(stderr, "[cdvdfsv] stream-sector %s off=0x%X n=%u -> 0x%X\n", path.c_str(),
                                         off, n, sb);
                            ++s_sec;
                        }
                        break;
                    }
                }
            }
        }
    }
    {
        std::vector<std::uint8_t> data(count * disc::kSector);
        disc::read(sector, count, data.data());
        const std::uint32_t at = write_dst & (ps2::kRamSize - 1);
        std::memcpy(ps2::g_ram + at, data.data(), std::min<std::size_t>(data.size(), ps2::kRamSize - at));
        ps2::watch_span(at, static_cast<std::uint32_t>(std::min<std::size_t>(data.size(), ps2::kRamSize - at)),
                        "cdvd:read");
    }
    if (eeaddr1) {
        const std::uint32_t a1 = eeaddr1 & (ps2::kRamSize - 1);
        // Preserve dest pointers EE may have staged for _CdAlignReadBuffer
        // (+8/+12). Only clear count fields and payload; wiping the whole
        // 144B block destroyed copy-out targets (ee1 stayed all-zero).
        std::uint32_t dest1 = 0, dest2 = 0, cnt1 = 0, cnt2 = 0;
        if (a1 + 16u <= ps2::kRamSize) {
            cnt1 = ee32(a1);
            cnt2 = ee32(a1 + 4u);
            dest1 = ee32(a1 + 8u);
            dest2 = ee32(a1 + 12u);
        }
        if (sector >= 0xF0000000u) {
            static int s_ee1 = 0;
            if (s_ee1 < 6) {
                std::fprintf(stderr, "[cdvdfsv] ee1 pre cnt=%u/%u dest=0x%X/0x%X\n", cnt1, cnt2, dest1, dest2);
                ++s_ee1;
            }
        }
        const std::size_t n = std::min<std::size_t>(144, ps2::kRamSize - a1);
        std::memset(ps2::g_ram + a1, 0, n);
        if (a1 + 16u <= ps2::kRamSize) {
            set_ee32(a1 + 8u, dest1);
            set_ee32(a1 + 12u, dest2);
        }
        // Sony AlignReadBuffer contract: lengths at +0/+4 must be non-zero when
        // dest1/dest2 are fed. Previously we restored dest pointers after memset
        // but left b1len/b2len at 0, so the EE callback saw a dest with no count.
        bool fed_dest = false;
        if (dest1 > 0x100000u && dest1 + nbytes < ps2::kRamSize && write_dst &&
            write_dst + nbytes <= ps2::kRamSize) {
            std::memcpy(ps2::g_ram + dest1, ps2::g_ram + (write_dst & (ps2::kRamSize - 1)), nbytes);
            ps2::watch_span(dest1, nbytes, "cdvd:ee1-dest");
            if (a1 + 4u <= ps2::kRamSize) set_ee32(a1, nbytes);
            fed_dest = true;
            static int s_d1 = 0;
            if (s_d1 < 8) {
                std::fprintf(stderr, "[cdvdfsv] ee1 dest1=0x%X <- 0x%X (%u B) b1len=%u\n", dest1, write_dst, nbytes,
                             nbytes);
                ++s_d1;
            }
        }
        if (dest2 > 0x100000u && dest2 + nbytes < ps2::kRamSize && write_dst &&
            write_dst + nbytes <= ps2::kRamSize && dest2 != dest1) {
            std::memcpy(ps2::g_ram + dest2, ps2::g_ram + (write_dst & (ps2::kRamSize - 1)), nbytes);
            ps2::watch_span(dest2, nbytes, "cdvd:ee1-dest2");
            if (a1 + 8u <= ps2::kRamSize) set_ee32(a1 + 4u, nbytes);
            fed_dest = true;
        }
        // Unaligned bounce dst without an EE-staged dest: stage head/tail in the
        // readee block (payload at +16, optional tail at +80) so AlignReadBuffer
        // can finish copy-out. Full sector bytes already live at write_dst.
        if (!fed_dest && write_dst && nbytes && a1 + 16u <= ps2::kRamSize) {
            const std::uint32_t mis = write_dst & 0xFu;
            if (mis != 0) {
                const std::uint32_t head = std::min(nbytes, 16u - mis);
                const std::uint32_t src = write_dst & (ps2::kRamSize - 1);
                set_ee32(a1, head);
                const std::uint32_t head_copy = std::min(head, 64u);
                if (a1 + 16u + head_copy <= ps2::kRamSize)
                    std::memcpy(ps2::g_ram + a1 + 16u, ps2::g_ram + src, head_copy);
                const std::uint32_t end_mis = (write_dst + nbytes) & 0xFu;
                if (nbytes > head && end_mis != 0 && a1 + 8u <= ps2::kRamSize) {
                    const std::uint32_t tail = end_mis;
                    set_ee32(a1 + 4u, tail);
                    if (a1 + 80u + tail <= ps2::kRamSize && src + nbytes >= tail)
                        std::memcpy(ps2::g_ram + a1 + 80u, ps2::g_ram + src + nbytes - tail, tail);
                }
                static int s_un = 0;
                if (s_un < 8) {
                    std::fprintf(stderr, "[cdvdfsv] readee unaligned dst=0x%X head=%u tail=%u\n", write_dst, head,
                                 (nbytes > head && end_mis) ? end_mis : 0u);
                    ++s_un;
                }
            }
        }
        ps2::watch_span(a1, static_cast<std::uint32_t>(n), "cdvd:readee");
    }
    if (eeaddr2) {
        set_ee32(eeaddr2 & (ps2::kRamSize - 1), nbytes);
        ps2::watch_span(eeaddr2 & (ps2::kRamSize - 1), 4, "cdvd:curpos");
    }
    if (sector >= 0xF0000000u) {
        static int s_ee = 0;
        if (s_ee < 24) {
            std::fprintf(stderr,
                         "[cdvdfsv] EE virt write lba=0x%X count=%u dst=0x%X wr=0x%X nbytes=%u ee1=0x%X ee2=0x%X\n",
                         sector, count, dst, write_dst, nbytes, eeaddr1, eeaddr2);
            ++s_ee;
        }
        // Non-invasive UI IGB read trace: did Alchemy keep requesting plant LBAs?
        std::string vpath;
        std::uint32_t vbase = 0;
        if (disc::virtual_payload(sector, &vpath, nullptr, &vbase)) {
            const bool ui = vpath.find("BUTANIM") != std::string::npos ||
                            vpath.find("butanim") != std::string::npos ||
                            vpath.find("INTROTXR") != std::string::npos ||
                            vpath.find("introtxr") != std::string::npos;
            if (ui) {
                static int s_ui = 0;
                if (s_ui < 48) {
                    std::fprintf(stderr,
                                 "[cdvdfsv] UI-IGB read %s lba=0x%X base=0x%X count=%u dst=0x%X "
                                 "ee_pc=0x%08X ee_ra=0x%08X\n",
                                 vpath.c_str(), sector, vbase, count, dst, ::ps2::g_cpu.pc,
                                 ::ps2::g_cpu.r[31].w[0]);
                    ++s_ui;
                }
            }
        }
    }
}

}

void install_cdvdfsv() {
    g_streaming = false;
    g_stream_pos = 0;
    g_butanim_hold = 0;
    register_job(kJobFsvRead, [](const Job &j) {
        if (g_trace_hle) std::fprintf(stderr, "[cdvdfsv] stream write lsn %u count %u to 0x%08X\n", j.a, j.b, j.c);
        if (!disc::ready(j.a, j.b)) {
            schedule(now() + usec_to_cycles(1000), j);
            return;
        }
        if (j.a >= 0xF0000000u && now() < g_next_virt_complete) {
            schedule(g_next_virt_complete, j);
            return;
        }
        // Defer later virt UI reads while the first IGB slot still needs the
        // shared stream scratch (CNK: BUTANIM then INTROTXR share stream+0x48).
        if (j.a >= 0xF0000000u && g_butanim_hold > 0) {
            std::string vpath;
            std::vector<std::uint8_t> vfull;
            std::uint32_t vbase = 0;
            const bool is_followon =
                disc::virtual_payload(j.a, &vpath, &vfull, &vbase) &&
                (vpath.find("introtxr") != std::string::npos || vpath.find("INTROTXR") != std::string::npos);
            if (is_followon) {
                std::uint32_t lg = 0;
                if (0x006F2540u + 4u <= ps2::kRamSize) lg = ee32(0x006F2540u);
                std::uint32_t st = 0;
                if (lg && lg + 0x54u + 4u <= ps2::kRamSize) st = ee32(lg + 0x54u);
                // Shared stream+0x48 (CNK BD1000): hold intro until BUTANIM
                // vt+108 has run (igfileio ui_igb_parse_attempted). Soft-arm
                // +45 alone must not release — that clobbered butanim bytes
                // before parse (prims stuck at 2). Alchemy/virt-GFC only.
                if (!ps2::iop::igfileio::ui_igb_parse_attempted()) {
                    --g_butanim_hold;
                    schedule(now() + usec_to_cycles(16000), j);
                    static int s_hold = 0;
                    if (s_hold < 8) {
                        std::fprintf(stderr, "[cdvdfsv] hold intro read (butanim +76=%u left=%d)\n", st,
                                     g_butanim_hold);
                        ++s_hold;
                    }
                    return;
                }
                g_butanim_hold = 0;
            }
        }
        // Sony order: payload + readee + curReadPos inside read_to_ee, then complete.
        read_to_ee(j.a, j.b, j.c, g_read_eeaddr1, g_read_eeaddr2);
        if (g_trace_hle) {
            const std::uint32_t nbytes = j.b * disc::kSector;
            std::uint32_t pos = 0;
            if (g_read_eeaddr2 && (g_read_eeaddr2 & (ps2::kRamSize - 1)) + 4u <= ps2::kRamSize)
                pos = ee32(g_read_eeaddr2);
            std::fprintf(stderr,
                         "[cdvdfsv] complete_after_read lba=%u count=%u dst=0x%X readee=0x%X curReadPos@0x%X=%u (expect %u)\n",
                         j.a, j.b, j.c, g_read_eeaddr1, g_read_eeaddr2, pos, nbytes);
        }
        sif::complete_call(0x80000595u);
        // Alchemy parks the UI loadgate on WaitSema(16). Do NOT clear +24008
        // (IO-spams at 0x428970). Wake the waiter; plants hold pristine bytes.
        if (j.a >= 0xF0000000u) {
            g_next_virt_complete = now() + usec_to_cycles(16000);
            ::ps2::kernel::host_signal_sema(16);
            ::ps2::kernel::host_signal_sema(54);
            ::ps2::kernel::host_signal_sema(55);
            // After the last sector of a planted file, retarget live CD request
            // structs that still point at the bounce to the pristine plant.
            std::string path;
            std::vector<std::uint8_t> full;
            std::uint32_t base = 0;
            if (disc::virtual_payload(j.a, &path, &full, &base) && !full.empty()) {
                const std::uint32_t nsec =
                    static_cast<std::uint32_t>((full.size() + disc::kSector - 1) / disc::kSector);
                if (j.a + j.b >= base + nsec) {
                    std::uint32_t plant = 0;
                    if (path.find("butanim") != std::string::npos || path.find("BUTANIM") != std::string::npos)
                        plant = 0x01B00000u;
                    else if (path.find("introtxr") != std::string::npos || path.find("INTROTXR") != std::string::npos)
                        plant = 0x01B80000u;
                    if (plant) {
                        // NEVER retarget bounce global 0x6F5A38 (clobbers plants).
                        // NEVER leave SearchFile+8 aimed at the plant: that diverts
                        // Alchemy's assemble dest away from the stream scratch
                        // (CNK: slot+0x4C → stream+0x48 @ 0xBD1000) so IGB bytes
                        // exist only in the side-channel well and slots stick at +76=3.
                        const std::uint32_t fsz = static_cast<std::uint32_t>(full.size());
                        int ingested = 0, progress = 0, undiverted = 0;

                        // 1) Undo plant diversion on live LBA/size/buf reqs.
                        for (std::uint32_t a = 0x00600000u; a + 12u < 0x00800000u; a += 4u) {
                            if (ee32(a) != base) continue;
                            if (ee32(a + 4u) != fsz) continue;
                            const std::uint32_t buf = ee32(a + 8u);
                            if (buf == plant || buf == 0x01B00000u || buf == 0x01B80000u) {
                                set_ee32(a + 8u, 0x00750CC0u);
                                ++undiverted;
                            }
                        }

                        // 2) Copy plant into Alchemy stream assemble buffers linked
                        // from loadgate UI slots (path @ +8, stream @ +0x4C).
                        std::uint32_t lg = 0;
                        if (0x006F2540u + 4u <= ps2::kRamSize) lg = ee32(0x006F2540u);
                        if (lg && lg + 8u * 96u + 0x50u < ps2::kRamSize) {
                            for (std::uint32_t i = 0; i < 8u; ++i) {
                                const std::uint32_t slot = lg + i * 96u;
                                const char *spath = reinterpret_cast<const char *>(ps2::g_ram + slot + 8u);
                                bool match = false;
                                if (path.find("butanim") != std::string::npos ||
                                    path.find("BUTANIM") != std::string::npos)
                                    match = std::strstr(spath, "butanim") || std::strstr(spath, "BUTANIM");
                                else if (path.find("introtxr") != std::string::npos ||
                                         path.find("INTROTXR") != std::string::npos)
                                    match = std::strstr(spath, "introtxr") || std::strstr(spath, "INTROTXR");
                                if (!match) continue;
                                const std::uint32_t stream = ee32(slot + 0x4Cu);
                                if (!stream || stream + 0x50u >= ps2::kRamSize) continue;
                                // Assemble scratch lives at stream+0x48 (CNK: 0xBD1000).
                                // Do NOT write stream+0 — that is a heap object header.
                                const std::uint32_t dst = ee32(stream + 0x48u);
                                if (dst < 0x00100000u || dst == plant || dst == 0x00750CC0u) continue;
                                if (dst + fsz > ps2::kRamSize) continue;
                                std::memcpy(ps2::g_ram + dst, ps2::g_ram + plant, fsz);
                                ps2::watch_span(dst, fsz, "cdvd:stream-ingest");
                                ++ingested;
                                std::fprintf(stderr,
                                             "[cdvdfsv] ingest %s plant=0x%X -> stream+0x48 0x%X (%u B)\n",
                                             path.c_str(), plant, dst, fsz);
                            }
                        }

                        // 3) Snap CD progress to complete. Guest may not have written
                        // size into 0x6F5A2C yet at IOP complete time — force it.
                        std::uint32_t sb = 0;
                        if (lg && lg + 8u * 96u + 0x50u < ps2::kRamSize) {
                            for (std::uint32_t i = 0; i < 8u; ++i) {
                                const std::uint32_t slot = lg + i * 96u;
                                const char *spath = reinterpret_cast<const char *>(ps2::g_ram + slot + 8u);
                                bool match = false;
                                if (path.find("butanim") != std::string::npos ||
                                    path.find("BUTANIM") != std::string::npos)
                                    match = std::strstr(spath, "butanim") || std::strstr(spath, "BUTANIM");
                                else if (path.find("introtxr") != std::string::npos ||
                                         path.find("INTROTXR") != std::string::npos)
                                    match = std::strstr(spath, "introtxr") || std::strstr(spath, "INTROTXR");
                                if (!match) continue;
                                const std::uint32_t stream = ee32(slot + 0x4Cu);
                                if (!stream || stream + 0x4Cu >= ps2::kRamSize) continue;
                                sb = ee32(stream + 0x48u);
                                break;
                            }
                        }
                        if (0x006F5A38u + 4u <= ps2::kRamSize && ingested) {
                            const std::uint32_t cur_sz = ee32(0x006F5A2Cu);
                            const std::uint32_t cur_pos = ee32(0x006F5A30u);
                            if (sb >= 0x00100000u && sb + fsz <= ps2::kRamSize) set_ee32(0x006F5A24u, sb);
                            set_ee32(0x006F5A2Cu, fsz);
                            set_ee32(0x006F5A30u, fsz);
                            set_ee32(0x006F5A34u, disc::kSector);
                            ++progress;
                            std::fprintf(stderr,
                                         "[cdvdfsv] progress-snap sz 0x%X→0x%X pos 0x%X→0x%X dest=0x%X\n",
                                         cur_sz, fsz, cur_pos, fsz, sb);
                        }

                        // 4) Let 0x10FAF0/0x10FCE0 run: clear +24016 only (NOT +24008).
                        if (lg && lg + 24016u < ps2::kRamSize && ps2::g_ram[lg + 24016u]) {
                            ps2::g_ram[lg + 24016u] = 0;
                        }
                        // Drive FCE0/FAF0 only AFTER status=1 + cursor aim this slot.
                        // FCE0's 0x110100 path requires status==1 and slot+0x50==1; calling
                        // it while status is still 3 was a no-op, then we set 1 too late.
                        // Do NOT clear +24008. Arm obj+45 only when vt+108 is already live.
                        if (lg && ingested) {
                            for (std::uint32_t i = 0; i < 8u; ++i) {
                                const std::uint32_t slot = lg + i * 96u;
                                if (slot + 0x58u >= ps2::kRamSize) break;
                                const char *spath = reinterpret_cast<const char *>(ps2::g_ram + slot + 8u);
                                bool match = false;
                                if (path.find("butanim") != std::string::npos ||
                                    path.find("BUTANIM") != std::string::npos)
                                    match = std::strstr(spath, "butanim") || std::strstr(spath, "BUTANIM");
                                else if (path.find("introtxr") != std::string::npos ||
                                         path.find("INTROTXR") != std::string::npos)
                                    match = std::strstr(spath, "introtxr") || std::strstr(spath, "INTROTXR");
                                if (!match) continue;
                                bool head_ok = false;
                                if (sb >= 0x00100000u && sb + 4u <= ps2::kRamSize && plant + 4u <= ps2::kRamSize)
                                    head_ok = std::memcmp(ps2::g_ram + sb, ps2::g_ram + plant, 4) == 0;
                                const std::uint32_t st_before = ee32(slot + 0x54u);
                                const std::uint32_t field50 = ee32(slot + 0x50u);
                                const std::uint32_t obj = ee32(slot + 0x58u);
                                std::uint8_t o44 = 0, o45 = 0;
                                std::uint32_t vt108 = 0;
                                if (obj && obj + 46u < ps2::kRamSize) {
                                    o44 = ps2::g_ram[obj + 44u];
                                    o45 = ps2::g_ram[obj + 45u];
                                    const std::uint32_t vt = ee32(obj);
                                    if (vt && vt + 112u < ps2::kRamSize) vt108 = ee32(vt + 108u);
                                }
                                // EE _CdAlignReadBuffer dest is 0 for these virt reads, so
                                // the retail copy-out that would arm obj+45 never runs.
                                // Arm +45/+44 only (bytes already in stream+0x48). Do NOT
                                // host_call FCE0/0x110100 here — that jalrs null @ 0x51ACEC
                                // when the bind graph is still cold. Let the guest font
                                // tick reach FCE0 once INTC/sema path is warm.
                                int armed = 0;
                                const bool is_butanim = path.find("butanim") != std::string::npos ||
                                                        path.find("BUTANIM") != std::string::npos;
                                if (head_ok && obj && obj + 46u < ps2::kRamSize && o45 == 0) {
                                    ps2::g_ram[obj + 44u] = 0;
                                    ps2::g_ram[obj + 45u] = 1;
                                    o45 = 1;
                                    armed = 1;
                                    // Remember butanim obj so intro hold waits for vt+108
                                    // (+0xFF), not soft-arm alone. No host FCE0.
                                    ps2::iop::igfileio::note_ui_igb_soft_arm(obj, is_butanim);
                                }
                                if (lg + 24020u + 4u <= ps2::kRamSize) set_ee32(lg + 24020u, i);
                                // Clear +0x5DD0 so guest 0x10F560 can call 0x10FCE0 on
                                // the mapped tid after soft-arm (CNK/Alchemy only).
                                if (armed && lg + 24016u < ps2::kRamSize && ps2::g_ram[lg + 24016u])
                                    ps2::g_ram[lg + 24016u] = 0;
                                if ((st_before == 3u || st_before == 4u) && head_ok)
                                    set_ee32(slot + 0x54u, 1u);
                                const std::uint32_t a9 =
                                    (slot + 0x5Cu + 4u <= ps2::kRamSize) ? ee32(slot + 0x5Cu) : 0u;
                                std::fprintf(stderr,
                                             "[cdvdfsv] post-ingest ready slot%u +76 %u→%u +50=%u "
                                             "head_ok=%d obj=0x%X +44=%u +45=%u vt108=0x%X a9=0x%X "
                                             "armed=%d (no host FCE0)\n",
                                             i, st_before, ee32(slot + 0x54u), field50,
                                             head_ok ? 1 : 0, obj, o44, o45, vt108, a9, armed);
                                break;
                            }
                        }
                        std::fprintf(stderr,
                                     "[cdvdfsv] file-done %s plant=0x%X ingest=%d progress=%d undivert=%d "
                                     "sb=0x%X pos=0x%X\n",
                                     path.c_str(), plant, ingested, progress, undiverted, sb,
                                     0x006F5A30u < ps2::kRamSize ? ee32(0x006F5A30u) : 0u);
                    }
                }
            }
        }
    });
    register_job(kJobFsvComplete, [](const Job &) { sif::complete_call(0x80000595u); });
    register_job(kJobFsvIopRead, [](const Job &j) {
        if (!disc::ready(j.a, j.b)) {
            schedule(now() + usec_to_cycles(1000), j);
            return;
        }
        std::vector<std::uint8_t> data(static_cast<std::size_t>(j.b) * disc::kSector);
        disc::read(j.a, j.b, data.data());
        for (std::size_t i = 0; i < data.size(); ++i) write8(j.c + static_cast<std::uint32_t>(i), data[i]);
        sif::complete_call(0x80000595u);
    });
    sif::register_hle_server(0x80000592u, [](std::uint32_t, std::uint32_t, std::uint32_t, std::uint32_t ret, std::uint32_t ret_size) {
        if (ret_size >= 16) set_ee32(ret + 12, 0xFF);
        return true;
    });
    sif::register_hle_server(0x80000593u, [](std::uint32_t method, std::uint32_t args, std::uint32_t, std::uint32_t ret, std::uint32_t ret_size) {
        switch (method) {
        case 0x01: {
            const std::time_t t = std::time(nullptr);
            const std::tm *tm = std::gmtime(&t);
            set_ee32(ret, 1);
            std::uint8_t *clock = ps2::g_ram + ret + 4;
            clock[0] = 0;
            clock[1] = bcd(tm->tm_sec);
            clock[2] = bcd(tm->tm_min);
            clock[3] = bcd((tm->tm_hour + 9) % 24);
            clock[4] = 0;
            clock[5] = bcd(tm->tm_mday);
            clock[6] = bcd(tm->tm_mon + 1);
            clock[7] = bcd(tm->tm_year % 100);
            break;
        }
        case 0x03: set_ee32(ret, 0x14); break;
        case 0x04: set_ee32(ret, 0); break;
        case 0x05: set_ee32(ret, 1); set_ee32(ret + 4, 0); break;
        case 0x0C: set_ee32(ret, g_streaming ? 0x12u : 0x0Au); break;
        case 0x16: set_ee32(ret, 1); break;
        case 0x22: set_ee32(ret, 1); break;
        case 0x27:
            set_ee32(ret, 1);
            set_ee32(ret + 4, disc::layer1_start() ? 1u : 0u);
            if (ret_size >= 12) set_ee32(ret + 8, disc::layer1_start());
            break;
        default:
            std::fprintf(stderr, "[cdvdfsv] S command 0x%X\n", method);
            set_ee32(ret, 1);
            break;
        }
        (void)args;
        return true;
    });
    sif::register_hle_server(0x80000595u, [](std::uint32_t method, std::uint32_t args, std::uint32_t, std::uint32_t ret, std::uint32_t ret_size) {
        const std::uint32_t sector = ee32(args), count = ee32(args + 4), dst = ee32(args + 8);
        const std::uint32_t eeaddr1 = ee32(args + 16), eeaddr2 = ee32(args + 20);
        g_read_args = args;
        g_read_eeaddr1 = eeaddr1;
        g_read_eeaddr2 = eeaddr2;
        if (g_trace_hle)
            std::fprintf(stderr, "[cdvdfsv] N 0x%X sector %u count %u to 0x%08X eeaddr1(readee)=0x%08X eeaddr2(curReadPos)=0x%08X\n",
                         method, sector, count, dst, eeaddr1, eeaddr2);
        switch (method) {
        case 0x01:
            if (ret_size >= 4) set_ee32(ret, 0);
            disc::ready(sector, count);
            g_read_eeaddr1 = eeaddr1;
            g_read_eeaddr2 = eeaddr2;
            schedule(now() + delay(count, sector), Job{kJobFsvRead, sector, count, dst});
            return false;
        case 0x04: set_ee32(ret, 1); return true;
        case 0x05: return true;
        case 0x08:
            schedule(now() + delay(0), Job{kJobFsvComplete});
            return false;
        case 0x09: {
            const std::uint32_t cmd = ee32(args + 12);
            if (g_trace_hle) std::fprintf(stderr, "[cdvdfsv] stream cmd %u (pos %u)\n", cmd, g_stream_pos);
            switch (cmd) {
            case 1: g_stream_pos = sector; g_streaming = true; set_ee32(ret, 1); return true;
            case 2: {
                const std::uint32_t pos = g_stream_pos;
                g_stream_pos += count;
                set_ee32(ret, count);
                disc::ready(pos, count);
                g_read_eeaddr1 = eeaddr1;
                g_read_eeaddr2 = eeaddr2;
                schedule(now() + delay(count, pos), Job{kJobFsvRead, pos, count, dst});
                return false;
            }
            case 3: g_streaming = false; set_ee32(ret, 1); return true;
            case 4: case 9: g_stream_pos = sector; set_ee32(ret, 1); return true;
            case 5: set_ee32(ret, 1); return true;
            case 6: set_ee32(ret, sector); return true;
            default: set_ee32(ret, 1); return true;
            }
        }
        case 0x0D:
            if (ret_size >= 4) set_ee32(ret, 0);
            disc::ready(sector, count);
            schedule(now() + delay(count, sector), Job{kJobFsvIopRead, sector, count, dst});
            return false;
        // sceCdNcmdDiskReady — status only (EE does not send mode on this path).
        case 0x0E: set_ee32(ret, g_fsv_drive_ready ? 2u : 6u); return true;
        default:
            std::fprintf(stderr, "[cdvdfsv] N command 0x%X\n", method);
            set_ee32(ret, 1);
            return true;
        }
    });
    sif::register_hle_server(0x80000596u, [](std::uint32_t method, std::uint32_t, std::uint32_t, std::uint32_t, std::uint32_t) {
        return method != 0x01;
    });
    sif::register_hle_server(0x80000597u, [](std::uint32_t, std::uint32_t args, std::uint32_t size, std::uint32_t ret, std::uint32_t) {
        const std::uint32_t offset = size == 0x124 ? 0x20u : 0x24u;
        const std::string path(reinterpret_cast<const char *>(ps2::g_ram + (args & (ps2::kRamSize - 1)) + offset));
        auto entry = disc::find(path);
        // Alchemy UI IGBs live in ASSETS.GOB. Virtual-mount from GFC so
        // sceCdSearchFile succeeds. Guest arms loadgate+24008 and WaitSemas a
        // sleep slot — igfileio signals 16/54/55 while set (must NOT clear the
        // flag: that IO-spams at 0x428970). Opt out: PS2_ALCHEMY_NO_CDVD_GFC.
        const bool gfc_off = std::getenv("PS2_ALCHEMY_NO_CDVD_GFC") != nullptr;
        if (!entry && !gfc_off) {
            std::vector<std::uint8_t> data;
            if (igfileio::read_asset(path, data) && !data.empty())
                entry = disc::mount_memory(path, std::move(data));
        }
        if (entry) {
            set_ee32(args, entry->sector);
            set_ee32(args + 4, entry->size);
        }
        std::fprintf(stderr, "[cdvdfsv] search %s -> %s\n", path.c_str(), entry ? "found" : "missing");
        set_ee32(ret, entry ? 1u : 0u);
        return true;
    });
    // EE libcdvd sceCdDiskReady / sceCdDiskReady_old: CallRpc send word = mode
    // (0 block / 1 poll). Recv word = SCECdComplete(2) or SCECdNotReady(6).
    // Mode 0 blocking is EE-side when IOP returns NotReady; with drive ready
    // we complete immediately (SDK-stable for mounted ISO).
    const auto ready = [](std::uint32_t, std::uint32_t args, std::uint32_t args_size, std::uint32_t ret, std::uint32_t) {
        const std::uint32_t mode = (args_size >= 4 && args) ? ee32(args) : 0u;
        if (g_fsv_drive_ready) {
            set_ee32(ret, 2); // SCECdComplete
            return true;
        }
        if (mode == 1) {
            set_ee32(ret, 6); // SCECdNotReady
            return true;
        }
        // mode 0 + not ready: no tray/spin model yet — Complete once media present.
        set_ee32(ret, 2);
        return true;
    };
    sif::register_hle_server(0x8000059Au, ready);
    sif::register_hle_server(0x8000059Cu, ready);
}

}

namespace ps2::iop::kernel {

void cdvdfsv_state(ps2::state::Stream &s) {
    s.tag("cdvdfsv");
    s.pod(g_streaming);
    s.pod(g_stream_pos);
    if (s.version() >= 9) {
        s.pod(g_read_eeaddr1);
        s.pod(g_read_eeaddr2);
    } else if (s.loading()) {
        g_read_eeaddr1 = g_read_eeaddr2 = 0;
    }
    if (s.loading()) g_fsv_drive_ready = true;
}

}
