#!/bin/bash
export LD_LIBRARY_PATH="/bin/chimera/.deps/gcc/relwithdebinfo/lib:$LD_LIBRARY_PATH"

set -u

SCRIPT_DIR="$( realpath -sm "$( dirname "${BASH_SOURCE[0]}" )"/../scripts )"


# "$SCRIPT_DIR"/run.sh raw_memory fig5-latency-cdf/workload-A/RAW oops-workloada 1 1
# "$SCRIPT_DIR"/run.sh raw_memory fig5-latency-cdf/workload-B/RAW oops-workloadb 1 1
# "$SCRIPT_DIR"/run.sh swarmkv fig5-latency-cdf/workload-A/SWARM-KV oops-workloada 2 4 -m 2 -T 0 -d=true
# "$SCRIPT_DIR"/run.sh swarmkv fig5-latency-cdf/workload-B/SWARM-KV oops-workloadb 2 4 -m 2 -T 0 -d=true
# "$SCRIPT_DIR"/run.sh swarmkv fig5-latency-cdf/workload-A/DM-ABD oops-workloada 2 4 -m 2 -d=true -g=false --in_place=false
# "$SCRIPT_DIR"/run.sh swarmkv fig5-latency-cdf/workload-B/DM-ABD oops-workloadb 2 4 -m 2 -d=true -g=false --in_place=false
# "$SCRIPT_DIR"/run.sh fusee fig5-latency-cdf/workload-A/FUSEE oops-workloada 2 4
# "$SCRIPT_DIR"/run.sh fusee fig5-latency-cdf/workload-B/FUSEE oops-workloadb 2 4
"$SCRIPT_DIR"/run.sh chimera-exe scan_test/fig5-latency-cdf/workload-A/CHIMERA oops-workloada 3 4 -m 2
"$SCRIPT_DIR"/run.sh chimera-exe scan_test/fig5-latency-cdf/workload-B/CHIMERA oops-workloadb 3 4 -m 2
"$SCRIPT_DIR"/run.sh chimera-exe scan_test/fig5-latency-cdf/workload-E/CHIMERA oops-workloade 3 4 -m 2