#!/bin/bash
export LD_LIBRARY_PATH="/bin/chimera/.deps/gcc/relwithdebinfo/lib:$LD_LIBRARY_PATH"

set -u

SCRIPT_DIR="$( realpath -sm "$( dirname "${BASH_SOURCE[0]}" )"/../scripts )"

# ./scripts/rundebug.sh <binary_name> <exp_folder_name> <workload_file> <num_servers> <num_clients> [extra_chimera_flags]
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-C/CHIMERA/2servers/1client oops-workloadc-uniform 2 1 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-C/CHIMERA/2servers/2client oops-workloadc-uniform 2 2 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-C/CHIMERA/2servers/4client oops-workloadc-uniform 2 4 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-C/CHIMERA/2servers/8client oops-workloadc-uniform 2 8 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-C/CHIMERA/3servers/1client oops-workloadc-uniform 3 1 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-C/CHIMERA/3servers/2client oops-workloadc-uniform 3 2 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-C/CHIMERA/3servers/4client oops-workloadc-uniform 3 4 --cache 1 --writeback 0
"$SCRIPT_DIR"/run.sh chimera-exe test-exp/workload-C/CHIMERA/3servers/8client oops-workloadc-uniform 3 8 --cache 1 --writeback 0

"$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-C/SWARM-KV/2servers/1client oops-workloadc-uniform 2 1 
"$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-C/SWARM-KV/2servers/2client oops-workloadc-uniform 2 2
"$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-C/SWARM-KV/2servers/4client oops-workloadc-uniform 2 4
"$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-C/SWARM-KV/2servers/8client oops-workloadc-uniform 2 8
"$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-C/SWARM-KV/3servers/1client oops-workloadc-uniform 3 1
"$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-C/SWARM-KV/3servers/2client oops-workloadc-uniform 3 2
"$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-C/SWARM-KV/3servers/4client oops-workloadc-uniform 3 4
"$SCRIPT_DIR"/run.sh swarmkv test-exp/workload-C/SWARM-KV/3servers/8client oops-workloadc-uniform 3 8
