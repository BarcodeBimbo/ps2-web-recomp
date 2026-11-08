#include "window.hpp"

#include "frame_clock.hpp"
#include "ps2/system.hpp"

#include <SDL.h>
#include <SDL_syswm.h>
#ifdef _WIN32
#include <windows.h>
#include <psapi.h>
#else
#include <sys/resource.h>
#include <unistd.h>
#endif
#ifdef __APPLE__
#include <SDL_metal.h>
#include <mach/mach.h>
#endif

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>

namespace {

enum Button : std::uint16_t {
    kSelect = 1u << 0, kL3 = 1u << 1, kR3 = 1u << 2, kStart = 1u << 3,
    kUp = 1u << 4, kRight = 1u << 5, kDown = 1u << 6, kLeft = 1u << 7,
    kL2 = 1u << 8, kR2 = 1u << 9, kL1 = 1u << 10, kR1 = 1u << 11,
    kTriangle = 1u << 12, kCircle = 1u << 13, kCross = 1u << 14, kSquare = 1u << 15,
};

struct KeyBinding {
    SDL_Scancode key;
    std::uint16_t button;
};

constexpr KeyBinding kKeys[] = {
    {SDL_SCANCODE_UP, kUp},         {SDL_SCANCODE_DOWN, kDown},     {SDL_SCANCODE_LEFT, kLeft},
    {SDL_SCANCODE_RIGHT, kRight},   {SDL_SCANCODE_Z, kCross},       {SDL_SCANCODE_X, kCircle},
    {SDL_SCANCODE_A, kSquare},      {SDL_SCANCODE_S, kTriangle},    {SDL_SCANCODE_Q, kL1},
    {SDL_SCANCODE_W, kR1},          {SDL_SCANCODE_1, kL2},          {SDL_SCANCODE_2, kR2},
    {SDL_SCANCODE_RETURN, kStart},  {SDL_SCANCODE_BACKSPACE, kSelect},
};

constexpr KeyBinding kModernKeys[] = {
    {SDL_SCANCODE_UP, kUp}, {SDL_SCANCODE_DOWN, kDown},
    {SDL_SCANCODE_LEFT, kLeft}, {SDL_SCANCODE_RIGHT, kRight},
    {SDL_SCANCODE_SPACE, kCross}, {SDL_SCANCODE_RETURN, kCross},
    {SDL_SCANCODE_E, kCircle}, {SDL_SCANCODE_R, kSquare}, {SDL_SCANCODE_Q, kTriangle},
    {SDL_SCANCODE_LSHIFT, kR2}, {SDL_SCANCODE_LCTRL, kL2},
    {SDL_SCANCODE_C, kL1}, {SDL_SCANCODE_V, kR1},
    {SDL_SCANCODE_P, kStart}, {SDL_SCANCODE_BACKSPACE, kSelect},
};
bool g_modern_keys = true;

struct PadBinding {
    SDL_GameControllerButton button;
    std::uint16_t mask;
};

constexpr PadBinding kPadButtons[] = {
    {SDL_CONTROLLER_BUTTON_A, kCross},          {SDL_CONTROLLER_BUTTON_B, kCircle},
    {SDL_CONTROLLER_BUTTON_X, kSquare},         {SDL_CONTROLLER_BUTTON_Y, kTriangle},
    {SDL_CONTROLLER_BUTTON_LEFTSHOULDER, kL1},  {SDL_CONTROLLER_BUTTON_RIGHTSHOULDER, kR1},
    {SDL_CONTROLLER_BUTTON_LEFTSTICK, kL3},     {SDL_CONTROLLER_BUTTON_RIGHTSTICK, kR3},
    {SDL_CONTROLLER_BUTTON_BACK, kSelect},      {SDL_CONTROLLER_BUTTON_START, kStart},
    {SDL_CONTROLLER_BUTTON_DPAD_UP, kUp},       {SDL_CONTROLLER_BUTTON_DPAD_DOWN, kDown},
    {SDL_CONTROLLER_BUTTON_DPAD_LEFT, kLeft},   {SDL_CONTROLLER_BUTTON_DPAD_RIGHT, kRight},
};

SDL_Window *g_window = nullptr;
SDL_Renderer *g_renderer = nullptr;
SDL_Texture *g_texture = nullptr;
SDL_AudioDeviceID g_audio = 0;
// the keyboard drives the first controller port along with the first game controller, a second one is player 2
SDL_GameController *g_pads[2] = {};
std::uint32_t g_tex_w = 0, g_tex_h = 0;
std::uint64_t g_last = 0;
std::vector<std::uint32_t> g_pixels;
bool g_gpu_present = false;

bool create_renderer() {
    g_renderer = SDL_CreateRenderer(g_window, -1, SDL_RENDERER_ACCELERATED);
    if (!g_renderer) g_renderer = SDL_CreateRenderer(g_window, -1, SDL_RENDERER_SOFTWARE);
    if (!g_renderer) {
        std::fprintf(stderr, "SDL: %s\n", SDL_GetError());
        return false;
    }
    return true;
}

bool attach_gpu() {
    if (std::getenv("PS2_SDL_RENDERER")) return false;
    SDL_SysWMinfo info;
    SDL_VERSION(&info.version);
    if (!SDL_GetWindowWMInfo(g_window, &info)) return false;
    ps2::WindowTarget target;
    int w = 0, h = 0;
    SDL_GetWindowSizeInPixels(g_window, &w, &h);
    target.width = static_cast<std::uint32_t>(w);
    target.height = static_cast<std::uint32_t>(h);
#ifdef __APPLE__
    if (info.subsystem == SDL_SYSWM_COCOA) {
        SDL_MetalView view = SDL_Metal_CreateView(g_window);
        if (!view) return false;
        target.kind = ps2::WindowTarget::Metal;
        target.surface = SDL_Metal_GetLayer(view);
        SDL_Metal_GetDrawableSize(g_window, &w, &h);
        target.width = static_cast<std::uint32_t>(w);
        target.height = static_cast<std::uint32_t>(h);
        return target.surface && ps2::attach_window(target);
    }
#endif
    switch (info.subsystem) {
#ifdef _WIN32
    case SDL_SYSWM_WINDOWS:
        target.kind = ps2::WindowTarget::Win32;
        target.display = info.info.win.hinstance;
        target.surface = info.info.win.window;
        break;
#endif
#if defined(SDL_VIDEO_DRIVER_X11)
    case SDL_SYSWM_X11:
        target.kind = ps2::WindowTarget::X11;
        target.display = info.info.x11.display;
        target.window = static_cast<std::uint64_t>(info.info.x11.window);
        break;
#endif
#if defined(SDL_VIDEO_DRIVER_WAYLAND)
    case SDL_SYSWM_WAYLAND:
        target.kind = ps2::WindowTarget::Wayland;
        target.display = info.info.wl.display;
        target.surface = info.info.wl.surface;
        break;
#endif
    default: return false;
    }
    return ps2::attach_window(target);
}

std::uint8_t axis(SDL_GameController *pad, SDL_GameControllerAxis a) {
    const int v = SDL_GameControllerGetAxis(pad, a);
    return static_cast<std::uint8_t>(std::clamp((v + 32768) >> 8, 0, 255));
}

void rumble(int port) {
    static double last_strong[2] = {};
    static bool last_weak[2] = {};
    static Uint32 sent[2] = {};
    SDL_GameController *pad = g_pads[port];
    if (!pad) return;
    const std::uint16_t motors = ps2::pad_rumble(port);
    const double strong = (motors >> 8) < 16 ? 0.0 : std::sqrt((motors >> 8) / 255.0);
    const bool weak = motors & 1u;
    const Uint32 now = SDL_GetTicks();
    if (std::fabs(strong - last_strong[port]) <= 0.08 && weak == last_weak[port] && (!(strong > 0.0 || weak) || now - sent[port] < 100)) return;
    last_strong[port] = strong;
    last_weak[port] = weak;
    sent[port] = now;
    SDL_GameControllerRumble(pad, static_cast<Uint16>(strong * 65535.0), weak ? 0xFFFF : 0, strong > 0.0 || weak ? 200 : 0);
}

// a new controller takes the first free port, the second one plugs in player 2
void open_pad(int device) {
    const SDL_JoystickID id = SDL_JoystickGetDeviceInstanceID(device);
    for (SDL_GameController *pad : g_pads)
        if (pad && SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(pad)) == id) return;
    for (int port = 0; port < 2; ++port)
        if (!g_pads[port]) {
            g_pads[port] = SDL_GameControllerOpen(device);
            return;
        }
}

void poll_port(int port) {
    static bool plugged[2] = {};
    SDL_GameController *pad = g_pads[port];
    if (port > 0 && plugged[port] != (pad != nullptr)) {
        plugged[port] = pad != nullptr;
        ps2::set_pad_connected(port, plugged[port]);
    }
    std::uint16_t pressed = 0;
    std::uint8_t l2 = 0xFF, r2 = 0xFF;
    std::uint8_t lx = 0x80, ly = 0x80, rx = 0x80, ry = 0x80;
    if (port == 0) {
        const Uint8 *keys = SDL_GetKeyboardState(nullptr);
        const auto apply_keys = [&](const auto &bindings) {
            for (const KeyBinding &b : bindings)
                if (keys[b.key]) pressed |= b.button;
        };
        if (g_modern_keys) apply_keys(kModernKeys);
        else apply_keys(kKeys);
        if (keys[g_modern_keys ? SDL_SCANCODE_A : SDL_SCANCODE_LEFT]) lx = 0x00;
        if (keys[g_modern_keys ? SDL_SCANCODE_D : SDL_SCANCODE_RIGHT]) lx = 0xFF;
        if (keys[g_modern_keys ? SDL_SCANCODE_W : SDL_SCANCODE_UP]) ly = 0x00;
        if (keys[g_modern_keys ? SDL_SCANCODE_S : SDL_SCANCODE_DOWN]) ly = 0xFF;
    }
    int mouse_x = 0, mouse_y = 0;
    if (port == 0 && SDL_GetRelativeMouseMode()) {
        const Uint32 mouse = SDL_GetRelativeMouseState(&mouse_x, &mouse_y);
        if (mouse & SDL_BUTTON_LMASK) pressed |= kSquare;
        if (mouse & SDL_BUTTON_RMASK) pressed |= kCircle;
        if (mouse & SDL_BUTTON_MMASK) pressed |= kL3;
        if (mouse & SDL_BUTTON_X1MASK) pressed |= kL1;
        if (mouse & SDL_BUTTON_X2MASK) pressed |= kR1;
    }
    if (pad) {
        for (const PadBinding &b : kPadButtons)
            if (SDL_GameControllerGetButton(pad, b.button)) pressed |= b.mask;
        const auto trigger = [&](SDL_GameControllerAxis a, std::uint16_t bit, std::uint8_t &pressure) {
            const int v = SDL_GameControllerGetAxis(pad, a);
            if (v <= 2000 || (pressed & bit)) return;
            pressed |= bit;
            pressure = static_cast<std::uint8_t>(std::max(1, v * 255 / 32767));
        };
        trigger(SDL_CONTROLLER_AXIS_TRIGGERLEFT, kL2, l2);
        trigger(SDL_CONTROLLER_AXIS_TRIGGERRIGHT, kR2, r2);
        if (lx == 0x80) lx = axis(pad, SDL_CONTROLLER_AXIS_LEFTX);
        if (ly == 0x80) ly = axis(pad, SDL_CONTROLLER_AXIS_LEFTY);
        rx = axis(pad, SDL_CONTROLLER_AXIS_RIGHTX);
        ry = axis(pad, SDL_CONTROLLER_AXIS_RIGHTY);
    }
    const auto mouse_axis = [](int delta) {
        return static_cast<std::uint8_t>(128 + std::clamp(delta, -32, 32) * 127 / 32);
    };
    if (mouse_x) rx = mouse_axis(mouse_x);
    if (mouse_y) ry = mouse_axis(mouse_y);
    rumble(port);
    static std::uint64_t last[2] = {~0ull, ~0ull};
    const std::uint64_t state = pressed | (static_cast<std::uint64_t>(rx) << 16) | (static_cast<std::uint64_t>(ry) << 24) | (static_cast<std::uint64_t>(lx) << 32) |
                                (static_cast<std::uint64_t>(ly) << 40) | (static_cast<std::uint64_t>(l2) << 48) | (static_cast<std::uint64_t>(r2) << 56);
    if (state == last[port]) return;
    last[port] = state;
    ps2::set_pad_pressure(8, l2, port);
    ps2::set_pad_pressure(9, r2, port);
    ps2::set_pad_buttons(pressed, port);
    ps2::set_pad_axis(0, rx, port);
    ps2::set_pad_axis(1, ry, port);
    ps2::set_pad_axis(2, lx, port);
    ps2::set_pad_axis(3, ly, port);
}

void poll() {
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_KEYDOWN && !e.key.repeat) {
            const auto key = e.key.keysym.scancode;
            if (key == SDL_SCANCODE_F9) g_modern_keys = !g_modern_keys;
            if (key == SDL_SCANCODE_F10) {
                if (SDL_SetRelativeMouseMode(SDL_GetRelativeMouseMode() ? SDL_FALSE : SDL_TRUE) != 0)
                    std::fprintf(stderr, "Mouse capture: %s\n", SDL_GetError());
            } else if (key == SDL_SCANCODE_ESCAPE) {
                SDL_SetRelativeMouseMode(SDL_FALSE);
            }
        }
        if (e.type == SDL_WINDOWEVENT && e.window.event == SDL_WINDOWEVENT_FOCUS_LOST)
            SDL_SetRelativeMouseMode(SDL_FALSE);
        if (e.type == SDL_QUIT) ps2::halt("window closed");
        if (e.type == SDL_KEYDOWN && e.key.keysym.scancode == SDL_SCANCODE_F11 && !e.key.repeat) {
            const bool full = SDL_GetWindowFlags(g_window) & SDL_WINDOW_FULLSCREEN;
            SDL_SetWindowFullscreen(g_window, full ? 0 : SDL_WINDOW_FULLSCREEN_DESKTOP);
            SDL_ShowCursor(full ? SDL_ENABLE : SDL_DISABLE);
        }
        if (e.type == SDL_WINDOWEVENT && e.window.event == SDL_WINDOWEVENT_SIZE_CHANGED && g_gpu_present) {
            int w = 0, h = 0;
#ifdef __APPLE__
            SDL_Metal_GetDrawableSize(g_window, &w, &h);
#else
            SDL_GetWindowSizeInPixels(g_window, &w, &h);
#endif
            ps2::resize_window(static_cast<std::uint32_t>(w), static_cast<std::uint32_t>(h));
        }
        if (e.type == SDL_CONTROLLERDEVICEADDED) open_pad(e.cdevice.which);
        if (e.type == SDL_CONTROLLERDEVICEREMOVED)
            for (SDL_GameController *&pad : g_pads)
                if (pad && e.cdevice.which == SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(pad))) {
                    SDL_GameControllerClose(pad);
                    pad = nullptr;
                }
    }
    poll_port(0);
    poll_port(1);
}

void show_pixels(const std::uint32_t *rgba, std::uint32_t w, std::uint32_t h) {
    if (w != g_tex_w || h != g_tex_h) {
        if (g_texture) SDL_DestroyTexture(g_texture);
        g_texture = SDL_CreateTexture(g_renderer, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STREAMING, static_cast<int>(w), static_cast<int>(h));
        SDL_RenderSetLogicalSize(g_renderer, static_cast<int>(w), static_cast<int>(w) * (ps2::g_options.widescreen ? 9 : 3) / (ps2::g_options.widescreen ? 16 : 4));
        g_tex_w = w;
        g_tex_h = h;
    }
    SDL_UpdateTexture(g_texture, nullptr, rgba, static_cast<int>(w * 4));
    SDL_RenderClear(g_renderer);
    SDL_RenderCopy(g_renderer, g_texture, nullptr, nullptr);
    SDL_RenderPresent(g_renderer);
}

void present() {
    if (g_gpu_present) {
        ps2::present_frame();
        return;
    }
    std::uint32_t w = 0, h = 0;
    if (ps2::display_frame(g_pixels, w, h)) show_pixels(g_pixels.data(), w, h);
}

constexpr Uint32 kAudioBytesPerMs = 48 * 4;

std::atomic<double> g_paced_ms{0.0};

struct PaceTimer {
    std::uint64_t start = SDL_GetPerformanceCounter();
    ~PaceTimer() {
        const double ms = static_cast<double>(SDL_GetPerformanceCounter() - start) * 1000.0 / static_cast<double>(SDL_GetPerformanceFrequency());
        g_paced_ms.store(g_paced_ms.load() + ms);
    }
};

void pace() {
    const PaceTimer timer;
    // Audio backpressure supplements the frame clock; it cannot replace it.
    // An empty or stalled audio queue must not unlock unlimited catch-up frames.
    if (g_audio) {
        const Uint32 audio_deadline = SDL_GetTicks() + 250;
        while (SDL_GetQueuedAudioSize(g_audio) > 80 * kAudioBytesPerMs &&
               SDL_GetTicks() < audio_deadline) {
            SDL_Delay(1);
        }
    }
    const std::uint64_t frequency = SDL_GetPerformanceFrequency();
    const double period_ms = ps2::g_options.pal ? 20.0 : 1000.0 / 59.94;
    const double now_ms = static_cast<double>(SDL_GetPerformanceCounter()) * 1000.0 /
                          static_cast<double>(frequency);
    const double previous_ms =
        g_last ? static_cast<double>(g_last) * 1000.0 / static_cast<double>(frequency) : 0.0;
    const double deadline_ms = ps2web::next_frame_deadline(now_ms, previous_ms, period_ms);
    g_last = static_cast<std::uint64_t>(deadline_ms * static_cast<double>(frequency) / 1000.0);
    if (deadline_ms > now_ms) {
        while (SDL_GetPerformanceCounter() < g_last) SDL_Delay(1);
    }
}

double process_cpu_seconds() {
#ifdef _WIN32
    FILETIME created{}, exited{}, kernel{}, user{};
    if (!GetProcessTimes(GetCurrentProcess(), &created, &exited, &kernel, &user)) return 0.0;
    const auto ticks = [](FILETIME time) {
        return (static_cast<std::uint64_t>(time.dwHighDateTime) << 32) | time.dwLowDateTime;
    };
    return static_cast<double>(ticks(kernel) + ticks(user)) / 1e7;
#else
    rusage usage{};
    getrusage(RUSAGE_SELF, &usage);
    return static_cast<double>(usage.ru_utime.tv_sec + usage.ru_stime.tv_sec) + static_cast<double>(usage.ru_utime.tv_usec + usage.ru_stime.tv_usec) / 1e6;
#endif
}

double resident_mb() {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS usage{};
    if (!GetProcessMemoryInfo(GetCurrentProcess(), &usage, sizeof usage)) return 0.0;
    return static_cast<double>(usage.WorkingSetSize) / (1024.0 * 1024.0);
#elif defined(__APPLE__)
    mach_task_basic_info_data_t task{};
    mach_msg_type_number_t count = MACH_TASK_BASIC_INFO_COUNT;
    if (task_info(mach_task_self(), MACH_TASK_BASIC_INFO, reinterpret_cast<task_info_t>(&task), &count) != KERN_SUCCESS) return 0.0;
    return static_cast<double>(task.resident_size) / (1024.0 * 1024.0);
#else
    long pages = 0, resident = 0;
    if (std::FILE *f = std::fopen("/proc/self/statm", "r")) {
        if (std::fscanf(f, "%ld %ld", &pages, &resident) != 2) resident = 0;
        std::fclose(f);
    }
    return static_cast<double>(resident) * static_cast<double>(sysconf(_SC_PAGESIZE)) / (1024.0 * 1024.0);
#endif
}

void show_speed() {
    static std::uint64_t start = 0, frames = 0;
    static double cpu_start = 0.0, gpu_start = 0.0, emu_start = 0.0, vu_start = 0.0, gs_start = 0.0;
    static std::uint64_t interpreted_start = 0;
    const auto emu_idle = [] { return ps2::thread_waited_ms(0) + g_paced_ms.load(); };
    const std::uint64_t now = SDL_GetPerformanceCounter();
    if (!start) {
        start = now;
        cpu_start = process_cpu_seconds();
        gpu_start = ps2::gpu_busy_ms();
        emu_start = emu_idle();
        vu_start = ps2::vu_thread_idle_ms();
        gs_start = ps2::thread_waited_ms(2);
        interpreted_start = ps2::vu1_interpreted_calls();
    }
    ++frames;
    const double seconds = static_cast<double>(now - start) / static_cast<double>(SDL_GetPerformanceFrequency());
    if (seconds < 1.0) return;
    const double cpu = process_cpu_seconds(), gpu = ps2::gpu_busy_ms(), emu = emu_idle(), vu = ps2::vu_thread_idle_ms(), gs = ps2::thread_waited_ms(2);
    const std::uint64_t interpreted = ps2::vu1_interpreted_calls();
    char title[256];
    const double queued = g_audio ? SDL_GetQueuedAudioSize(g_audio) / static_cast<double>(kAudioBytesPerMs) : 0.0;
    std::snprintf(title, sizeof title, "ps2-web-recomp  %.1f fps  CPU %.0f%%  GPU %.0f%%  idle emu %.0f%% vu %.0f%% gs %.0f%%  RAM %.0f MB  audio %.0f ms",
                  static_cast<double>(frames) / seconds, (cpu - cpu_start) / seconds * 100.0, (gpu - gpu_start) / (seconds * 10.0),
                  (emu - emu_start) / (seconds * 10.0), (vu - vu_start) / (seconds * 10.0), (gs - gs_start) / (seconds * 10.0), resident_mb(), queued);
    if (interpreted > interpreted_start) {
        const std::size_t used = std::strlen(title);
        std::snprintf(title + used, sizeof title - used, "  vu1 interpreted %.0f/s", static_cast<double>(interpreted - interpreted_start) / seconds);
    }
    SDL_SetWindowTitle(g_window, title);
    start = now;
    frames = 0;
    emu_start = emu;
    vu_start = vu;
    gs_start = gs;
    interpreted_start = interpreted;
    cpu_start = cpu;
    gpu_start = gpu;
}

void on_vblank() {
    show_speed();
    poll();
    present();
    pace();
}

void queue_audio(const std::int16_t *samples, std::size_t frames) {
    if (SDL_GetQueuedAudioSize(g_audio) > 500 * kAudioBytesPerMs) return;
    SDL_QueueAudio(g_audio, samples, static_cast<Uint32>(frames * 4));
}

}

bool open_window(bool fullscreen, std::string_view boot) {
    const auto separator = boot.find_last_of("/\\:");
    auto id = boot.substr(separator == std::string_view::npos ? 0 : separator + 1);
    id = id.substr(0, id.find(';'));
    if (!id.empty()) std::fprintf(stderr, "Disc ID %.*s\n", static_cast<int>(id.size()), id.data());
    g_modern_keys = true;
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_GAMECONTROLLER) != 0) {
        std::fprintf(stderr, "SDL: %s\n", SDL_GetError());
        return false;
    }
#ifdef __APPLE__
    const Uint32 metal = std::getenv("PS2_SDL_RENDERER") ? 0u : SDL_WINDOW_METAL;
#else
    const Uint32 metal = 0u;
#endif
    const Uint32 flags = SDL_WINDOW_RESIZABLE | SDL_WINDOW_ALLOW_HIGHDPI | metal | (fullscreen ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0u);
    g_window = SDL_CreateWindow("ps2-web-recomp", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, ps2::g_options.widescreen ? 1280 : 960, 720, flags);
    if (!g_window) {
        std::fprintf(stderr, "SDL: %s\n", SDL_GetError());
        return false;
    }
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "linear");
    SDL_AudioSpec want{}, have{};
    want.freq = 48000;
    want.format = AUDIO_S16SYS;
    want.channels = 2;
    want.samples = 1024;
    g_audio = SDL_OpenAudioDevice(nullptr, 0, &want, &have, 0);
    if (g_audio) {
        // Host mute (God): keep device paused unless PS2_UNMUTE=1. Runtime only.
        const bool unmute = std::getenv("PS2_UNMUTE") != nullptr;
        SDL_PauseAudioDevice(g_audio, unmute ? 0 : 1);
        if (unmute) ps2::set_audio_sink(queue_audio);
        else ps2::set_audio_sink([](const std::int16_t *, std::size_t) {});
        std::fprintf(stderr, "[window] audio %s\n", unmute ? "unmuted (PS2_UNMUTE)" : "muted (gain/output zero)");
    }
    for (int i = 0; i < SDL_NumJoysticks(); ++i)
        if (SDL_IsGameController(i)) open_pad(i);
    if (fullscreen) SDL_ShowCursor(SDL_DISABLE);
    return true;
}

int run_window(const std::function<int()> &emulate) {
    ps2::init_graphics();
    g_gpu_present = attach_gpu();
    std::fprintf(stderr, "[window] %s\n", g_gpu_present ? "presenting through WebGPU" : "presenting through SDL");
    if (!g_gpu_present && !create_renderer()) return 1;
    const bool threads = !std::getenv("PS2_ONE_THREAD") && !std::getenv("PS2_TIME") && ps2::g_options.frames_dir.empty();
    if (!threads) {
        ps2::g_options.on_vblank = on_vblank;
        return emulate();
    }
    ps2::g_options.on_vblank = [] {
        ps2::post_present();
        pace();
    };
    ps2::start_render_thread();
    if (!std::getenv("PS2_NO_VU_THREAD")) {
        ps2::start_vu_thread();
        std::thread(ps2::run_vu_thread).detach();
    }
    std::atomic<bool> done{false};
    int result = 0;
    std::thread emulation([&] {
        result = emulate();
        done.store(true);
        ps2::wake_render_thread();
    });
    const std::function<void(const std::uint32_t *, std::uint32_t, std::uint32_t)> copy = show_pixels, none;
    while (!done.load()) {
        poll();
        if (ps2::render_pending(g_gpu_present, g_gpu_present ? none : copy, show_speed, 8.0) == ps2::Rendered::idle) ps2::wait_render_work(4);
    }
    emulation.join();
    SDL_Quit();
    std::fflush(nullptr);
    std::_Exit(result);
}
