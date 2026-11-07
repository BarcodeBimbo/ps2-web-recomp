#include "frame_clock.hpp"
#include "ps2/disc.hpp"
#include "ps2/state_request.hpp"
#include "ps2/system.hpp"
#include "ps2/video.hpp"

#include <emscripten.h>
#include <emscripten/threading.h>
#include <pthread.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

void register_generated_code();
void register_generated_vu();

EM_JS_DEPS(ps2web, "$stringToNewUTF8,$UTF8ToString");

EM_JS(void, ps2web_fetch, (const char *url, double offset, int size, void *out, std::atomic<std::uint32_t> *state), {
    const target = UTF8ToString(url);
    const finish = (value) => {
        Atomics.store(HEAP32, state >> 2, value);
        Atomics.notify(HEAP32, state >> 2);
    };
    const end = offset + size - 1;
    const load = async () => {
        // More retries + longer abort: panel can hitch while wasm builds hammer the disk.
        for (let attempt = 0; attempt < 4; ++attempt) {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 25000);
            try {
                const response = await fetch(target, {
                    headers: {Range: "bytes=" + offset + "-" + end},
                    signal: controller.signal
                });
                const range = response.headers.get("Content-Range") || "";
                if (response.status !== 206 || !range.startsWith("bytes " + offset + "-" + end + "/")) {
                    if (response.body) await response.body.cancel();
                    throw new Error("Invalid disc range response: " + response.status + " " + range);
                }
                const bytes = new Uint8Array(size);
                const reader = response.body.getReader();
                let used = 0;
                try {
                    while (true) {
                        const chunk = await reader.read();
                        if (chunk.done) break;
                        if (chunk.value.length > size - used) throw new Error("Oversized disc range response");
                        bytes.set(chunk.value, used); used += chunk.value.length;
                    }
                } finally { await reader.cancel().catch(() => {}); }
                if (used !== size) throw new Error("Short disc range response");
                HEAPU8.set(bytes, out);
                finish(3);
                return;
            } catch (error) {
                if (attempt === 3) {
                    console.warn("Disc read failed at byte " + offset, error);
                    finish(4);
                } else {
                    await new Promise((r) => setTimeout(r, 250 * (attempt + 1)));
                }
            } finally {
                clearTimeout(timeout);
            }
        }
    };
    load();
});

EM_JS(int, ps2web_save_program, (const char *name, const std::uint8_t *code, int size), {
    try {
        const xhr = new XMLHttpRequest();
        xhr.open("PUT", "vu1/" + UTF8ToString(name), false);
        xhr.send(HEAPU8.slice(code, code + size));
        return xhr.status;
    } catch (e) {
        return 0;
    }
});

EM_JS(double, ps2web_disc_size, (), { return Module.discSize || 0; });
EM_JS(char *, ps2web_card_path, (), {
    return stringToNewUTF8(Module.ps2CardPath || "/memcard/Mcd001.ps2");
});
EM_JS(char *, ps2web_state_url, (), { return Module.stateUrl ? stringToNewUTF8(new URL(Module.stateUrl, location.href).href) : 0; });
EM_JS(double, ps2web_url_size, (const char *url), {
    try {
        const xhr = new XMLHttpRequest();
        xhr.open("HEAD", UTF8ToString(url), false);
        xhr.send();
        return xhr.status === 200 ? Number(xhr.getResponseHeader("Content-Length") || 0) : 0;
    } catch (e) {
        return 0;
    }
});
EM_JS(double, ps2web_url_read, (const char *url, std::uint8_t *out, double size), {
    try {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", UTF8ToString(url), false);
        xhr.responseType = "arraybuffer";
        xhr.send();
        if (xhr.status !== 200) return 0;
        const bytes = new Uint8Array(xhr.response);
        HEAPU8.set(bytes.subarray(0, size), out);
        return bytes.length;
    } catch (e) {
        return 0;
    }
});
EM_JS(char *, ps2web_disc_url, (), { return stringToNewUTF8(new URL(Module.discUrl, location.href).href); });
EM_JS(void, ps2web_frame_done, (), {
    if (!Module.shownChannel) {
        Module.shownChannel = new MessageChannel();
        Module.shownWaiters = [];
        Module.shownChannel.port1.onmessage = () => {
            Module.shownPending = false;
            const waiters = Module.shownWaiters;
            Module.shownWaiters = [];
            for (const resolve of waiters) resolve();
        };
    }
    Module.shownPending = true;
    requestAnimationFrame(() => Module.shownChannel.port2.postMessage(0));
    if (Module.onFrame) Module.onFrame();
});
// Disc chunk waits (FMV / large reads) can block the emu worker for tens of seconds
// without presenting. Keep the shell's frame-stall watchdog from false-firing.
EM_JS(void, ps2web_busy_heartbeat, (int waiting_on_disc), {
    Module.lastFrameAt = performance.now();
    Module.discWaiting = !!waiting_on_disc;
});
EM_ASYNC_JS(void, ps2web_wait_shown, (), {
    if (Module.shownPending) await new Promise((resolve) => Module.shownWaiters.push(resolve));
});
EM_JS(void, ps2web_stream_frame, (const std::uint32_t *rgba, int width, int height), {
    if (Module.onStreamFrame) Module.onStreamFrame(HEAPU8.subarray(rgba, rgba + width * height * 4), width, height);
});

EM_JS(void, ps2web_blit, (const std::uint32_t *rgba, int width, int height, int wide), {
    const canvas = Module.canvas;
    if (!Module.blitContext) Module.blitContext = canvas.getContext("2d");
    if (!Module.blitImage || Module.blitImage.width !== width || Module.blitImage.height !== height) {
        Module.blitImage = new ImageData(width, height);
        Module.blitSource = new OffscreenCanvas(width, height);
    }
    Module.blitImage.data.set(HEAPU8.subarray(rgba, rgba + width * height * 4));
    Module.blitSource.getContext("2d").putImageData(Module.blitImage, 0, 0);
    const ctx = Module.blitContext;
    const across = wide ? 16 : 4, down = wide ? 9 : 3;
    const scale = Math.min(canvas.width / across, canvas.height / down);
    const w = scale * across, h = scale * down;
    const sx = Math.max(1, Math.floor(w / width)), sy = Math.max(1, Math.floor(h / height));
    let source = Module.blitSource;
    if (sx > 1 || sy > 1) {
        if (!Module.blitSharp || Module.blitSharp.width !== width * sx || Module.blitSharp.height !== height * sy)
            Module.blitSharp = new OffscreenCanvas(width * sx, height * sy);
        const sharp = Module.blitSharp.getContext("2d");
        sharp.imageSmoothingEnabled = false;
        sharp.drawImage(Module.blitSource, 0, 0, width * sx, height * sy);
        source = Module.blitSharp;
    }
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(source, (canvas.width - w) / 2, (canvas.height - h) / 2, w, h);
});

namespace {

constexpr std::size_t kChunk = 256u << 10;
constexpr std::uint32_t kSlots = 256;
constexpr std::uint64_t kReadAhead = 16;
constexpr std::uint32_t kAudioFrames = 1u << 14;

enum : std::uint32_t { kEmpty, kWanted, kLoading, kReady, kFailed };

struct Slot {
    std::atomic<std::uint32_t> state{kEmpty};
    std::uint64_t index = 0, used = 0;
    std::uint32_t size = 0;
    std::uint8_t *data = nullptr;
};

struct AudioRing {
    std::atomic<std::uint32_t> write{0}, read{0};
    std::uint32_t capacity = kAudioFrames;
    std::atomic<std::uint32_t> active{0};
    std::int16_t samples[kAudioFrames * 2];
};

AudioRing g_audio;
Slot g_slots[kSlots];
std::uint64_t g_disc_size = 0, g_use_clock = 0, g_last_chunk = ~0ull, g_run = 0;
char *g_disc_url = nullptr;
char *g_state_url = nullptr;

Slot *find_slot(std::uint64_t index) {
    for (Slot &s : g_slots)
        if (s.state.load(std::memory_order_acquire) != kEmpty && s.index == index) return &s;
    return nullptr;
}

Slot *want(std::uint64_t index) {
    if (index * kChunk >= g_disc_size) return nullptr;
    if (Slot *s = find_slot(index)) return s;
    Slot *victim = nullptr;
    for (Slot &s : g_slots) {
        const std::uint32_t state = s.state.load(std::memory_order_acquire);
        if (state == kEmpty) {
            victim = &s;
            break;
        }
        if ((state == kReady || state == kFailed) && (!victim || s.used < victim->used)) victim = &s;
    }
    if (!victim) return nullptr;
    if (!victim->data) victim->data = new std::uint8_t[kChunk];
    victim->index = index;
    victim->size = static_cast<std::uint32_t>(std::min<std::uint64_t>(kChunk, g_disc_size - index * kChunk));
    victim->used = ++g_use_clock;
    victim->state.store(kWanted, std::memory_order_release);
    ps2::wake_render_thread();
    return victim;
}

void advance(std::uint64_t index) {
    if (index <= g_last_chunk && g_last_chunk - index <= kReadAhead * 4) return;
    g_run = index == g_last_chunk + 1 ? g_run + 1 : 0;
    g_last_chunk = index;
}

void read_ahead(std::uint64_t index) {
    // After a seek (FMV/level load) g_run resets to 0 and used to prefetch nothing,
    // so the EE stalled on every chunk and gameplay felt like skipped frames.
    // Keep a minimum depth so the first sequential reads after a jump stay warm.
    const std::uint64_t depth = std::max<std::uint64_t>(8, std::min(g_run * 2 + 4, kReadAhead));
    for (std::uint64_t k = 1; k <= depth; ++k) want(index + k);
}

const Slot *chunk(std::uint64_t index) {
    Slot *s = want(index);
    advance(index);
    read_ahead(std::max(index, g_last_chunk));
    if (s) {
        // 90s: panel can stall under parallel wasm builds / large ISO ranges.
        const double deadline = emscripten_get_now() + 90000.0;
        for (;;) {
            const auto state = s->state.load(std::memory_order_acquire);
            if (state == kReady) {
                s->used = ++g_use_clock;
                ps2web_busy_heartbeat(0);
                return s;
            }
            if (state == kFailed || emscripten_get_now() >= deadline) {
                ps2web_busy_heartbeat(0);
                ps2::halt("Disc streaming failed or timed out. Check the server connection and reload the game.");
                return nullptr;
            }
            ps2web_busy_heartbeat(1);
            emscripten_futex_wait(&s->state, state, 1000.0);
        }
    }
    return nullptr;
}

bool disc_ready(std::uint64_t offset, std::size_t size) {
    if (!size) return true;
    const std::uint64_t last = (offset + size - 1) / kChunk;
    bool ready = true;
    for (std::uint64_t index = offset / kChunk; index <= last; ++index) {
        Slot *s = want(index);
        if (s && s->state.load(std::memory_order_acquire) == kFailed) {
            ps2::halt("Disc streaming failed. Check the server connection and reload the game.");
            return false;
        }
        ready = ready && s && s->state.load(std::memory_order_acquire) == kReady;
        advance(index);
    }
    read_ahead(std::max(last, g_last_chunk));
    return ready;
}

std::size_t read_disc(std::uint64_t offset, void *out, std::size_t size) {
    std::size_t done = 0;
    auto *to = static_cast<std::uint8_t *>(out);
    while (done < size && offset + done < g_disc_size) {
        const std::uint64_t at = offset + done;
        const Slot *c = chunk(at / kChunk);
        if (!c) break;
        const std::size_t within = static_cast<std::size_t>(at % kChunk);
        const std::size_t take = std::min<std::size_t>(size - done, c->size - within);
        std::memcpy(to + done, c->data + within, take);
        done += take;
    }
    return done;
}

void service_disc() {
    for (Slot &s : g_slots) {
        std::uint32_t expected = kWanted;
        if (s.state.compare_exchange_strong(expected, kLoading, std::memory_order_acq_rel))
            ps2web_fetch(g_disc_url, static_cast<double>(s.index * kChunk), static_cast<int>(s.size), s.data, &s.state);
    }
}

void push_audio(const std::int16_t *samples, std::size_t frames) {
    std::uint32_t write = g_audio.write.load(std::memory_order_relaxed);
    const std::uint32_t read = g_audio.read.load(std::memory_order_acquire);
    for (std::size_t i = 0; i < frames && write - read < kAudioFrames; ++i, ++write) {
        const std::uint32_t at = (write & (kAudioFrames - 1)) * 2;
        g_audio.samples[at] = samples[i * 2];
        g_audio.samples[at + 1] = samples[i * 2 + 1];
    }
    g_audio.write.store(write, std::memory_order_release);
}

double audio_queued_ms() { return static_cast<double>(g_audio.write.load() - g_audio.read.load()) / 48.0; }

double g_next_frame = 0.0;
std::atomic<double> g_emulation_idle{0.0}, g_render_idle{0.0};
// 0 = uncapped (no wall-clock sleep). Default NTSC 60 / PAL 50 until shell overrides.
std::atomic<double> g_frame_period_ms{1000.0 / 60.0};
std::atomic<bool> g_vsync{true};

void pace() {
    ps2::post_present();
    // With V-Sync on, never run uncapped: an uncapped EE floods presents into
    // hard RAF waits and reads as menu/gameplay frame skips (hitch trains).
    double period = g_frame_period_ms.load(std::memory_order_relaxed);
    if (g_vsync.load(std::memory_order_relaxed)) {
        if (period <= 0.0 || period < (1000.0 / 60.0) * 0.98)
            period = ps2::g_options.pal ? 20.0 : 1000.0 / 60.0;
    } else if (period <= 0.0) {
        if (g_audio.active.load() && audio_queued_ms() > 250.0) usleep(500);
        return;
    }
    const double now = emscripten_get_now();
    g_next_frame = ps2web::next_frame_deadline(now, g_next_frame, period);
    // Sleep most of the wait, then spin the last ~1.5 ms so usleep overshoot
    // cannot push us past the vsync and produce the remaining 55–58 on-screen dips.
    if (g_next_frame > now) {
        const double sleep_ms = g_next_frame - now;
        if (sleep_ms > 1.5) usleep(static_cast<useconds_t>((sleep_ms - 1.5) * 1000.0));
        while (emscripten_get_now() < g_next_frame) {
        }
    }
    // Soft audio trim after pace so it cannot steal from the vsync deadline.
    if (g_audio.active.load() && audio_queued_ms() > 250.0) usleep(500);
}

void on_vblank() {
    const double start = emscripten_get_now();
    pace();
    g_emulation_idle.store(g_emulation_idle.load() + emscripten_get_now() - start);
}

struct Launch {
    std::vector<std::string> args;
};

void notify_halt(const char *reason) {
    // The callback is queued for the browser thread, so its argument must outlive
    // this function. A single fixed buffer is sufficient because a stopped player
    // cannot safely restart its worker set without reloading the page.
    static std::atomic<bool> notified{false};
    static char message[1024] = {};
    if (notified.exchange(true, std::memory_order_acq_rel)) return;
    std::snprintf(message, sizeof(message), "%s", reason ? reason : "The emulator stopped.");
    // emulate() normally runs on a pthread; Module callbacks belong to the main thread.
    MAIN_THREAD_ASYNC_EM_ASM({
        if (typeof Module.onHalt === "function") Module.onHalt(UTF8ToString($0));
    }, message);
}

void *emulate(void *data) {
    try {
    const Launch &launch = *static_cast<const Launch *>(data);
    if (!g_disc_size) {
        std::fprintf(stderr, "[web] disc image is missing or has an invalid size\n");
        notify_halt("Disc image is missing or unavailable. Check the disc URL and reload the player.");
        return nullptr;
    }
    if (!ps2::disc::open("disc", g_disc_size, read_disc, disc_ready)) {
        std::fprintf(stderr, "[web] cannot open the disc image\n");
        notify_halt("Could not open the disc image. Check that it is a valid PS2 ISO and that the server is reachable.");
        return nullptr;
    }
    std::uint32_t entry = 0;
    ps2::load_patches("/game/patches.txt");
    if (!ps2::load_elf("/game/core.elf", entry)) {
        std::fprintf(stderr, "cannot load the game executable\n");
        notify_halt("Could not load the translated game executable. Rebuild the game and check the build log.");
        return nullptr;
    }
    ps2::boot(entry, launch.args);
    if (g_state_url) {
        const double size = ps2web_url_size(g_state_url);
        constexpr double max_state_size = 512.0 * 1024.0 * 1024.0;
        if (!std::isfinite(size) || size <= 0.0 || size > max_state_size) {
            std::fprintf(stderr, "[web] invalid or oversized state file\n");
            notify_halt("The save-state file is missing, invalid, or larger than 512 MiB.");
            return nullptr;
        }
        std::vector<std::uint8_t> data(static_cast<std::size_t>(size));
        if (ps2web_url_read(g_state_url, data.data(), size) != size || !ps2::load_state(data.data(), data.size())) {
            std::fprintf(stderr, "[web] cannot load the state %s\n", g_state_url);
            notify_halt("Could not load the selected save state. Check the file and try again.");
            return nullptr;
        }
    }
    ps2::run();
    notify_halt(ps2::halt_reason().c_str());
    } catch (const std::exception &error) { notify_halt(error.what()); }
      catch (...) { notify_halt("Unexpected emulation failure. Download diagnostics and rebuild the game."); }
    return nullptr;
}

}

extern "C" EMSCRIPTEN_KEEPALIVE int ps2web_cheat(unsigned slot, unsigned address, unsigned bytes, unsigned low, unsigned high, int enabled) {
    return ps2::set_live_patch(slot, address, bytes, std::uint64_t(low) | (std::uint64_t(high) << 32), enabled != 0) ? 1 : 0;
}

extern "C" EMSCRIPTEN_KEEPALIVE int ps2web_prompt_capture(int start) {
    return start ? ps2::request_prompt_capture() : ps2::prompt_capture_status();
}

extern "C" EMSCRIPTEN_KEEPALIVE void ps2web_pad(int pad, int buttons, int lx, int ly, int rx, int ry) {
    ps2::set_pad_buttons(static_cast<std::uint16_t>(buttons), pad);
    ps2::set_pad_axis(0, static_cast<std::uint8_t>(rx), pad);
    ps2::set_pad_axis(1, static_cast<std::uint8_t>(ry), pad);
    ps2::set_pad_axis(2, static_cast<std::uint8_t>(lx), pad);
    ps2::set_pad_axis(3, static_cast<std::uint8_t>(ly), pad);
}

extern "C" EMSCRIPTEN_KEEPALIVE void ps2web_pad_connected(int pad, int connected) { ps2::set_pad_connected(pad, connected != 0); }

extern "C" EMSCRIPTEN_KEEPALIVE void ps2web_pressure(int pad, int a, int b, int c, int d) {
    const int packed[4] = {a, b, c, d};
    for (int i = 0; i < 16; ++i) ps2::set_pad_pressure(i, static_cast<std::uint8_t>(static_cast<unsigned>(packed[i / 4]) >> (i % 4 * 8)), pad);
}

extern "C" EMSCRIPTEN_KEEPALIVE int ps2web_rumble(int pad) { return ps2::pad_rumble(pad); }

extern "C" EMSCRIPTEN_KEEPALIVE void ps2web_resize(int width, int height) {
    ps2::resize_window(static_cast<std::uint32_t>(width), static_cast<std::uint32_t>(height));
}

extern "C" EMSCRIPTEN_KEEPALIVE int ps2web_quick_state(int loading) {
    return ps2::request_state_operation(loading != 0, "/quicksave.state", [](bool load, bool success) {
        MAIN_THREAD_ASYNC_EM_ASM({
            if (Module.onQuickState) Module.onQuickState(!!$0, !!$1);
        }, load, success);
    }) ? 1 : 0;
}

std::atomic<bool> g_streaming{false};

extern "C" EMSCRIPTEN_KEEPALIVE void ps2web_stream(int on) { g_streaming.store(on != 0); }

extern "C" EMSCRIPTEN_KEEPALIVE void ps2web_video_options(int flags) { ps2::set_video_options(static_cast<std::uint32_t>(flags)); }

extern "C" EMSCRIPTEN_KEEPALIVE void ps2web_set_fps_limit(double fps) {
    if (!(fps > 0.0) || fps > 1000.0) {
        // Uncapped is only legal with V-Sync off; otherwise keep the 60 Hz lock.
        if (g_vsync.load(std::memory_order_relaxed))
            g_frame_period_ms.store(ps2::g_options.pal ? 20.0 : 1000.0 / 60.0, std::memory_order_relaxed);
        else
            g_frame_period_ms.store(0.0, std::memory_order_relaxed);
        return;
    }
    if (g_vsync.load(std::memory_order_relaxed) && fps > 60.5)
        fps = ps2::g_options.pal ? 50.0 : 60.0;
    g_frame_period_ms.store(1000.0 / fps, std::memory_order_relaxed);
}

extern "C" EMSCRIPTEN_KEEPALIVE double ps2web_fps_limit() {
    const double period = g_frame_period_ms.load(std::memory_order_relaxed);
    return period <= 0.0 ? 0.0 : 1000.0 / period;
}

extern "C" EMSCRIPTEN_KEEPALIVE void ps2web_set_vsync(int on) {
    const bool enabled = on != 0;
    g_vsync.store(enabled, std::memory_order_relaxed);
    if (enabled) {
        const double period = g_frame_period_ms.load(std::memory_order_relaxed);
        if (period <= 0.0 || period < (1000.0 / 60.0) * 0.98)
            g_frame_period_ms.store(ps2::g_options.pal ? 20.0 : 1000.0 / 60.0, std::memory_order_relaxed);
    }
}

extern "C" EMSCRIPTEN_KEEPALIVE int ps2web_vsync() {
    return g_vsync.load(std::memory_order_relaxed) ? 1 : 0;
}

extern "C" EMSCRIPTEN_KEEPALIVE double ps2web_gpu_ms() { return ps2::gpu_busy_ms(); }
extern "C" EMSCRIPTEN_KEEPALIVE double ps2web_frames() { return static_cast<double>(ps2::frames_run()); }
extern "C" EMSCRIPTEN_KEEPALIVE int ps2web_diagnostics(int request) {
    return request ? ps2::request_diagnostics() : ps2::diagnostics_pending();
}
extern "C" EMSCRIPTEN_KEEPALIVE double ps2web_primitives() { return static_cast<double>(ps2::primitives_drawn()); }
extern "C" EMSCRIPTEN_KEEPALIVE void *ps2web_audio_ring() { return &g_audio; }
extern "C" EMSCRIPTEN_KEEPALIVE double ps2web_audio_queued_ms() { return audio_queued_ms(); }
extern "C" EMSCRIPTEN_KEEPALIVE double ps2web_vu_interpreted() { return static_cast<double>(ps2::vu1_interpreted_calls()); }
extern "C" EMSCRIPTEN_KEEPALIVE double ps2web_idle_ms(int which) {
    if (which == 2) return ps2::vu_thread_idle_ms();
    return which ? g_render_idle.load() : g_emulation_idle.load();
}

int main(int argc, char **argv) {
    static Launch launch;
    for (int i = 2; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--arg" && i + 1 < argc) launch.args.push_back(argv[++i]);
        else if (a == "--frames" && i + 1 < argc) ps2::g_options.max_frames = std::strtoull(argv[++i], nullptr, 10);
        else if (a == "--widescreen") ps2::g_options.widescreen = true;
        else if (a == "--press" && i + 1 < argc) {
            ps2::Press press;
            if (ps2::parse_press(argv[++i], press)) ps2::g_options.presses.push_back(press);
        }
    }
    if (launch.args.empty()) {
        std::string boot = "/game/core.elf";
        if (std::FILE *f = std::fopen("/game/boot.txt", "rb")) {
            char text[256] = {};
            const std::size_t n = std::fread(text, 1, sizeof text - 1, f);
            std::fclose(f);
            std::string line(text, n);
            line.erase(line.find_last_not_of(" \r\n\t") + 1);
            if (!line.empty()) boot = line;
        }
        launch.args.push_back(boot);
    }
    g_disc_size = static_cast<std::uint64_t>(ps2web_disc_size());
    g_disc_url = ps2web_disc_url();
    g_state_url = ps2web_state_url();
    ps2::g_options.on_vblank = on_vblank;
    ps2::g_options.on_vu_program = [](const std::string &name, const std::uint8_t *code, std::size_t size) {
        static bool unsupported = false;
        if (unsupported) return;
        const int status = ps2web_save_program(name.c_str(), code, static_cast<int>(size));
        if (status == 200 || status == 201) std::fprintf(stderr, "[web] saved VU1 program %s\n", name.c_str());
        else unsupported = true;
    };
    if (!EM_ASM_INT({ return Module.noCard ? 1 : 0; })) {
        char *card_path = ps2web_card_path();
        if (card_path) ps2::g_options.memcard_path = card_path;
        std::free(card_path);
        ps2::g_options.on_memcard_saved = [] { MAIN_THREAD_ASYNC_EM_ASM({ if (Module.ps2CardSaved) Module.ps2CardSaved(); }); };
    }
    ps2::set_audio_sink(push_audio);
    register_generated_code();
    register_generated_vu();

    if (const char *fps = std::getenv("PS2_FPS_LIMIT")) {
        const double value = std::atof(fps);
        if (!(value > 0.0) || value > 1000.0) g_frame_period_ms.store(0.0, std::memory_order_relaxed);
        else g_frame_period_ms.store(1000.0 / value, std::memory_order_relaxed);
    } else if (ps2::g_options.pal) {
        g_frame_period_ms.store(20.0, std::memory_order_relaxed);
    }
    if (const char *vsync = std::getenv("PS2_VSYNC")) {
        g_vsync.store(std::strcmp(vsync, "0") && std::strcmp(vsync, "off") && std::strcmp(vsync, "false"),
                      std::memory_order_relaxed);
    }

    ps2::init_graphics();
    const bool no_surface = EM_ASM_INT({ return Module.noSurface ? 1 : 0; });
    bool copy = EM_ASM_INT({ return Module.presentCopy ? 1 : 0; });
    bool surface = false;
    if (!copy && !no_surface) {
        ps2::WindowTarget target;
        target.kind = ps2::WindowTarget::Canvas;
        target.selector = "#canvas";
        target.width = static_cast<std::uint32_t>(EM_ASM_INT({ return Module.canvas.width; }));
        target.height = static_cast<std::uint32_t>(EM_ASM_INT({ return Module.canvas.height; }));
        surface = ps2::attach_window(target);
    }
    copy = copy || (!surface && !no_surface);
    EM_ASM({
        Module.videoEffectsAvailable = !!$0;
        if (Module.refreshVideoControls) Module.refreshVideoControls();
    }, surface);
    std::fprintf(stderr, "[web] %s\n", surface ? "presenting through WebGPU" : copy ? "presenting through a 2D canvas copy" : "not presenting");

    ps2::start_render_thread();
    pthread_attr_t attr;
    if (pthread_attr_init(&attr) != 0) {
        std::fprintf(stderr, "[web] cannot initialize thread attributes\n");
        notify_halt("The browser could not initialize the emulator worker threads.");
        return 1;
    }
    if (pthread_attr_setstacksize(&attr, 16u << 20) != 0)
        std::fprintf(stderr, "[web] could not set the requested worker stack size; using the platform default\n");
    if (!std::getenv("PS2_NO_VU_THREAD")) {
        ps2::start_vu_thread();
        pthread_t vu_thread;
        if (pthread_create(&vu_thread, &attr, [](void *) -> void * {
                ps2::run_vu_thread();
                return nullptr;
            }, nullptr) != 0) {
            pthread_attr_destroy(&attr);
            std::fprintf(stderr, "[web] cannot start the VU thread\n");
            notify_halt("Could not start the vector-unit worker. Close other tabs and reload the game.");
            return 1;
        }
    }
    pthread_t thread;
    if (pthread_create(&thread, &attr, emulate, &launch) != 0) {
        pthread_attr_destroy(&attr);
        std::fprintf(stderr, "[web] cannot start the emulation thread\n");
        notify_halt("Could not start the emulation worker. Close other tabs and reload the game.");
        return 1;
    }
    pthread_attr_destroy(&attr);
    const std::function<void(const std::uint32_t *, std::uint32_t, std::uint32_t)> blit = [](const std::uint32_t *rgba, std::uint32_t width, std::uint32_t height) {
        ps2web_blit(rgba, static_cast<int>(width), static_cast<int>(height), ps2::g_options.widescreen ? 1 : 0);
    };
    const std::function<void(const std::uint32_t *, std::uint32_t, std::uint32_t)> streamed = [copy, &blit](const std::uint32_t *rgba, std::uint32_t width, std::uint32_t height) {
        if (copy) blit(rgba, width, height);
        if (g_streaming.load()) ps2web_stream_frame(rgba, static_cast<int>(width), static_cast<int>(height));
    };
    const std::function<void(const std::uint32_t *, std::uint32_t, std::uint32_t)> none;
    // Hard RAF wait when V-Sync is on (locks presents to the display). Off skips
    // so high FPS caps can exceed refresh.
    // After disc/load stalls the EE can queue 3–4 presents. Waiting a full vsync
    // for each one turns one load hitch into a visible skip train. Skip the wait
    // only while deeply backed up (>2); steady play stays at depth 0–1 with a
    // hard wait every frame (skipping at >1 was the mid-50s regression).
    const std::function<void()> wait_shown = [] {
        if (!g_vsync.load(std::memory_order_relaxed)) return;
        if (ps2::presents_queued() > 2) return;
        const double start = emscripten_get_now();
        ps2web_wait_shown();
        g_render_idle.store(g_render_idle.load() + emscripten_get_now() - start);
    };
    for (;;) {
        service_disc();
        // 10 ms budget drains present backlog under Asyncify better than 6 ms
        // (which left frames queued and read as stutter).
        const ps2::Rendered rendered = ps2::render_pending(surface, g_streaming.load() ? streamed : copy ? blit : none, wait_shown, 10.0);
        if (rendered == ps2::Rendered::presented) ps2web_frame_done();
        if (rendered != ps2::Rendered::idle) {
            ps2::browser_yield();
        } else {
            const double start = emscripten_get_now();
            ps2::wait_render_work(50);
            g_render_idle.store(g_render_idle.load() + emscripten_get_now() - start);
        }
    }
}
