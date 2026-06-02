#!/bin/bash
set -e

BASE_DIR="$( realpath -sm  "$( dirname "${BASH_SOURCE[0]}" )")"
cd "$BASE_DIR"

source "$BASE_DIR/scripts/config.sh"

# Define a function to process an individual machine deployment
deploy_to_node() {
  local idx=$1
  local node="w${idx}"
  
  # Redirect internal output to a local node log or silence to prevent terminal text corruption
  (
    ssh "$node" "mkdir -p \"$BASE_DIR\""
    scp -C -o Cipher=chacha20-poly1305@openssh.com deployment.zip "${node}:$BASE_DIR/deployment.zip"
    
    ssh "$node" "unzip -o \"$BASE_DIR/deployment.zip\" -d \"$BASE_DIR\"; \
                 cd \"$BASE_DIR\"; \
                 tar -xf ycsb-0.12.0.tar.gz; \
                 rm -rf YCSB; mv ycsb-0.12.0 YCSB; \
                 cd \"$BASE_DIR/bin\"; \
                 mkdir -p staging; \
                 unzip -o -q bin.zip -d staging/; \
                 mv -f staging/chimera ./chimera-exe; \
                 mv -f staging/* ./ 2>/dev/null || true; \
                 rm -rf staging;"
                 
    echo " ✓ [${node}] Deployment payload successfully processed and verified."
  ) 2>&1 | sed "s/^/[${node}] /" # Prefixes the output lines so you know which node is talking
}

echo "Starting parallel broadcast deployment to ${MACHINE_COUNT} nodes..."
echo "------------------------------------------------------------"

# Fire off the worker functions into the background simultaneously
for i in $(seq 1 "$MACHINE_COUNT"); do
  deploy_to_node "$i" &
done

# CRITICAL barrier: Instructs the parent script to pause here until 
# EVERY background child process has finished executing
wait

echo "------------------------------------------------------------"
echo "Parallel deployment successful across all nodes!"