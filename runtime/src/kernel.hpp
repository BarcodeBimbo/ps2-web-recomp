#pragma once

#include "ps2/cpu.hpp"

#include <cstdint>
#include <functional>

namespace ps2::state {
class Stream;
}

namespace ps2::kernel {

void state(ps2::state::Stream &s);
std::function<void()> alarm_action(int id);

void reset();
void start_main_thread(std::uint32_t entry, std::uint32_t gp, std::uint32_t argc, std::uint32_t argv);
void handle_syscall(Cpu &c, std::uint32_t pc);
void service(Cpu &c);
bool must_unwind();
bool in_handler();
bool interruptible();
int current_thread();
void on_vblank_start();
void on_hblank();
void wake_idle();
void dump();
// Host-side SignalSema for HLE that finishes work while the EE is blocked
// (Alchemy GOB/STBL pumps waiting on a temp sema after FINISH).
bool host_signal_sema(int id);
// Run a guest EE function on a temporary handler stack (HLE helpers).
std::uint32_t host_call(std::uint32_t address, std::uint32_t a0 = 0, std::uint32_t gp = 0,
                        std::uint32_t max_steps = 500000u, std::uint32_t a1 = 0,
                        std::uint32_t a2 = 0, std::uint32_t a3 = 0);
// Like host_call but also seeds t0/t1/t2 (r8/r9/r10) before entry.
std::uint32_t host_call_t(std::uint32_t address, std::uint32_t a0, std::uint32_t a1, std::uint32_t a2,
                          std::uint32_t a3, std::uint32_t t0, std::uint32_t t1, std::uint32_t t2,
                          std::uint32_t gp, std::uint32_t max_steps = 500000u);
// Request the active capped host_call to unwind cleanly (e.g. after a host AV).
void abort_host_call();
// After a longjmp out of host_call (SEH), restore handler/context flags.
void host_call_cleanup();

}
