#!/bin/bash

set -u

SCRIPT_DIR="$( realpath -sm "$( dirname "${BASH_SOURCE[0]}" )" )"
source "$SCRIPT_DIR"/config.sh

BINARY=$1
FOLDER=$2
WORKLOAD=$3
NBSERVERS=$4
NBCLIENTS=$5
ARGS="-y "$YCSB_BIN" -w "$WORKLOAD_DIR/$WORKLOAD" -s $NBSERVERS -c $NBCLIENTS ${@:6}"

echo "Running exp $FOLDER: $BINARY -w $WORKLOAD -s $NBSERVERS -c $NBCLIENTS ${@:6}"
for retry in $(seq 1 15); do
  if [ $retry -gt 1 ]; then
    echo "Retrying..."
  fi

  "$SCRIPT_DIR"/setup-all-tmux.sh

  echo -n "Starting"

  # Trigger our newly fixed, aggressive port-cleaning script
  "$SCRIPT_DIR"/remote-memc.sh $REGISTRY_MACHINE
  
  # CRITICAL: Allow time for the tmux window to initialize and bind port 11211
  sleep 1.5

  for s in $(seq 1 $NBSERVERS); do
    echo -n "."
    MACHINE=machine$(($FIRST_SERVER + ($s - 1) % $SERVER_MACHINES))
    CORE=$(((($s - 1) / $SERVER_MACHINES) * 2))
    "$SCRIPT_DIR"/remote-invoker.sh $MACHINE "$FOLDER" server$s $CORE "$BIN_DIR/$BINARY" -i $s $ARGS
  done

  echo -n " (Waiting for servers to initialize)..."
  sleep 1.5

  for c in $(seq 1 $NBCLIENTS); do
    echo -n "."
    MACHINE=machine$(($FIRST_CLIENT + ($c - 1) % $CLIENT_MACHINES))
    CORE=$(((($c - 1) / $CLIENT_MACHINES) * 2))
    i=$((c + $NBSERVERS))
    "$SCRIPT_DIR"/remote-invoker.sh $MACHINE "$FOLDER" client$c $CORE "$BIN_DIR/$BINARY" -i $i $ARGS
  done
  echo " ✓"

  "$SCRIPT_DIR"/wait-till-completion.sh machine$FIRST_SERVER server1 240 || continue

  "$SCRIPT_DIR"/kill-all-tmux.sh
  exit 0
done
echo "####################### !!! Failed after 15 retries! !!! #######################"
