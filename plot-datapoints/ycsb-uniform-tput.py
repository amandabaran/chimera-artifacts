#!/usr/bin/env python3

import os
import re
import sys
from prelude import plt
from matplotlib.ticker import *
from matplotlib.lines import Line2D

def parse_chimera_native(path):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, 'r') as f:
        for line in f:
            clean = line.strip().lower()
            if "local tput:" in clean:
                match = re.search(r"local tput:\s*(\d+)", clean)
                if match:
                    out["local tput"] = int(match.group(1))
            elif "aggregated tput:" in clean:
                match = re.search(r"aggregated tput:\s*(\d+)", clean)
                if match:
                    out["aggregated tput"] = int(match.group(1))
    return out

# --- Configuration ---
SERVERS_CONFIG = '3servers'

apps = {
    'YCSB A - 50/50' : 'A',
    'YCSB B - 95/5' : 'B',
    'YCSB C - 100/0' : 'C',
}

schemes = {
    'SWARM-KV': { 'label': 'SWARM-KV', 'color': '#3b8df8', 'lstyle': '-', 'lwidth': 0.9 },
    'CHIMERA':  { 'label': 'CHIMERA',  'color': '#0bab0b', 'lstyle': '--', 'lwidth': 1.2 },
    'DM-ABD':   { 'label': 'DM-ABD',   'color': '#d11414', 'lstyle': '--', 'lwidth': 1 },
    'FUSEE':    { 'label': 'FUSEE',    'color': '#f4860b', 'lstyle': ':', 'lwidth': 1.4 },
}

client_counts = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64]
MAX_CLIENTS = max(client_counts)

legends_schemes = [
    Line2D([0], [0], color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
           linewidth=schemes[s]['lwidth'], label=schemes[s]['label']) for s in schemes
]

# --- UNIFIED LAYOUT SIZING ---
fig, subplots = plt.subplots(1, 3, figsize=(5.00, 1.45))
fig.subplots_adjust(top=0.74, bottom=0.24, left=0.10, right=0.98, wspace=0.35)

for plot in subplots:
    plot.tick_params(axis='both', which='major', pad=2.0)

# --- Data Loop & Plotting ---
for col_idx, (app_title, workload_letter) in enumerate(apps.items()):
    subplot = subplots[col_idx]
    subplot.set_title(app_title, pad=5, fontsize=8.5)
    
    for s in schemes:
        tputs_mops = []
        valid_clients = []
        
        for nc in client_counts:
            total_tput = 0
            has_data = False
            fusee_global_tput = None
            
            for c in range(1, nc + 1):
                path = os.path.join("logs", "YCSB", f"workload-{workload_letter}", s, SERVERS_CONFIG, f"{nc}client", f"client{c}.txt")
                if not os.path.exists(path):
                    continue
                
                data = parse_chimera_native(path)
                has_data = True
                
                if "aggregated tput" in data:
                    fusee_global_tput = data["aggregated tput"]
                else:
                    total_tput += data.get("local tput", 0)
            
            if has_data:
                valid_clients.append(nc)
                if "FUSEE" in s.upper() and fusee_global_tput is not None:
                    final_tput_mops = fusee_global_tput / 1000.0
                else:
                    final_tput_mops = total_tput / 1000.0
                tputs_mops.append(final_tput_mops)

        if valid_clients:
            subplot.plot(valid_clients, tputs_mops, color=schemes[s]['color'], 
                         linestyle=schemes[s]['lstyle'], linewidth=schemes[s]['lwidth'])

    subplot.set_xlabel('Client threads', labelpad=2)

# --- Workload-Specific Throughput Tuning ---
subplots[0].set_ylim(0, 6.0)
subplots[0].yaxis.set_major_locator(MultipleLocator(2.0))

subplots[1].set_ylim(0, 15.0)
subplots[1].yaxis.set_major_locator(MultipleLocator(5.0))

subplots[2].set_ylim(0, 18.0)
subplots[2].yaxis.set_major_locator(MultipleLocator(6.0))

# --- Global Forced Grid Apply Pass ---
for subplot in subplots:
    subplot.yaxis.set_minor_locator(NullLocator())
    subplot.xaxis.set_minor_locator(NullLocator())
    subplot.set_xlim(0, MAX_CLIENTS + 4)
    subplot.xaxis.set_major_locator(MultipleLocator(16))
    subplot.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5, alpha=0.7)
    subplot.set_axisbelow(True)

subplots[0].set_ylabel('Tput (Mops)', labelpad=3)

# --- UNIFIED LEGEND ---
leg_scheme = fig.legend(handles=legends_schemes, bbox_to_anchor=(0.54, 0.93), 
                        loc='center', edgecolor='black', ncols=4, borderpad=.25, handletextpad=0.5)

os.makedirs("output-plots", exist_ok=True)
plt.savefig("output-plots/ycsb-uniform-throughput.pdf", format='pdf', bbox_inches='tight', pad_inches=0.01)
print("Saved clean Throughput plot safely.")