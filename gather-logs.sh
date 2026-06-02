#!/bin/bash
set -e

BASE_DIR="$( realpath -sm  "$( dirname "${BASH_SOURCE[0]}" )")"

cd "$BASE_DIR"

source "$BASE_DIR/scripts/config.sh"

for i in $(seq 1 "$MACHINE_COUNT"); do
  ssh w$i "cd \"$BASE_DIR\"; rm -rf logs.zip; zip -r logs.zip logs/"
  scp w$i:"$BASE_DIR/logs.zip" w$i-logs.zip
  unzip -o w$i-logs.zip
  rm -rf w$i-logs.zip
done
