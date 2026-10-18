#!/usr/bin/env bash
# Build the two pinned third-party renderers used by AUDIO-1B, outside version control.
#
#   tools/audio1b_build_renderers.sh [DEST]      (default: build/audio1/renderers, git-ignored)
#
# Needs git, cmake, a C/C++ toolchain and python3. Nothing built here is committed or shipped.
# Licences (checked in AUDIO-1B): Game_Music_Emu LGPL-2.1; libvgm has no top-level licence file at the
# pinned commit - its SN76489 core sn76496.c states BSD-3-Clause (Nicola Salmoria), sn76489.c
# (Maxim) states none. Use as local validation/evaluation tools only until that is resolved.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$ROOT/build/audio1/renderers}"
GME_REPO=https://github.com/libgme/game-music-emu
GME_COMMIT=9e23d10f9fd2a6a2f33b10912dd8dc7153258995      # tag 0.6.5
VGM_REPO=https://github.com/ValleyBell/libvgm
VGM_COMMIT=a6eed945ecf4e5a25cf82004779c6f7e4fd5c319

mkdir -p "$DEST"
cd "$DEST"

fetch() {  # repo commit dir
  if [ ! -d "$3/.git" ]; then git init -q "$3"; git -C "$3" remote add origin "$1"; fi
  git -C "$3" fetch -q --depth 1 origin "$2"
  git -C "$3" checkout -q --detach FETCH_HEAD
  [ "$(git -C "$3" rev-parse HEAD)" = "$2" ] || { echo "pin mismatch in $3" >&2; exit 1; }
}

fetch "$GME_REPO" "$GME_COMMIT" gme-src
cmake -S gme-src -B gme-build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
      -DENABLE_UBSAN=OFF -DGME_ZLIB=OFF -DGME_YM2612_EMU=Nuked >/dev/null
cmake --build gme-build -j4 >/dev/null

fetch "$VGM_REPO" "$VGM_COMMIT" libvgm-src
# Build-only patch: let an environment variable choose the SN76489 core (MAME or MAXM). vgm2wav's own
# source marks this spot ("example for setting cores"); the original file is left untouched in git.
python3 - <<'PY'
from pathlib import Path
p = Path('libvgm-src/vgm2wav.cpp')
s = p.read_text()
marker = '    // set_core(plrEngine,DEVID_YM2612,FCC_NUKE);'
patch = marker + '''
    if (getenv("VGM_SN_CORE")) {
        const char* c = getenv("VGM_SN_CORE");
        set_core(plrEngine, DEVID_SN76496, !strcmp(c, "MAXM") ? FCC_MAXM : FCC_MAME);
    }'''
if 'VGM_SN_CORE' not in s:
    assert marker in s
    p.write_text(s.replace(marker, patch))
PY
cmake -S libvgm-src -B libvgm-build -DCMAKE_BUILD_TYPE=Release -DBUILD_PLAYER=OFF -DBUILD_LIBAUDIO=OFF \
      -DBUILD_TESTS=OFF -DUSE_SANITIZERS=OFF -DBUILD_VGM2WAV=ON >/dev/null
cmake --build libvgm-build -j4 --target vgm2wav >/dev/null

echo "export AUDIO1B_GME_LIB=$DEST/gme-build/gme/libgme.so"
echo "export AUDIO1B_VGM2WAV=$DEST/libvgm-build/bin/vgm2wav"
