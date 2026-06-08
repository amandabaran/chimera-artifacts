#!/bin/bash
export LD_LIBRARY_PATH="/bin/chimera/.deps/gcc/relwithdebinfo/lib:$LD_LIBRARY_PATH"

set -u

SCRIPT_DIR="$( realpath -sm "$( dirname "${BASH_SOURCE[0]}" )"/../scripts )"

# CLIENT_COUNTS=(2 4 8 16 32 48 64)
# CLIENT_COUNTS=(1 2 3 4 5 6 7 8 10 12 14 16 20 24 28 32 36 40 44 48 52 56 60 64)
# CLIENT_COUNTS=(44 48 52 56 60 64)
CLIENT_COUNTS=(48 64)
SERVER_COUNTS=(3)

# Extra feature flags specifically for the CHIMERA system
CHIMERA_EXTRA_FLAGS="--cache 1 --writeback 0 --ml 1"

EXP_FOLDER_BASE="ML"

WORKLOAD_FILE="ml-workload"

for ns in "${SERVER_COUNTS[@]}"; do
    for nc in "${CLIENT_COUNTS[@]}"; do
        
        # 1. Run CHIMERA Configurations
        EXP_FOLDER_CHIMERA="${EXP_FOLDER_BASE}/CHIMERA/${ns}servers/${nc}client"
        
        echo "====> Executing: CHIMERA | ML Workload | Servers: ${ns} | Clients: ${nc}"
        
        "$SCRIPT_DIR"/run.sh chimera-exe "$EXP_FOLDER_CHIMERA" "$WORKLOAD_FILE" "$ns" "$nc" $CHIMERA_EXTRA_FLAGS

        
        # # 2. Run SWARM-KV Configurations
        # EXP_FOLDER_SWARM="${EXP_FOLDER_BASE}/SWARM-KV/${ns}servers/${nc}client"
        
        # echo "====> Executing: SWARM-KV | ML Workload | Servers: ${ns} | Clients: ${nc}"
        
        # "$SCRIPT_DIR"/run.sh swarmkv "$EXP_FOLDER_SWARM" "$WORKLOAD_FILE" "$ns" "$nc"

    done
done
