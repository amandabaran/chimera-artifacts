#!/bin/bash
export LD_LIBRARY_PATH="/bin/chimera/.deps/gcc/relwithdebinfo/lib:$LD_LIBRARY_PATH"

set -u

SCRIPT_DIR="$( realpath -sm "$( dirname "${BASH_SOURCE[0]}" )"/../scripts )"

CLIENT_COUNTS=(8)
SERVER_COUNTS=(3)

TIMES=(1)

# Extra feature flags specifically for the CHIMERA system

EXP_FOLDER_BASE="think-times"

for t in "${TIMES[@]}"; do
    CHIMERA_EXTRA_FLAGS="--cache 1 --writeback 0 --ml 1 --think ${t}"
    for ns in "${SERVER_COUNTS[@]}"; do
        for nc in "${CLIENT_COUNTS[@]}"; do
            WORKLOAD_FILE="ml-workload"
                # 1. Run CHIMERA Configurations
            EXP_FOLDER_CHIMERA="${EXP_FOLDER_BASE}/CHIMERA/think${t}/${ns}servers/${nc}client"
            
            echo "====> Executing: CHIMERA | ML Workload | Servers: ${ns} | Clients: ${nc}"
            
            "$SCRIPT_DIR"/run.sh chimera-exe "$EXP_FOLDER_CHIMERA" "$WORKLOAD_FILE" "$ns" "$nc" $CHIMERA_EXTRA_FLAGS

        done
    done
done
