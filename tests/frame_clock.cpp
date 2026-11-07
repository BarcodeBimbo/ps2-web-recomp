#include "../host/frame_clock.hpp"
#include <cassert>
#include <cmath>
int main() {
    using ps2web::next_frame_deadline;
    const double period = 1000.0 / 59.94;
    double now = 1000, deadline = 0;
    for (int i = 0; i < 10000; ++i) {
        deadline = next_frame_deadline(now, deadline, period);
        assert(deadline > now && deadline - now <= period + 0.000001);
        now = deadline;
    }
    assert(std::abs(next_frame_deadline(900000, deadline, 20)-900020)<0.000001);
    assert(next_frame_deadline(1000, 5000, 20)==1020);
    assert(next_frame_deadline(1000, 990, 20)==1010);
}
