#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EMSDK="${EMSDK:-$ROOT/tools/emsdk}"
EMSDK_VERSION="6.0.11"
EMSDK_BOOTSTRAP_REVISION="dd8e25632640cfc1fb570c7fa4cc374e8a5e5a72" # immutable emsdk 6.0.11 release commit
web=1
[ "${1:-}" = "--native-only" ] && web=0

if [ "$web" = 1 ] && [ ! -f "$EMSDK/emsdk_env.sh" ]; then
  echo "== installing the Emscripten SDK $EMSDK_VERSION into $EMSDK"
  mkdir -p "$(dirname "$EMSDK")"
  rm -rf "$EMSDK"
  git init "$EMSDK"
  git -C "$EMSDK" remote add origin https://github.com/emscripten-core/emsdk.git
  git -C "$EMSDK" fetch --depth 1 origin "$EMSDK_BOOTSTRAP_REVISION"
  git -C "$EMSDK" checkout --detach FETCH_HEAD
  "$EMSDK/emsdk" install "$EMSDK_VERSION"
  "$EMSDK/emsdk" activate "$EMSDK_VERSION"
fi

if [ ! -f "$ROOT/third_party/wgpu-native/lib/libwgpu_native.a" ]; then
  echo "== fetching wgpu-native for the native runner"
  "$ROOT/scripts/fetch_wgpu.sh"
fi

. "$ROOT/scripts/cxx.sh"
cmake -S "$ROOT" -B "$ROOT/build/tools" -G Ninja -DCMAKE_BUILD_TYPE=Release "${cxx_flags[@]}" > /dev/null
ninja -C "$ROOT/build/tools" eerecomp vurecomp
echo "== ready"
