"""Compile the actual upload allocator with sanitizers; no GPU or game needed."""
from pathlib import Path
import subprocess
import os
import tempfile
root = Path(__file__).resolve().parents[1]
source = (root / 'runtime/src/gs/gpu/gpu.cpp').read_text()
arena = source[source.index('struct Arena {'):source.index('} g_arena;') + len('} g_arena;')]
append = source[source.index('std::uint32_t arena_append('):source.index('\nfloat u2f(')]
with tempfile.TemporaryDirectory() as temp:
    cpp = Path(temp) / 'arena.cpp'
    cpp.write_text('''#include <algorithm>
#include <memory>
#include <cstdint>
#include <cstring>
#include <cassert>
''' + arena + '\n' + append + '''
int main() {
    assert(arena_append(nullptr, 0) == 0);
    unsigned char data[7] = {1,2,3,4,5,6,7};
    for (int size = 1; size <= 7; ++size) {
        auto offset = arena_append(data, size);
        assert(std::memcmp(g_arena.data() + offset, data, size) == 0);
    }
    for (int i=0; i<1200000; ++i) arena_append(data, 7);
}
''')
    binary = Path(temp) / 'arena'
    subprocess.run(['g++', '-std=c++20', '-fsanitize=address,undefined', '-g', str(cpp), '-o', str(binary)], check=True)
    subprocess.run([binary], check=True, env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'})
print('PASS: empty, unaligned and growing WebGPU uploads under ASan/UBSan')
