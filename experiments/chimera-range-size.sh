#!/bin/bash
export LD_LIBRARY_PATH="/bin/chimera/.deps/gcc/relwithdebinfo/lib:$LD_LIBRARY_PATH"

set -u

SCRIPT_DIR="$( realpath -sm "$( dirname "${BASH_SOURCE[0]}" )"/../scripts )"

CLIENT_COUNTS=(32 64)
SERVER_COUNTS=(3)
WORKLOADS=("e")

RANGES=(1 2 4 16 32 64)

# Extra feature flags specifically for the CHIMERA system

EXP_FOLDER_BASE="rq-sizes"

for range in "${RANGES[@]}"; do
    CHIMERA_EXTRA_FLAGS="--cache 1 --writeback 0 --maxrange ${range}"
    for wl in "${WORKLOADS[@]}"; do
        # Convert workload letters to matching uppercase names for output paths
        WL_UPPER=$(echo "$wl" | tr '[:lower:]' '[:upper:]')
        WORKLOAD_FILE="oops-workload${wl}-${range}"

        for ns in "${SERVER_COUNTS[@]}"; do
            for nc in "${CLIENT_COUNTS[@]}"; do
                
                # 1. Run CHIMERA Configurations
                EXP_FOLDER_CHIMERA="${EXP_FOLDER_BASE}/workload-${WL_UPPER}/CHIMERA/range${range}/${ns}servers/${nc}client"
                
                echo "====> Executing: CHIMERA | Workload ${WL_UPPER} | Servers: ${ns} | Clients: ${nc}"
                
                "$SCRIPT_DIR"/run.sh chimera-exe "$EXP_FOLDER_CHIMERA" "$WORKLOAD_FILE" "$ns" "$nc" $CHIMERA_EXTRA_FLAGS

                
                # 2. Run SWARM-KV Configurations
                EXP_FOLDER_SWARM="${EXP_FOLDER_BASE}/workload-${WL_UPPER}/SWARM-KV/range${range}/${ns}servers/${nc}client"
                
                echo "====> Executing: SWARM-KV | Workload ${WL_UPPER} | Servers: ${ns} | Clients: ${nc}"
                
                "$SCRIPT_DIR"/run.sh swarmkv "$EXP_FOLDER_SWARM" "$WORKLOAD_FILE" "$ns" "$nc"

            done
        done
    done
done
