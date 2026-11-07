// Link against ps2runtime; include the actual SIF implementation to inspect its
// packet queues without adding production-only test hooks.
#ifndef PS2_SIF_IMPLEMENTATION
#define PS2_SIF_IMPLEMENTATION "../runtime/src/iop/sif.cpp"
#endif
#include PS2_SIF_IMPLEMENTATION
#include <cassert>
#include <iostream>
using namespace ps2;
namespace ik = ps2::iop::kernel;

static std::vector<std::uint8_t> imports() {
    std::vector<std::uint8_t> data(0x200);
    auto word=[&](unsigned at,unsigned value){std::memcpy(data.data()+at,&value,4);};
    auto half=[&](unsigned at,std::uint16_t value){std::memcpy(data.data()+at,&value,2);};
    std::memcpy(data.data(),"\177ELF\1\1\1",7);
    half(16,0xff80);half(18,8);word(20,1);word(28,52);half(40,52);half(42,32);half(44,2);
    word(52,0x70000080);word(56,0x80);
    word(84,1);word(88,0x100);word(100,0x100);word(104,0x200);
    word(0x8c,0x100);word(0x94,0x100);std::memcpy(data.data()+0x9a,"rpc_fixture",12);
    word(0x100,0x41e00000);word(0x108,0x101);std::memcpy(data.data()+0x10c,"sifcmd",6);
    unsigned k=0;for(unsigned index:{17,19,20,21,22}){word(0x114+k*8,0x03e00008);word(0x118+k*8,0x24000000|index);++k;}
    return data;
}
struct MemoryState : ps2::state::Stream {
    std::vector<std::uint8_t> &data;
    std::size_t position=0;
    MemoryState(bool write, std::vector<std::uint8_t> &buffer) : Stream(write), data(buffer) {}
    void bytes(void *out,std::size_t n) override {
        if(saving()){const auto *p=static_cast<const std::uint8_t *>(out);data.insert(data.end(),p,p+n);}
        else {if(n>data.size()-position)throw std::runtime_error("test state truncated");std::memcpy(out,data.data()+position,n);position+=n;}
    }
};
int main() {
    iop::reset();
    const int module=iop::link_module(imports(),"buffer");assert(module>0);
    const auto base=ik::modules().at(module).base;
    auto invoke=[&](iop::Cpu &c,unsigned slot){
        const auto opcode=iop::read32(base+20+slot*8);assert(opcode>>26==iop::kHleOpcode);
        iop::call_hle(c,opcode&0x03ffffff);
    };
    constexpr unsigned q=0x180000, sd=0x180080, buf=0x180100, recv=0x100000;
    unsigned stage=0, completed=0, handler_calls=0, loop=0;
    bool block_handler=false;
    const unsigned handler=ik::hle_stub([&](iop::Cpu &c){
        ++handler_calls;
        iop::write32(buf,c.r[4]);
        // A valid o32 callback may use its caller's 16-byte argument-home area.
        for(unsigned k=0;k<16;k+=4)iop::write32(c.r[29]+k,0xabababab);
        c.r[2]=buf;
        if(block_handler){block_handler=false;ik::block(c,ik::kWaitSleep,0);}
    });
    loop=ik::hle_stub([&](iop::Cpu &c){
        c.pc=loop;c.npc=loop+4;
        if(stage==1){++completed;stage=0;}
        c.r[4]=q;invoke(c,2);
        if(!c.r[2]){ik::block(c,ik::kWaitSleep,0);return;}
        const unsigned request=c.r[2];stage=1;c.r[4]=request;c.r[31]=loop;
        invoke(c,3);
    });
    const int tid=ik::create_thread(loop,0x2000,40,0,0,0);ik::start_thread(tid,0);
    auto *thread=ik::thread(tid);const unsigned original_sp=thread->context.r[29];
    iop::Cpu setup{};setup.r[29]=0x181000;
    setup.r[4]=q;setup.r[5]=tid;invoke(setup,1);
    setup.r[4]=sd;setup.r[5]=0x534e44;setup.r[6]=handler;setup.r[7]=buf;
    iop::write32(setup.r[29]+24,q);invoke(setup,0);
    iop::run(800);assert(thread->status==ik::kWait && thread->wait==ik::kWaitSleep);
    auto send=[&](unsigned fn){
        sif::Call call{};call.server_data=0x534e44^0xacacacac;call.rpc_number=fn;call.recv=recv;call.recv_size=4;
        sif::g_requests[q].push_back(sif::Request{call,0,{}});sif::deliver_request(q);
    };
    send(7);
    if(thread->status!=ik::kReady){std::cerr<<"FAIL: queued RPC did not wake a sleeping polling worker\n";return 1;}
    iop::run(8000);
    assert(completed==1 && handler_calls==1);assert(ps2::load<std::uint32_t>(ps2::g_ram+recv)==7);
    assert(thread->context.r[29]==original_sp && thread->rpc_return==0);
    // A callback can sleep and finish later without losing the polling continuation.
    block_handler=true;send(8);iop::run(8000);
    assert(completed==1 && handler_calls==2 && thread->rpc_return==loop);
#ifndef PS2_RPC_BASELINE
    std::vector<std::uint8_t> saved;
    MemoryState save(true,saved);save.set_version(7);ik::state(save);sif::state(save);save.bytes(iop::ram_ptr(0),iop::kRamSize);
    thread->rpc_return=0;sif::g_held_calls.clear();
    MemoryState restore(false,saved);restore.set_version(7);ik::state(restore);sif::state(restore);restore.bytes(iop::ram_ptr(0),iop::kRamSize);
    thread=ik::thread(tid);assert(thread->rpc_return==loop && !sif::g_held_calls.empty());
#endif
    ik::wake(*thread,buf);ik::reschedule();iop::run(8000);
    assert(completed==2 && thread->context.r[29]==original_sp);
    assert(ps2::load<std::uint32_t>(ps2::g_ram+recv)==8);
    // Delivery between a poll and SleepThread must preserve a wake credit.
    thread->status=ik::kReady;iop::write32(q+4,0);const int credits=thread->wakeups;
    sif::deliver_request(q);assert(thread->wakeups==credits+1);
    thread->status=ik::kWait;thread->wait=ik::kWaitSema;thread->wait_id=99;
    sif::deliver_request(q);assert(thread->status==ik::kWait && thread->wait==ik::kWaitSema);
#ifndef PS2_RPC_BASELINE
    std::vector<std::uint8_t> legacy;
    MemoryState old_save(true,legacy);old_save.set_version(6);ik::state(old_save);
    thread->rpc_return=123;
    MemoryState old_load(false,legacy);old_load.set_version(6);ik::state(old_load);
    thread=ik::thread(tid);assert(thread->rpc_return==0);
#endif
    // Keep the existing sceSifRpcLoop path working with the same reply logic.
    constexpr unsigned q2=q+0x200,sd2=sd+0x200;
    const unsigned normal=ik::hle_stub([&](iop::Cpu &c){c.r[4]=q2;invoke(c,4);});
    const int tid2=ik::create_thread(normal,0x1000,30,0,0,0);ik::start_thread(tid2,0);
    const auto normal_sp=ik::thread(tid2)->context.r[29];
    setup.r[4]=q2;setup.r[5]=tid2;invoke(setup,1);
    setup.r[4]=sd2;setup.r[5]=0x534e45;setup.r[6]=handler;setup.r[7]=buf;
    iop::write32(setup.r[29]+24,q2);invoke(setup,0);
    iop::run(800);assert(ik::thread(tid2)->wait==ik::kWaitRpc);
    sif::Call normal_call{};normal_call.server_data=0x534e45^0xacacacac;normal_call.rpc_number=9;normal_call.recv=recv;normal_call.recv_size=4;
    sif::g_requests[q2].push_back(sif::Request{normal_call,0,{}});sif::deliver_request(q2);iop::run(8000);
    assert(handler_calls==3 && ps2::load<std::uint32_t>(ps2::g_ram+recv)==9);
    assert(ik::thread(tid2)->context.r[29]==normal_sp && ik::thread(tid2)->wait==ik::kWaitRpc);
    // Malformed RPC extents must fail before touching adjacent memory.
#ifndef PS2_RPC_BASELINE
    bool rejected=false;try{sif::iop_span(iop::kRamSize-2,4);}catch(const std::out_of_range&){rejected=true;}assert(rejected);
    sif::Call huge{};huge.server_data=0x534e44^0xacacacac;huge.send_size=0xfffffff8;
    rejected=false;try{sif::call(reinterpret_cast<const std::uint8_t *>(&huge));}catch(const std::out_of_range&){rejected=true;}assert(rejected);
#endif
    std::cout<<"PASS: custom polling RPC wake, imports 20/21, callback/reply, blocking continuation, stack restoration and wake race\n";
}
