#pragma once

namespace ps2web {
// Maintain a wall-clock limit even when the audio device has no samples.
// Discard a stale deadline after suspension instead of running catch-up frames.
inline double next_frame_deadline(double now, double previous, double period) {
    if (previous == 0.0 || now - previous > 200.0 || previous - now > period)
        previous = now;
    return previous + period;
}
}
