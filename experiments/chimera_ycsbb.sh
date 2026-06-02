#!/bin/bash
export LD_LIBRARY_PATH="/bin/chimera/.deps/gcc/relwithdebinfo/lib:$LD_LIBRARY_PATH"

set -u

SCRIPT_DIR="$( realpath -sm "$( dirname "${BASH_SOURCE[0]}" )"/../scripts )"

# ./scripts/rundebug.sh <binary_name> <exp_folder_name> <workload_file> <num_servers> <num_clients> [extra_chimera_flags]
# "$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/2servers/1client oops-workloadb-uniform 2 1 --cache 1 --writeback 0
# "$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/2servers/2client oops-workloadb-uniform 2 2 --cache 1 --writeback 0
# "$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/2servers/4client oops-workloadb-uniform 2 4 --cache 1 --writeback 0
# "$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/2servers/8client oops-workloadb-uniform 2 8 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/3servers/1client/cache  oops-workloadb-uniform 3 1 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/3servers/2client/cache  oops-workloadb-uniform 3 2 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/3servers/4client/cache  oops-workloadb-uniform 3 4 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/3servers/8client/cache oops-workloadb-uniform 3 8 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/3servers/1client/nocache oops-workloadb-uniform 3 1 --cache 0 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/3servers/2client/nocache oops-workloadb-uniform 3 2 --cache 0 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/3servers/4client/nocache oops-workloadb-uniform 3 4 --cache 0 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-B/CHIMERA/3servers/8client/nocache oops-workloadb-uniform 3 8 --cache 0 --writeback 0

# "$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-B/SWARM-KV/2servers/1client oops-workloadb-uniform 2 1 
# "$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-B/SWARM-KV/2servers/2client oops-workloadb-uniform 2 2
# "$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-B/SWARM-KV/2servers/4client oops-workloadb-uniform 2 4
# "$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-B/SWARM-KV/2servers/8client oops-workloadb-uniform 2 8
# "$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-B/SWARM-KV/3servers/1client oops-workloadb-uniform 3 1
# "$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-B/SWARM-KV/3servers/2client oops-workloadb-uniform 3 2
# "$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-B/SWARM-KV/3servers/4client oops-workloadb-uniform 3 4
# "$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-B/SWARM-KV/3servers/8client oops-workloadb-uniform 3 8
