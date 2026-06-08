#!/bin/bash
export LD_LIBRARY_PATH="/bin/chimera/.deps/gcc/relwithdebinfo/lib:$LD_LIBRARY_PATH"

set -u

SCRIPT_DIR="$( realpath -sm "$( dirname "${BASH_SOURCE[0]}" )"/../scripts )"

CLIENT_COUNTS=(32)
SERVER_COUNTS=(3)
WORKLOADS=("b")

REGISTERS=(1)

# Extra feature flags specifically for the CHIMERA system

EXP_FOLDER_BASE="reg-scaling"

for nregs in "${REGISTERS[@]}"; do
    CHIMERA_EXTRA_FLAGS="--cache 1 --writeback 0 --regs ${nregs}"
    for wl in "${WORKLOADS[@]}"; do
        # Convert workload letters to matching uppercase names for output paths
        WL_UPPER=$(echo "$wl" | tr '[:lower:]' '[:upper:]')
        WORKLOAD_FILE="oops-workload${wl}-uniform-${nregs}"

        for ns in "${SERVER_COUNTS[@]}"; do
            for nc in "${CLIENT_COUNTS[@]}"; do
                
                # 1. Run CHIMERA Configurations
                EXP_FOLDER_CHIMERA="${EXP_FOLDER_BASE}/workload-${WL_UPPER}/CHIMERA/${nregs}reg/${ns}servers/${nc}client"
                
                echo "====> Executing: CHIMERA | Workload ${WL_UPPER} | Servers: ${ns} | Clients: ${nc}"
                
                "$SCRIPT_DIR"/run.sh chimera-exe "$EXP_FOLDER_CHIMERA" "$WORKLOAD_FILE" "$ns" "$nc" $CHIMERA_EXTRA_FLAGS

                
                # 2. Run SWARM-KV Configurations
                EXP_FOLDER_SWARM="${EXP_FOLDER_BASE}/workload-${WL_UPPER}/SWARM-KV/${nregs}reg/${ns}servers/${nc}client"
                
                echo "====> Executing: SWARM-KV | Workload ${WL_UPPER} | Servers: ${ns} | Clients: ${nc}"
                
                "$SCRIPT_DIR"/run.sh swarmkv "$EXP_FOLDER_SWARM" "$WORKLOAD_FILE" "$ns" "$nc" -n ${nregs}

                # 3. Run DM-ABD Configurations
                EXP_FOLDER_DM_ABD="${EXP_FOLDER_BASE}/workload-${WL_UPPER}/DM-ABD/${nregs}reg/${ns}servers/${nc}client"

                echo "====> Executing: DM-ABD | Workload ${WL_UPPER} | Servers: ${ns} | Clients: ${nc}"

                "$SCRIPT_DIR"/run.sh swarmkv "$EXP_FOLDER_DM_ABD" "$WORKLOAD_FILE" "$ns" "$nc" -d=true -g=false --in_place=false -n ${nregs}

                # 4. Run FUSEE Configurations
                EXP_FOLDER_FUSEE="${EXP_FOLDER_BASE}/workload-${WL_UPPER}/FUSEE/${nregs}reg/${ns}servers/${nc}client"

                echo "====> Executing: FUSEE | Workload ${WL_UPPER} | Servers: ${ns} | Clients: ${nc}"

                "$SCRIPT_DIR"/run.sh fusee "$EXP_FOLDER_FUSEE" "$WORKLOAD_FILE" "$ns" "$nc" -n ${nregs}

            done
        done
    done
done
