cmake_minimum_required(VERSION 3.20)
project(ps2-web-recomp CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PS2_GENERATED "" CACHE PATH "Folder with the C++ generated for a game")

set(PS2_WEB_ASYNC_MODE "asyncify" CACHE STRING "Browser async runtime: asyncify (compatible) or jspi (fast)")
set_property(CACHE PS2_WEB_ASYNC_MODE PROPERTY STRINGS asyncify jspi)
if(NOT PS2_WEB_ASYNC_MODE MATCHES "^(asyncify|jspi)$")
    message(FATAL_ERROR "PS2_WEB_ASYNC_MODE must be asyncify or jspi")
endif()

if(EMSCRIPTEN)
    if(PS2_WEB_ASYNC_MODE STREQUAL "asyncify")
        add_compile_definitions(PS2_COMPAT_TRAMPOLINE=1)
        set(PS2_TAIL_FLAG -mno-tail-call)
        set(PS2_EXCEPTION_FLAGS -fexceptions)
    else()
        set(PS2_TAIL_FLAG -mtail-call)
        set(PS2_EXCEPTION_FLAGS -fwasm-exceptions -sWASM_LEGACY_EXCEPTIONS=0)
    endif()
    add_compile_options(-msimd128 ${PS2_TAIL_FLAG} ${PS2_EXCEPTION_FLAGS} -pthread)
    add_link_options(-msimd128 ${PS2_TAIL_FLAG} ${PS2_EXCEPTION_FLAGS} -pthread)
endif()

if(NOT EMSCRIPTEN)
    add_executable(eerecomp
        recomp/main.cpp
        recomp/r5900.cpp
        recomp/elf.cpp
        recomp/analysis.cpp
        recomp/codegen.cpp
        recomp/snr2.cpp)
    target_compile_options(eerecomp PRIVATE -Wall -Wextra)

    add_executable(vujit_dump recomp/vujit_dump.cpp runtime/src/vu_jit.cpp)
    target_include_directories(vujit_dump PRIVATE runtime/include runtime/src)
    add_executable(vurecomp recomp/vurecomp.cpp)
    target_include_directories(vurecomp PRIVATE runtime/include)
    target_compile_options(vurecomp PRIVATE -Wall -Wextra)
endif()

add_library(ps2runtime STATIC
    runtime/src/memory.cpp
    runtime/src/dispatch.cpp
    runtime/src/system.cpp
    runtime/src/kernel.cpp
    runtime/src/hw.cpp
    runtime/src/cop.cpp
    runtime/src/disc.cpp
    runtime/src/dmac.cpp
    runtime/src/vif.cpp
    runtime/src/vu_micro.cpp
    runtime/src/vu_jit.cpp
    runtime/src/vu_jit_web.cpp
    runtime/src/ipu/ipu.cpp
    runtime/src/gs/gs.cpp
    runtime/src/gs/gif.cpp
    runtime/src/gs/queue.cpp
    runtime/src/gs/raster.cpp
    runtime/src/iop/cpu.cpp
    runtime/src/iop/kernel.cpp
    runtime/src/iop/libs.cpp
    runtime/src/iop/hw.cpp
    runtime/src/iop/spu2.cpp
    runtime/src/iop/sio2.cpp
    runtime/src/iop/io.cpp
    runtime/src/iop/cdvd.cpp
    runtime/src/iop/sif.cpp
    runtime/src/iop/igfileio.cpp
    runtime/src/iop/cdvdfsv.cpp)
target_include_directories(ps2runtime PUBLIC runtime/include)
target_compile_options(ps2runtime PRIVATE -Wall -Wextra)
if(EMSCRIPTEN)
    # Compile + link: USE_ZLIB pulls the port so zlib.h is on the include path.
    target_compile_options(ps2runtime PUBLIC -sUSE_ZLIB=1)
    target_link_options(ps2runtime PUBLIC -sUSE_ZLIB=1)
else()
    find_library(PS2_ZLIB z)
    if(PS2_ZLIB)
        target_link_libraries(ps2runtime PUBLIC ${PS2_ZLIB})
    else()
        target_link_libraries(ps2runtime PUBLIC z)
    endif()
endif()

set(PS2_WGPU_DIR "${CMAKE_SOURCE_DIR}/third_party/wgpu-native" CACHE PATH "wgpu-native release folder")
set(PS2_WGPU_IMPORT "${PS2_WGPU_DIR}/lib/libwgpu_native.dll.a")
if(EMSCRIPTEN OR (WIN32 AND EXISTS "${PS2_WGPU_IMPORT}") OR (NOT WIN32 AND EXISTS "${PS2_WGPU_DIR}/lib/libwgpu_native.a"))
    set(PS2_GS_WGSL "${CMAKE_BINARY_DIR}/gs_wgsl.cpp")
    add_custom_command(OUTPUT "${PS2_GS_WGSL}"
        COMMAND ${CMAKE_COMMAND} -DSRC=${CMAKE_SOURCE_DIR}/runtime/src/gs/gpu/gs.wgsl -DOUT=${PS2_GS_WGSL} -DNAME=kGsShader -P ${CMAKE_SOURCE_DIR}/cmake/embed.cmake
        DEPENDS runtime/src/gs/gpu/gs.wgsl cmake/embed.cmake)
    set(PS2_BLIT_WGSL "${CMAKE_BINARY_DIR}/blit_wgsl.cpp")
    add_custom_command(OUTPUT "${PS2_BLIT_WGSL}"
        COMMAND ${CMAKE_COMMAND} -DSRC=${CMAKE_SOURCE_DIR}/runtime/src/gs/gpu/blit.wgsl -DOUT=${PS2_BLIT_WGSL} -DNAME=kBlitShader -P ${CMAKE_SOURCE_DIR}/cmake/embed.cmake
        DEPENDS runtime/src/gs/gpu/blit.wgsl cmake/embed.cmake)
    target_sources(ps2runtime PRIVATE runtime/src/gs/gpu/gpu.cpp "${PS2_GS_WGSL}" "${PS2_BLIT_WGSL}")
    target_compile_definitions(ps2runtime PUBLIC PS2_GPU)
    if(EMSCRIPTEN)
        target_compile_options(ps2runtime PUBLIC --use-port=emdawnwebgpu)
        target_link_options(ps2runtime PUBLIC --use-port=emdawnwebgpu)
    else()
        target_include_directories(ps2runtime PRIVATE "${PS2_WGPU_DIR}/include")
        if(WIN32)
            target_link_libraries(ps2runtime PUBLIC "${PS2_WGPU_IMPORT}")
        else()
            target_link_libraries(ps2runtime PUBLIC "${PS2_WGPU_DIR}/lib/libwgpu_native.a" dl pthread m)
        endif()
        if(APPLE)
            target_link_libraries(ps2runtime PUBLIC "-framework Metal" "-framework QuartzCore" "-framework Foundation" "-framework CoreFoundation" "-framework IOKit" "-framework IOSurface" objc)
        endif()
    endif()
endif()

if(PS2_GENERATED)
    file(GLOB PS2_UNITS CONFIGURE_DEPENDS "${PS2_GENERATED}/*.cpp")
    add_library(ps2game STATIC ${PS2_UNITS})
    target_include_directories(ps2game PRIVATE "${PS2_GENERATED}")
    target_link_libraries(ps2game PUBLIC ps2runtime)
    target_compile_options(ps2game PRIVATE -Wno-unused-label -Wno-unused-variable)

    if(EMSCRIPTEN)
        set(PS2_WEB_ELF "" CACHE FILEPATH "Game executable preloaded as /game/core.elf")
        set(PS2_WEB_BOOT_FILE "" CACHE FILEPATH "Text file holding the argv[0] the game sees, preloaded as /game/boot.txt")
        set(PS2_WEB_PATCHES "" CACHE FILEPATH "Patch list the runtime writes into memory, preloaded as /game/patches.txt")
        add_executable(ps2web host/web.cpp)
        if(PS2_WEB_BOOT_FILE)
            target_link_options(ps2web PRIVATE "SHELL:--preload-file \"${PS2_WEB_BOOT_FILE}@/game/boot.txt\"")
        endif()
        if(PS2_WEB_PATCHES)
            target_link_options(ps2web PRIVATE "SHELL:--preload-file \"${PS2_WEB_PATCHES}@/game/patches.txt\"")
        endif()
        target_link_libraries(ps2web PRIVATE ps2game ps2runtime)
        # Keep GROWABLE_ARRAYBUFFERS=0 for the pinned SDK's broad compatibility.
        # Changing this setting affects heap representation/platform requirements.
        # Verify every WebGPU heap-view boundary before enabling growable views. Do not suppress the
        # pthread growth warning: it describes a real JS performance tradeoff.
        # Memory can grow; WebGPU requires fixed backing stores for uploads.
        if(PS2_WEB_ASYNC_MODE STREQUAL "asyncify")
            target_link_options(ps2web PRIVATE -sASYNCIFY=1 -sASYNCIFY_STACK_SIZE=1048576 -sDISABLE_EXCEPTION_CATCHING=0 -sASSERTIONS=1)
        else()
            target_link_options(ps2web PRIVATE -sJSPI=1)
        endif()
        set(PS2_SHELL "${CMAKE_BINARY_DIR}/ps2-shell.html")
        file(READ "${CMAKE_SOURCE_DIR}/web/shell.html" PS2_SHELL_CONTENT)
        string(REPLACE "__PS2_ASYNC_MODE__" "${PS2_WEB_ASYNC_MODE}" PS2_SHELL_CONTENT "${PS2_SHELL_CONTENT}")
        file(WRITE "${PS2_SHELL}" "${PS2_SHELL_CONTENT}")
        set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${CMAKE_SOURCE_DIR}/web/shell.html")
        # 384 MiB initial: GoW gameplay grew past 256 MiB and detached the audio SAB
        # (GROWABLE_ARRAYBUFFERS=0). Still allow growth for outliers; shell rebinds audio.
        # No --profiling-funcs: the name section cost showed up in heavy GoW combat.
        target_link_options(ps2web PRIVATE -sALLOW_MEMORY_GROWTH=1 -sGROWABLE_ARRAYBUFFERS=0 -sINITIAL_MEMORY=402653184 -sPTHREAD_POOL_SIZE=2 -sALLOW_TABLE_GROWTH=1 -lidbfs.js -sSTACK_SIZE=16777216 -sENVIRONMENT=web
            "SHELL:--pre-js \"${CMAKE_SOURCE_DIR}/web/gpu_upload_compat.js\""
            -sEXPORTED_FUNCTIONS=_main,_ps2web_diagnostics,_ps2web_pad,_ps2web_pad_connected,_ps2web_pressure,_ps2web_rumble,_ps2web_prompt_capture,_ps2web_cheat,_ps2web_resize,_ps2web_gpu_ms,_ps2web_frames,_ps2web_primitives,_ps2web_audio_ring,_ps2web_audio_queued_ms,_ps2web_idle_ms,_ps2web_vu_interpreted,_ps2web_quick_state,_ps2web_video_options,_ps2web_stream,_ps2web_set_fps_limit,_ps2web_fps_limit,_ps2web_set_vsync,_ps2web_vsync
            -sEXPORTED_RUNTIME_METHODS=callMain,addRunDependency,removeRunDependency,HEAPU8,ENV
            "SHELL:--shell-file \"${PS2_SHELL}\""
            "SHELL:--preload-file \"${PS2_WEB_ELF}@/game/core.elf\"")
        set_target_properties(ps2web PROPERTIES SUFFIX ".html" LINK_DEPENDS "${CMAKE_SOURCE_DIR}/web/shell.html;${CMAKE_SOURCE_DIR}/web/gpu_upload_compat.js")
        return()
    endif()

    add_executable(ps2run host/main.cpp)
    target_link_libraries(ps2run PRIVATE ps2game ps2runtime)
    if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
        target_sources(ps2run PRIVATE host/profile.cpp)
        target_compile_definitions(ps2run PRIVATE PS2_PROFILE)
    endif()
    if(WIN32)
        find_package(SDL2 REQUIRED CONFIG)
        target_compile_definitions(ps2run PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
        target_link_libraries(ps2run PRIVATE psapi)
    else()
        find_package(SDL2 QUIET)
    endif()
    if(SDL2_FOUND AND NOT EMSCRIPTEN)
        target_sources(ps2run PRIVATE host/window.cpp)
        target_compile_definitions(ps2run PRIVATE PS2_WINDOW)
        target_link_libraries(ps2run PRIVATE SDL2::SDL2)
    endif()
endif()

option(PS2_BUILD_TESTS "Build native IOP RPC regression executables" OFF)
if(PS2_BUILD_TESTS AND NOT EMSCRIPTEN)
    find_package(Threads REQUIRED)
    enable_testing()
    foreach(PS2_RPC_TEST iop_rpc_poll iop_rpc_snapshot)
        add_executable(${PS2_RPC_TEST} "tests/${PS2_RPC_TEST}.cpp")
        target_include_directories(${PS2_RPC_TEST} PRIVATE runtime/src)
        target_link_libraries(${PS2_RPC_TEST} PRIVATE ps2runtime Threads::Threads)
    endforeach()
    add_test(NAME iop_rpc_poll COMMAND iop_rpc_poll)
    set(PS2_NFS_RPC_CAPTURE "${CMAKE_SOURCE_DIR}/games/60c82f4a111da300ac23bbec85272788/explore_ram.bin")
    if(EXISTS "${PS2_NFS_RPC_CAPTURE}")
        add_test(NAME iop_rpc_snapshot COMMAND iop_rpc_snapshot "${PS2_NFS_RPC_CAPTURE}")
    endif()
endif()
