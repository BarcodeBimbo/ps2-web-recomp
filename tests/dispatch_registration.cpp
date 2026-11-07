#include "ps2/generated.hpp"
#include "ps2/system.hpp"
#include <cassert>
namespace ps2 {
Options g_options;
alignas(64) std::uint8_t g_ram[kRamSize+64]{};
alignas(64) std::uint8_t g_spr[kScratchpadSize]{};
std::uint32_t slow_ld32(std::uint32_t){return 0;}
void halt(const std::string&){}
}
void code(ps2::Cpu&,std::uint32_t,std::uint32_t){}
int main(){
 std::uint16_t entries[4]={1,0,0,0};
 ps2::UnitInfo unit{0x100000,16,code,entries};
 ps2::register_units(&unit,1);assert(ps2::has_code(0x100000));assert(!ps2::has_code(0x100001));assert(!ps2::has_code(0x100010));
 ps2::register_units(nullptr,0);assert(!ps2::has_code(0x100000));
 ps2::register_modules(nullptr,0);
}
