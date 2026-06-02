#!/usr/bin/env python3

import os
import re
import sys
from prelude import plt
from matplotlib.ticker import *
from matplotlib.lines import Line2D

def parse_chimera_native(path):
    out = {}
    current_op = None
    with open(path, 'r') as f:
        for line in f:
            clean = line.strip().lower()
            if "get stats:" in clean:
                current_op = "GET"
                out[current_op] = {'pcount': 0, 'psum': 0}
            elif "update stats:" in clean or "put stats:" in clean:
                current_op = "UPDATE"
                out[current_op] = {'pcount': 0, 'psum': 0}
            elif "local tput:" in clean:
                match = re.search(r"local tput:\s*(\d+)", clean)
                if match:
                    out["local tput"] = int(match.group(1))
            elif current_op and "%:" in clean:
                match = re.search(r"([0-9.]+)\s*%:\s*([0-9.]+)\s*(us|ns)", clean)
                if match:
                    perc = float(match.group(1))
                    val = float(match.group(2))
                    unit = match.group(3)
                    latency_us = val if unit == "us" else val / 1000.0
                    out[current_op][perc] = latency_us
                    if perc > 0.5:
                        out[current_op]['pcount'] += 1
                        out[current_op]['psum'] += latency_us
    return out

# --- Configuration ---
SERVERS_CONFIG = '3servers'
MAX_CLIENTS = 8  # Set to 16, 32, or 64 as you extend your performance tests

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

ops = {
    'GET': 'o',
    'UPDATE': 'd',
}

client_counts = [1, 2, 4, 8]

legends_schemes = [
    Line2D([0], [0], color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
           linewidth=schemes[s]['lwidth'], label=schemes[s]['label']) for s in schemes
]

legends_ops = [
    Line2D([], [], color='grey', marker=ops[op], linestyle='None',
           markersize=4.5, label=op) for op in ops
]

# Create single row with an open, high-aspect vertical dimension
fig, subplots = plt.subplots(1, 3, figsize=(5.00, 1.45), tight_layout=True)
plt.tight_layout(pad=0, w_pad=0.45, rect=(0, 0, 1, 1))
fig.subplots_adjust(top=0.74, bottom=0.24)

for plot in subplots:
    plot.tick_params(axis='both', which='major', pad=2.0)
    plot.tick_params(axis='both', which='minor', pad=2.0)

# --- Data Loop & Plotting ---
for col_idx, (app_title, workload_letter) in enumerate(apps.items()):
    subplot = subplots[col_idx]
    subplot.set_title(app_title, pad=4, fontsize=8.5)
    
    for s in schemes:
        lats_get = []
        lats_upd = []
        valid_clients = []
        
        for nc in client_counts:
            get_ops, get_lat_sum = 0, 0
            upd_ops, upd_lat_sum = 0, 0
            has_data = False
            
            for c in range(1, nc + 1):
                path = os.path.join("logs", "YCSB", f"workload-{workload_letter}", s, SERVERS_CONFIG, f"{nc}client", f"client{c}.txt")
                if not os.path.exists(path):
                    continue
                
                data = parse_chimera_native(path)
                has_data = True
                
                if 'GET' in data:
                    get_ops += data['GET'].get('pcount', 0)
                    get_lat_sum += data['GET'].get('psum', 0)
                if 'UPDATE' in data:
                    upd_ops += data['UPDATE'].get('pcount', 0)
                    upd_lat_sum += data['UPDATE'].get('psum', 0)
            
            if has_data:
                valid_clients.append(nc)
                lats_get.append((get_lat_sum / get_ops) if get_ops > 0 else 0)
                lats_upd.append((upd_lat_sum / upd_ops) if upd_ops > 0 else 0)
                
        if valid_clients:
            if any(lats_get):
                subplot.plot(valid_clients, lats_get, color=schemes[s]['color'], 
                             linestyle=schemes[s]['lstyle'], linewidth=schemes[s]['lwidth'], 
                             marker=ops['GET'], markersize=3.5)
            if workload_letter != 'C' and any(lats_upd):
                subplot.plot(valid_clients, lats_upd, color=schemes[s]['color'], 
                             linestyle=schemes[s]['lstyle'], linewidth=schemes[s]['lwidth'], 
                             marker=ops['UPDATE'], markersize=3.5)

    subplot.grid(axis='both', which='major', linestyle='--', linewidth='0.5')
    subplot.grid(axis='both', which='minor', linestyle=':', linewidth='0.25')
    subplot.set_axisbelow(True)
    subplot.set_xlabel('Client threads', labelpad=2)
    
    # Adaptive X-limits
    subplot.set_xlim(0, MAX_CLIENTS + (1 if MAX_CLIENTS <= 8 else 4))
    if MAX_CLIENTS <= 8:
        subplot.xaxis.set_major_locator(FixedLocator([1, 2, 4, 8]))
    else:
        subplot.xaxis.set_major_locator(MultipleLocator(16 if MAX_CLIENTS > 32 else 8))
        subplot.xaxis.set_minor_locator(MultipleLocator(4))

# --- Workload-Specific Y-Axis Tuning ---
# Workload A expanded to 14us to cleanly resolve tail spikes at high loads
subplots[0].set_ylim(0, 14)
subplots[0].yaxis.set_major_locator(MultipleLocator(4))
subplots[0].yaxis.set_minor_locator(MultipleLocator(2))

# Workload B handles moderate updates, framed comfortably at 8us
subplots[1].set_ylim(0, 8)
subplots[1].yaxis.set_major_locator(MultipleLocator(2))
subplots[1].yaxis.set_minor_locator(MultipleLocator(1))

# Workload C is pure read-only execution, bounded tightly at 5us
subplots[2].set_ylim(0, 5)
subplots[2].yaxis.set_major_locator(MultipleLocator(1))
subplots[2].yaxis.set_minor_locator(MultipleLocator(0.5))

subplots[0].set_ylabel('Latency (μs)', labelpad=3)

# Legend Layout Configurations
leg_scheme = fig.legend(handles=legends_schemes, bbox_to_anchor=(0.28, 0.93), loc='center', edgecolor='black', ncols=2, borderpad=.25, handletextpad=0.5)
leg_ops = fig.legend(handles=legends_ops, bbox_to_anchor=(0.76, 0.93), loc='center', edgecolor='black', ncols=2, borderpad=.25, handletextpad=0.5)

os.makedirs("output-plots", exist_ok=True)
plt.savefig("output-plots/ycsb-uniform-latency.pdf", format='pdf', bbox_inches='tight', pad_inches=0.01)
print("Latency curves mapped safely to output-plots/ycsb-uniform-latency.pdf")