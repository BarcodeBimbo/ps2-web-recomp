#include "gs/queue.hpp"
#include <cassert>
#include <cstring>
#include <thread>
#include <stdexcept>
#include <vector>
using namespace ps2::gs::queue;
int main() {
    Ring q;
    bool rejected=false;
    try {q.start(17);} catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected); q.start(256);
    rejected=false;
    try {q.post(kGif,0,0,nullptr,257);} catch(const std::invalid_argument&) {rejected=true;}
    assert(rejected);
    constexpr unsigned count=20000;
    std::thread consumer([&]{
        for(unsigned i=0;i<count;++i) {
            Header h{}; const std::uint8_t *data=nullptr;
            while(!q.peek(h,data)) q.wait_for_work(-1);
            assert(h.arg0==i && h.bytes==((i%2)?240:16));
            for(unsigned k=0;k<h.bytes;++k) assert(data[k]==(i%251));
            q.pop(h);
        }
    });
    for(unsigned i=0;i<count;++i) {
        std::vector<std::uint8_t> data((i%2)?240:16,i%251);
        q.post(kGif,i,0,data.data(),data.size());
    }
    consumer.join();
}
