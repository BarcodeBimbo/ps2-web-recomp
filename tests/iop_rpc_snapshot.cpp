// Link against ps2runtime; include the actual SIF implementation to inspect its
// packet queues without adding production-only test hooks.
#ifndef PS2_SIF_IMPLEMENTATION
#define PS2_SIF_IMPLEMENTATION "../runtime/src/iop/sif.cpp"
#endif
#include PS2_SIF_IMPLEMENTATION
#include <cassert>
#include <iostream>
#include <fstream>
#include <iterator>
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
int main(int argc,char **argv) {
    if(argc!=2){std::cerr<<"usage: iop_rpc_snapshot <NFS exploration RAM dump>\n";return 2;}
    std::ifstream in(argv[1],std::ios::binary);
    std::vector<std::uint8_t> raw((std::istreambuf_iterator<char>(in)),{});
    if(raw.size()!=37748736){std::cerr<<"Expected EE+IOP+SPU2 snapshot\n";return 2;}
    iop::reset();
    std::memcpy(ps2::g_ram,raw.data(),32u<<20);
    std::memcpy(iop::ram_ptr(0x20000),raw.data()+(32u<<20)+0x20000,iop::kRamSize-0x20000);
    // Rebind old HLE import IDs through the current runtime's IRX linker.
    for(unsigned table=0x20000;table+20<iop::kRamSize;table+=4){
        if(iop::ram32(table)!=0x41e00000)continue;
        for(unsigned stub=table+20;stub+8<iop::kRamSize;stub+=8){
            const auto op=iop::ram32(stub),slot=iop::ram32(stub+4);
            if(op==0 && slot==0)break;
            if(op>>26!=iop::kHleOpcode || (slot&0xffff0000)!=0x24000000)continue;
            auto fixture=imports();
            std::memcpy(fixture.data()+0x10c,iop::ram_ptr(table+12),8);
            std::memcpy(fixture.data()+0x118,&slot,4);
            std::memset(fixture.data()+0x11c,0,0x100-28);
            const auto module=iop::link_module(fixture,"buffer");assert(module>0);
            const auto base=ik::modules().at(module).base;
            iop::set_ram32(stub,iop::ram32(base+20));
            ik::free(base);
        }
    }
    constexpr unsigned q=0xa1160,sd=0xa1178,buf=0xa0960;
    int tid=ik::create_thread(0x93554,0x1000,15,0,0,0);ik::start_thread(tid,0);
    auto *thread=ik::thread(tid);auto &c=thread->context;
    c.r[28]=0xa2720;c.r[29]=0x1f0000;c.r[17]=c.r[29]+0x1c;
    c.r[19]=0x9a780;c.r[21]=0x9a7a0;c.r[20]=0x9ab28;c.r[16]=0x9ad68;
    c.r[23]=c.r[22]=c.r[30]=0x90000;
    for(unsigned k=0;k<4;++k)iop::write32(c.r[29]+0x34+4*k,c.r[29]+0x24+4*k);
    // The capture stopped immediately after the driver's SleepThread call.
    thread->status=ik::kWait;thread->wait=ik::kWaitSleep;
    sif::g_queue_threads[q]=tid;iop::write32(q+4,0);
    sif::Server server;server.sd=sd;server.func=0x930a0;server.buf=buf;server.queue=q;
    sif::g_servers[0x534e44]=server;
    sif::Call request{};std::memcpy(&request,ps2::g_ram+0x5cde40,sizeof request);
    assert(request.rpc_number==0 && request.send_size==20 && request.server_data==(0x534e44^0xacacacac));
    std::vector<std::uint8_t> data(ps2::g_ram+0x5bf400,ps2::g_ram+0x5bf400+32);
    sif::g_requests[q].push_back(sif::Request{request,20,data});
    sif::deliver_request(q);
    if(thread->status!=ik::kReady){std::cerr<<"FAIL: captured sound worker remains asleep\n";return 1;}
    for(unsigned n=0;n<100000;++n){
        iop::run(800);
        if(sif::g_requests[q].empty() && sif::g_held_calls.empty()){
            bool replied=false;
            for(const auto &packet:sif::g_outgoing){
                if(packet.size()<sizeof(sif::Rend))continue;
                sif::Rend end{};std::memcpy(&end,packet.data(),sizeof end);
                if(end.header.cid==sif::kCmdRend && end.command==0x8000000a && end.client_data==request.client_data)replied=true;
            }
            if(!replied){std::cerr<<"FAIL: callback did not produce the matching RPC end packet\n";return 1;}
            std::cout<<"PASS: captured NFS sound RPC fn0 executed and replied after "<<n+1<<" slices\n";
            std::cout<<"worker pc=0x"<<std::hex<<(ik::current()?iop::g_cpu.pc:thread->context.pc)<<"\n";
            return 0;
        }
        if(thread->status==ik::kDormant)break;
    }
    sif::dump();iop::dump();std::cerr<<"FAIL: captured RPC did not complete\n";return 1;
}
