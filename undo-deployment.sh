#!/bin/bash
set -e

BASE_DIR="$( realpath -sm  "$( dirname "${BASH_SOURCE[0]}" )")"

source "$BASE_DIR/scripts/config.sh"

for i in $(seq 1 "$MACHINE_COUNT"); do
  ssh w$i "rm -rf \"$BASE_DIR\""
done
