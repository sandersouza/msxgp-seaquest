#!/bin/bash
# Portable synthetic checks; original reference inputs are not required.
set -eu
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
cd "$script_dir/.."
if [ -n "$(git ls-files references/roms/)" ] || git ls-files --error-unmatch references/dissasm/seaquest-atari800.s >/dev/null 2>&1; then
    echo 'Original reference inputs must not be tracked in public Git.' >&2
    exit 1
fi
mkdir -p .tools
if [ ! -d .tools/sjasmplus ]; then
    git clone --depth 1 --branch v1.24.0 https://github.com/z00m128/sjasmplus.git .tools/sjasmplus
fi
if [ "$(git -C .tools/sjasmplus rev-parse HEAD)" != d379eeac9ad3857fb48fd3a3929175d0a56038ce ]; then
    echo 'Unexpected sjasmplus revision; preserving existing checkout.' >&2
    exit 1
fi
git -C .tools/sjasmplus diff --quiet HEAD
make -C .tools/sjasmplus -j2 USE_LUA=0
python3 -B -m unittest discover -s tests -v
python3 -B scripts/rom.py build
python3 -B scripts/rom.py check
python3 -B scripts/render_bench.py --build-only
