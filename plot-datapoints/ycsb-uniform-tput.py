#!/usr/bin/env python3

import os
import re
import sys
from prelude import plt
from matplotlib.ticker import *
from matplotlib.lines import Line2D

def parse_chimera_native(path):
    out = {}
    with open(path, 'r') as f:
        for line in f:
            clean = line.strip().lower()
            if "local tput:" in clean:
                match = re.search(r"local tput:\s*(\d+)", clean)
                if match:
                    out["local tput"] = int(match.group(1))
    return out

# --- Configuration ---
SERVERS_CONFIG = '3servers'
MAX_CLIENTS = 8  # Scales dynamically based on client logs

apps = {
    'YCSB A - Uniform' : 'A',
    'YCSB B - Uniform' : 'B',
    'YCSB C - Uniform' : 'C',
}

schemes = {
    'SWARM-KV': {
        'label': 'SWARM-KV', 'color': '#3b8df8', 'lstyle': '-', 'lwidth': 0.9,
    },
    'CHIMERA': {
        'label': 'CHIMERA', 'color': '#0bab0b', 'lstyle': '--', 'lwidth': 1.2,
    },
}

client_counts = [1, 2, 4, 8]

legends_schemes = [
    Line2D([0], [0], color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
           linewidth=schemes[s]['lwidth'], label=schemes[s]['label']) for s in schemes
]

# 1x3 row layout optimized for throughput curves
fig, subplots = plt.subplots(1, 3, figsize=(5.00, 1.25), tight_layout=True)
plt.tight_layout(pad=0, w_pad=0.45, rect=(0, 0, 1, 1))
fig.subplots_adjust(top=0.74, bottom=0.26)

for plot in subplots:
    plot.tick_params(axis='both', which='major', pad=2.0)
    plot.tick_params(axis='both', which='minor', pad=2.0)

# --- Data Loop & Plotting ---
for col_idx, (app_title, workload_letter) in enumerate(apps.items()):
    subplot = subplots[col_idx]
    subplot.set_title(app_title, pad=4, fontsize=8.5)
    
    for s in schemes:
        tputs_mops = []
        valid_clients = []
        
        for nc in client_counts:
            total_tput = 0
            has_data = False
            
            for c in range(1, nc + 1):
                path = os.path.join("logs", "YCSB", f"workload-{workload_letter}", s, SERVERS_CONFIG, f"{nc}client", f"client{c}.txt")
                if not os.path.exists(path):
                    continue
                
                data = parse_chimera_native(path)
                has_data = True
                total_tput += data.get('local tput', 0)
            
            if has_data:
                valid_clients.append(nc)
                tputs_mops.append(total_tput / 1000.0)
                
        if valid_clients:
            subplot.plot(valid_clients, tputs_mops, color=schemes[s]['color'], 
                         linestyle=schemes[s]['lstyle'], linewidth=schemes[s]['lwidth'])

    # Aesthetics and ticks
    subplot.grid(axis='both', which='major', linestyle='--', linewidth='0.5')
    subplot.grid(axis='both', which='minor', linestyle=':', linewidth='0.25')
    subplot.set_axisbelow(True)
    subplot.set_xlabel('Client threads', labelpad=2)
    
    subplot.set_xlim(0, MAX_CLIENTS + (1 if MAX_CLIENTS <= 8 else 4))
    if MAX_CLIENTS <= 8:
        subplot.xaxis.set_major_locator(FixedLocator([1, 2, 4, 8]))
    else:
        subplot.xaxis.set_major_locator(MultipleLocator(16 if MAX_CLIENTS > 32 else 8))
        subplot.xaxis.set_minor_locator(MultipleLocator(4))

# Throughput ranges (Mops)
subplots[0].set_ylim(0, 2.0)
subplots[0].yaxis.set_major_locator(MultipleLocator(0.5))
subplots[1].set_ylim(0, 3.0)
subplots[1].yaxis.set_major_locator(MultipleLocator(1.0))
subplots[2].set_ylim(0, 3.0)
subplots[2].yaxis.set_major_locator(MultipleLocator(1.0))

subplots[0].set_ylabel('Tput (Mops)', labelpad=3)

# Centered Scheme Legend
leg_scheme = fig.legend(handles=legends_schemes, bbox_to_anchor=(0.50, 0.93), loc='center', edgecolor='black', ncols=2, borderpad=.25, handletextpad=0.5)

os.makedirs("output-plots", exist_ok=True)
plt.savefig("output-plots/ycsb-uniform-throughput.pdf", format='pdf', bbox_inches='tight', pad_inches=0.01)
print("Saved Throughput plot safely to output-plots/ycsb-uniform-throughput.pdf")