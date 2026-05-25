#!/bin/bash
set -e

SCRIPT_DIR="$( realpath -sm  "$( dirname "${BASH_SOURCE[0]}" )")"

cd "$SCRIPT_DIR"

rm -rf bin.zip
zip -Dj bin.zip chimera/chimera/build/bin/* chimera/{swarm-kv,fusee}/build/bin/*

echo "Success: bin/bin.zip created with swarmkv, raw_memory, chimera, and fusee."

