#include "ps2/memory.hpp"
#include "ps2/cpu.hpp"
#include <cassert>
#include <stdexcept>
namespace ps2 { Cpu g_cpu; }
namespace ps2::hw {
std::uint32_t read32(std::uint32_t){return 0;}
std::uint64_t read64(std::uint32_t){return 0;}
void write32(std::uint32_t,std::uint32_t){}
void write64(std::uint32_t,std::uint64_t){}
void read128(std::uint32_t,ps2::Reg128&){}
void write128(std::uint32_t,const ps2::Reg128&){}
}
namespace ps2::vu { void code_changed(int){} }
int main(){
 using namespace ps2;
 const std::uint32_t ends[]={kRamSize, kScratchpadBase+kScratchpadSize,0x11001000u,0x11005000u,0x1100c000u,0x11010000u};
 for(auto end:ends){
  st8(end-1,17); assert(ld8(end-1)==17);
  bool rejected=false;try{st64(end-1,42);}catch(const std::out_of_range&){rejected=true;}assert(rejected);
  rejected=false;try{(void)ld32(end-1);}catch(const std::out_of_range&){rejected=true;}assert(rejected);
  Reg128 value{};st128(end-16,value);ld128(end-16,value);
  rejected=false;try{ld128(end-1,value);}catch(const std::out_of_range&){rejected=true;}assert(rejected);
 }
}
