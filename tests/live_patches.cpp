#include "ps2/live_patches.hpp"
#include "ps2/state.hpp"
#include <cassert>
#include <thread>
#include <vector>
#include <atomic>
int main() {
    ps2::LivePatches patches;
    assert(!patches.publish(128,0,4,0,true));
    assert(!patches.publish(0,0x01ffffff,4,0,true));
    assert(!patches.publish(0,0,3,0,true));
    assert(!patches.publish(0,0x10000000,4,0,true));
    assert(patches.publish(0,0x1000,4,0x12345678,true));
    assert(!patches.publish(0,0x1000,4,0,true));
    unsigned writes=0;
    patches.apply([&](auto address, auto size, auto value){assert(address==0x1000&&size==4&&value==0x12345678);++writes;});
    assert(writes==1);
    assert(patches.publish(0,0,0,0,false));
    patches.apply([&](auto,auto,auto){assert(false);});
    std::atomic<bool> done{false};
    std::thread producer([&]{for(unsigned i=0;i<100000;++i)while(!patches.publish(1,0x1000,4,i,true))std::this_thread::yield();done.store(true);});
    while(!done.load())patches.apply([](auto address,auto size,auto value){assert(address==0x1000&&size==4&&value<100000);});
    producer.join();
    patches.apply([](auto,auto,auto){});
    const std::uint8_t bad[]={255,255,255,255};
    ps2::state::Reader reader(bad,sizeof bad);std::vector<std::uint64_t> values;
    try {reader.vec(values);assert(false);} catch(const std::runtime_error&) {}
}
