#include "ps2/generated.hpp"
#include "ps2/system.hpp"
#include <cassert>
namespace ps2 {
Options g_options;
alignas(64) std::uint8_t g_ram[kRamSize+64]{};
alignas(64) std::uint8_t g_spr[kScratchpadSize]{};
std::uint32_t slow_ld32(std::uint32_t){return 0;}
void halt(const std::string&){assert(false);}
}
using namespace ps2;
void second(Cpu&,std::uint32_t,std::uint32_t);
void first(Cpu& c,std::uint32_t,std::uint32_t depth){
 if(++c.r[2].w[0]>=250000){c.pc=kIdle;return;}
 PS2_TAIL_TRANSFER(c,0x100010u,second,1u,depth);
}
void second(Cpu& c,std::uint32_t,std::uint32_t depth){PS2_TAIL_TRANSFER(c,0x100000u,first,1u,depth);}
void caller(Cpu& c,std::uint32_t entry,std::uint32_t depth){
 if(entry==1){c.r[31].w[0]=0x100024;first(c,1,depth+1);if(c.pc!=0x100024)return;}
 c.r[3].w[0]++;c.pc=kIdle;
}
int main(){
 const std::uint16_t entries[]={1,0,0,0},returns[]={1,2,0,0};
 const UnitInfo units[]={{0x100000,16,first,entries},{0x100010,16,second,entries},{0x100020,16,caller,returns}};
 register_units(units,3);Cpu c{};c.pc=0x100000;
 while(c.pc!=kIdle)dispatch(c,0,0);
 assert(c.r[2].w[0]==250000);
 // Nested generated calls can hand a tail transfer back to the outer dispatcher.
 c={};c.pc=0x100020;dispatch(c,0,0);assert(c.pc==0x100010);assert(c.r[3].w[0]==0);
 // A return PC is independently dispatchable after such an unwind.
 c.pc=0x100024;dispatch(c,0,0);assert(c.r[3].w[0]==1);assert(c.pc==kIdle);
}
