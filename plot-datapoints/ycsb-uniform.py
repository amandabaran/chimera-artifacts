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
    if not os.path.exists(path):
        return out
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
                    
            # Parse Throughput Breakdown if available (for individual tput plotting)
            elif current_op and "ops:" in clean:
                match = re.search(r"ops:\s*(\d+)", clean)
                if match:
                    out[current_op]['ops'] = int(match.group(1))
                    
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

# ==============================================================================
# --- TOGGLE MODE HERE ---
# ==============================================================================
# True  => 1 aggregated line per system for both Latency & Throughput
# False => Individual breakdown lines (GET vs UPDATE shapes) for both metrics
AGGREGATE_METRICS = True 

SERVERS_CONFIG = '3servers'
apps = {
    'YCSB A - Uniform' : 'A',
    'YCSB B - Uniform' : 'B',
    'YCSB C - Uniform' : 'C',
}

schemes = {
    'SWARM-KV': {'label': 'SWARM-KV', 'color': '#3b8df8', 'lstyle': '-', 'lwidth': 1.0},
    'CHIMERA': {'label': 'CHIMERA', 'color': '#0bab0b', 'lstyle': '--', 'lwidth': 1.3},
}

ops = {
    'GET': 'o',
    'UPDATE': 'd',
}

client_counts = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64]
MAX_CLIENTS = max(client_counts)

# --- Build Legend Handles Dynamically ---
legends_schemes = [
    Line2D([0], [0], color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
           linewidth=schemes[s]['lwidth'], label=schemes[s]['label']) for s in schemes
]

legends_ops = [] if AGGREGATE_METRICS else [
    Line2D([], [], color='grey', marker=ops[op], linestyle='None',
           markersize=4.5, label=op) for op in ops
]

fig, subplots = plt.subplots(2, 3, figsize=(6.20, 2.80))
fig.subplots_adjust(top=0.83, bottom=0.14, left=0.11, right=0.97)
plt.tight_layout(pad=0, h_pad=0.35, w_pad=0.45, rect=(0, 0, 1, 1))

for plot in subplots[0]:
    plot.tick_params(axis='x', which='both', bottom=True, labelbottom=False)

for row in subplots:
    for plot in row:
        plot.tick_params(axis='both', which='major', labelsize=8, pad=2.0)

# --- Data Loop & Plotting ---
for col_idx, (app_title, workload_letter) in enumerate(apps.items()):
    subplots[0][col_idx].set_title(app_title, pad=5, fontsize=9.0, weight='bold')
    
    for s in schemes:
        valid_clients = []
        
        # Lists for Individual Mode
        lats_get, lats_upd = [], []
        tputs_get, tputs_upd = [], []
        
        # Lists for Aggregated Mode
        lats_combined = []
        tputs_combined = []
        
        for nc in client_counts:
            total_tput = 0
            get_ops, get_lat_sum, get_count_tput = 0, 0, 0
            upd_ops, upd_lat_sum, upd_count_tput = 0, 0, 0
            has_data = False
            
            for c in range(1, nc + 1):
                path = os.path.join("logs", "YCSB", f"workload-{workload_letter}", s, SERVERS_CONFIG, f"{nc}client", f"client{c}.txt")
                if not os.path.exists(path):
                    continue
                
                data = parse_chimera_native(path)
                has_data = True
                
                total_tput += data.get('local tput', 0)
                if 'GET' in data:
                    get_ops += data['GET'].get('pcount', 0)
                    get_lat_sum += data['GET'].get('psum', 0)
                    get_count_tput += data['GET'].get('ops', 0)
                if 'UPDATE' in data:
                    upd_ops += data['UPDATE'].get('pcount', 0)
                    upd_lat_sum += data['UPDATE'].get('psum', 0)
                    upd_count_tput += data['UPDATE'].get('ops', 0)
            
            if has_data:
                valid_clients.append(nc)
                
                avg_get = (get_lat_sum / get_ops) if get_ops > 0 else 0
                avg_upd = (upd_lat_sum / upd_ops) if upd_ops > 0 else 0
                
                if AGGREGATE_METRICS:
                    # Symmetrical Aggregation: Weighted Mean Latency & Total System Throughput
                    total_ops_recorded = get_ops + upd_ops
                    avg_combined = ((get_lat_sum + upd_lat_sum) / total_ops_recorded) if total_ops_recorded > 0 else 0
                    lats_combined.append(avg_combined)
                    tputs_combined.append(total_tput / 1000.0)
                else:
                    # Symmetrical Split: Breakdown of both metrics by Operation Type
                    lats_get.append(avg_get)
                    lats_upd.append(avg_upd)
                    
                    # If local operational throughput logs aren't distinct, scale from total
                    if get_count_tput == 0 and upd_count_tput == 0:
                        # Fallback profile proportional split (e.g., YCSB A 50/50, B 95/5)
                        ratio_get = 0.5 if workload_letter == 'A' else (0.95 if workload_letter == 'B' else 1.0)
                    else:
                        total_logged = get_count_tput + upd_count_tput
                        ratio_get = (get_count_tput / total_logged) if total_logged > 0 else 1.0
                        
                    tputs_get.append((total_tput * ratio_get) / 1000.0)
                    tputs_upd.append((total_tput * (1.0 - ratio_get)) / 1000.0)

        # --- Draw Renderings ---
        if valid_clients:
            if AGGREGATE_METRICS:
                # Top Row: Aggregate Latency (No shapes)
                subplots[0][col_idx].plot(valid_clients, lats_combined,
                    color=schemes[s]['color'], linestyle=schemes[s]['lstyle'], linewidth=schemes[s]['lwidth'])
                # Bottom Row: Aggregate Throughput (No shapes)
                subplots[1][col_idx].plot(valid_clients, tputs_combined,
                    color=schemes[s]['color'], linestyle=schemes[s]['lstyle'], linewidth=schemes[s]['lwidth'])
            else:
                # Top Row: Split Latency by Op shape
                if any(lats_get):
                    subplots[0][col_idx].plot(valid_clients, lats_get,
                        color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
                        linewidth=schemes[s]['lwidth'], marker=ops['GET'], markersize=3.0)
                if workload_letter != 'C' and any(lats_upd):
                    subplots[0][col_idx].plot(valid_clients, lats_upd,
                        color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
                        linewidth=schemes[s]['lwidth'], marker=ops['UPDATE'], markersize=3.0)
                
                # Bottom Row: Split Throughput by Op shape (Symmetrical Matching)
                if any(tputs_get):
                    subplots[1][col_idx].plot(valid_clients, tputs_get,
                        color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
                        linewidth=schemes[s]['lwidth'], marker=ops['GET'], markersize=3.0)
                if workload_letter != 'C' and any(tputs_upd):
                    subplots[1][col_idx].plot(valid_clients, tputs_upd,
                        color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
                        linewidth=schemes[s]['lwidth'], marker=ops['UPDATE'], markersize=3.0)

    # --- Formatting Layouts ---
    for row_idx in [0, 1]:
        subplot = subplots[row_idx][col_idx]
        subplot.grid(axis='both', which='major', linestyle='--', linewidth='0.5')
        subplot.set_xlim(0, MAX_CLIENTS + 2)
        subplot.xaxis.set_major_locator(MultipleLocator(16))
        subplot.set_axisbelow(True)

# Custom Y limits to keep the comparison visualization proportional
subplots[0][0].set_ylim(0, 45)
subplots[0][1].set_ylim(0, 25)
subplots[0][2].set_ylim(0, 15)


# subplots[0][0].set_ylim(0, 45)   # Workload A updates spike significantly under contention
# subplots[0][0].yaxis.set_major_locator(MultipleLocator(10))
# subplots[0][0].yaxis.set_minor_locator(MultipleLocator(5))

# subplots[0][1].set_ylim(0, 25)   # Workload B handles mixed lookups securely
# subplots[0][1].yaxis.set_major_locator(MultipleLocator(5))
# subplots[0][1].yaxis.set_minor_locator(MultipleLocator(2.5))

# subplots[0][2].set_ylim(0, 15)    # Workload C stays highly optimized
# subplots[0][2].yaxis.set_major_locator(MultipleLocator(2))
# subplots[0][2].yaxis.set_minor_locator(MultipleLocator(1))

# # Bottom Row (Throughput Scaled Out to Accommodate High Threads)
# subplots[1][0].set_ylim(0, 5.0)
# subplots[1][0].yaxis.set_major_locator(MultipleLocator(2.0))
# subplots[1][1].set_ylim(0, 15.0)
# subplots[1][1].yaxis.set_major_locator(MultipleLocator(3.0))
# subplots[1][2].set_ylim(0, 18.0)
# subplots[1][2].yaxis.set_major_locator(MultipleLocator(3.0))

if AGGREGATE_METRICS:
    subplots[1][0].set_ylim(0, 6.0)
    subplots[1][1].set_ylim(0, 15.0)
    subplots[1][2].set_ylim(0, 18.0)
else:
    subplots[1][0].set_ylim(0, 4.0)
    subplots[1][1].set_ylim(0, 10.0)
    subplots[1][2].set_ylim(0, 15.0)

subplots[0][0].set_ylabel('Latency (μs)', labelpad=4, fontsize=9)
subplots[1][0].set_ylabel('Tput (Mops)', labelpad=4, fontsize=9)
for col_idx in range(3):
    subplots[1][col_idx].set_xlabel('Client threads', labelpad=3, fontsize=8.5)

# --- Responsive Legend Positioning ---
if AGGREGATE_METRICS:
    fig.legend(handles=legends_schemes, bbox_to_anchor=(0.5, 0.94),
               loc='center', edgecolor='black', ncols=2, borderpad=.25, fontsize=8.5)
else:
    fig.legend(handles=legends_schemes, bbox_to_anchor=(0.30, 0.94),
               loc='center', edgecolor='black', ncols=2, borderpad=.25, fontsize=8.5)
    fig.legend(handles=legends_ops, bbox_to_anchor=(0.74, 0.94),
               loc='center', edgecolor='black', ncols=2, borderpad=.25, fontsize=8.5)

os.makedirs("output-plots", exist_ok=True)
plt.savefig("output-plots/ycsb-uniform_64.pdf", format='pdf', bbox_inches='tight', pad_inches=0.01)
print(f"Figure generated successfully (Aggregate Mode: {AGGREGATE_METRICS})")

