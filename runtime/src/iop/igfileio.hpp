#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace ps2::iop::igfileio {

// Host-side Vicarious Visions / Alchemy GFC+GOB reader used by IGFILEIO HLE.
// Shared by any title that loads IGFILEIO without shipping the IRX on disc.
bool ensure_index();
bool read_asset(const std::string &path, std::vector<std::uint8_t> &out);
bool read_asset_by_crc(std::uint32_t crc, std::vector<std::uint8_t> &out);
// If EE has a pending Alchemy STBLz cluster buffer, rewrite it as STBL0 in place
// when the decompressed payload fits. Generic for GFC/GOB titles that park
// compressed clusters in EE before a guest inflate that never runs.
bool service_pending_stblz();
// True while an Alchemy GFC cluster sits armed in EE scratch (walker flag set).
bool alchemy_asset_pending();
// Run deferred host_call work from the top-level EE loop (not from vblank).
bool poll_deferred_work();
void reset();
// True after deferred UI-IGB FCE0 attempt (cdvdfsv may release intro hold).
bool ui_igb_parse_attempted();

// RPC 0x12114 handler. Returns true when the call is fully answered.
bool handle(std::uint32_t method, std::uint32_t args, std::uint32_t size, std::uint32_t ret, std::uint32_t ret_size);

}
