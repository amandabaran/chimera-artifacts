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
            
            # 1. Capture operation blocks safely across frameworks
            if "get stats" in clean:
                current_op = "GET"
                out[current_op] = {'pcount': 0, 'psum': 0}
            elif "update stats" in clean or "put stats" in clean:
                current_op = "UPDATE"
                out[current_op] = {'pcount': 0, 'psum': 0}
                
            # 2. Extract Throughput (Handles "kops", "kpos", and plain integer counts)
            elif "local tput:" in clean or "throughput:" in clean:
                match = re.search(r"(?:local tput|throughput):\s*(\d+)", clean)
                if match:
                    out["local tput"] = int(match.group(1))
            elif "aggregated tput:" in clean:
                match = re.search(r"aggregated tput:\s*(\d+)", clean)
                if match:
                    out["local tput"] = int(match.group(1))

            # 3. DIRECT AVERAGE PARSING: Grab the exact average reported by the system
            elif current_op and "average latency:" in clean:
                match = re.search(r"average latency:\s*([0-9.]+)\s*(us|ns)", clean)
                if match:
                    val = float(match.group(1))
                    unit = match.group(2)
                    
                    # Convert everything uniformly to microseconds for the graph
                    latency_us = val if unit == "us" else val / 1000.0
                    
                    # Inject a weight of 1 so downstream mathematical consolidation functions cleanly
                    out[current_op]['pcount'] = 1
                    out[current_op]['psum'] = latency_us
                        
    return out

# ─── CONFIGURATION ──────────────────────────────────────────────────
AGGREGATE_METRICS = False 
SERVERS_CONFIG = '3servers'

apps = {
    'YCSB A - 50/50' : 'A',
    'YCSB B - 95/5'  : 'B',
    # 'YCSB C - 100/0' : 'C',  # Commented out safely as requested
}

schemes = {
    'SWARM-KV': { 'label': 'SWARM-KV', 'color': '#3b8df8', 'lstyle': '-',  'lwidth': 0.9 },
    'CHIMERA':  { 'label': 'CHIMERA',  'color': '#0bab0b', 'lstyle': '--', 'lwidth': 1.2 },
    'DM-ABD':   { 'label': 'DM-ABD',   'color': '#d11414', 'lstyle': '--', 'lwidth': 1.0 },
    'FUSEE':    { 'label': 'FUSEE',    'color': '#f4860b', 'lstyle': ':',  'lwidth': 1.4 },
}

ops = { 'GET': 'o', 'UPDATE': 'd' }
client_counts = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64]
MAX_CLIENTS = max(client_counts)

# ─── LEGEND CONSTRUCTIONS ──────────────────────────────────────────
legends_schemes = [
    Line2D([0], [0], color=schemes[s]['color'], linestyle=schemes[s]['lstyle'],
           linewidth=schemes[s]['lwidth'], label=schemes[s]['label']) for s in schemes
]

legends_ops = [] if AGGREGATE_METRICS else [
    Line2D([], [], color='black', marker=ops['GET'], linestyle='none', markersize=5, label='GET'),
    Line2D([], [], color='black', marker=ops['UPDATE'], linestyle='none', markersize=5, label='PUT')
]

# ─── DYNAMIC SUBPLOT LAYOUT GENERATOR ──────────────────────────────
num_apps = len(apps)
fig, subplots = plt.subplots(1, num_apps, figsize=(1.8 * num_apps, 1.45))

if num_apps == 1:
    subplots = [subplots]

fig.subplots_adjust(top=0.76, bottom=0.22, left=0.11, right=0.98, wspace=0.32)

for plot in subplots:
    plot.tick_params(axis='both', which='major', pad=2.0)

# Workload-Specific dynamic axis parameters mapping
y_limits = {
    'A': (0, 100, 25), 
    'B': (0, 60, 15),  
    'C': (0, 30, 10)   
}

# ─── MAIN DATA RETRIEVAL AND PROCESSING LOOP ───────────────────────
for col_idx, (app_title, workload_letter) in enumerate(apps.items()):
    subplot = subplots[col_idx]
    subplot.set_title(app_title, pad=5, fontsize=8)
    
    # Configure exact dynamic bound allocations
    if workload_letter in y_limits:
        ymin, ymax, ystep = y_limits[workload_letter]
        subplot.set_ylim(ymin, ymax)
        subplot.yaxis.set_major_locator(MultipleLocator(ystep))
    
    for s in schemes:
        valid_clients = []
        metrics = { 'COMBINED': [], 'GET': [], 'UPDATE': [] }
        
        # --- 1. DATA COLLECTION PASS ---
        for nc in client_counts:
            get_ops, get_lat_sum = 0, 0
            upd_ops, upd_lat_sum = 0, 0
            has_data = False
            
            target_dir = os.path.join("logs", "YCSB", f"workload-{workload_letter}", s, SERVERS_CONFIG, f"{nc}client")
            
            # STRICT GUARD 1: Directory Existence Check
            if not os.path.exists(target_dir):
                sys.exit(f"\n[CRITICAL] Missing execution directory for scheme '{s}'!\nPath: {target_dir}")
            
            client_files = [f for f in os.listdir(target_dir) if f.startswith("client") and f.endswith(".txt")]
            
            # STRICT GUARD 2: Empty Directory Verification
            if not client_files:
                sys.exit(f"\n[CRITICAL] No client text profiles populated inside directory!\nPath: {target_dir}")
                
            # STRICT GUARD 3: Complete Cluster Run Matrix Verification 
            if len(client_files) < nc:
                sys.exit(f"\n[CRITICAL] Matrix degradation detected for '{s}' at {nc} clients!\n"
                         f"Expected: {nc} log files. Found: {len(client_files)} files.\n"
                         f"Path: {target_dir}")
            
            has_data = True
            for filename in client_files:
                path = os.path.join(target_dir, filename)
                data = parse_chimera_native(path)
                
                # STRICT GUARD 4: Corrupt Log / Parser Mismatch Validation
                if 'GET' not in data and 'UPDATE' not in data:
                    sys.exit(f"\n[CRITICAL] File returned zero valid metric keys!\nPath: {path}")
                
                if 'GET' in data:
                    get_ops += data['GET'].get('pcount', 0)
                    get_lat_sum += data['GET'].get('psum', 0)
                if 'UPDATE' in data:
                    upd_ops += data['UPDATE'].get('pcount', 0)
                    upd_lat_sum += data['UPDATE'].get('psum', 0)
            
            if has_data:
                valid_clients.append(nc)
                avg_get = (get_lat_sum / get_ops) if get_ops > 0 else 0
                avg_upd = (upd_lat_sum / upd_ops) if upd_ops > 0 else 0
                
                if AGGREGATE_METRICS:
                    total_ops_recorded = get_ops + upd_ops
                    avg_combined = ((get_lat_sum + upd_lat_sum) / total_ops_recorded) if total_ops_recorded > 0 else 0
                    metrics['COMBINED'].append(avg_combined)
                else:
                    metrics['GET'].append(avg_get)
                    metrics['UPDATE'].append(avg_upd)
                
        # --- 2. RENDER PLOT PASS ---
        if valid_clients:
            ops_to_plot = ['COMBINED'] if AGGREGATE_METRICS else ['GET', 'UPDATE']
            for op in ops_to_plot:
                data_points = metrics[op]
                if not any(data_points) or (workload_letter == 'C' and op == 'UPDATE'):
                    continue
                
                # Line style matches the scheme layout configuration uniformly
                line_style = schemes[s]['lstyle']
                
                if AGGREGATE_METRICS:
                    marker_style = None
                    mark_points = None
                else:
                    marker_style = ops[op]
                    # --- FILTER MARKERS TO SPECIFIC TICK PLACEMENTS ONLY ---
                    target_ticks = [16, 32, 48, 64]
                    mark_points = [valid_clients.index(c) for c in target_ticks if c in valid_clients]

                subplot.plot(
                    valid_clients, data_points, 
                    color=schemes[s]['color'], 
                    linestyle=line_style, 
                    linewidth=schemes[s]['lwidth'], 
                    marker=marker_style, 
                    markevery=mark_points,
                    markersize=3.5, 
                    alpha=0.9
                )

# ─── GLOBAL VISUAL CLEANUP PASS ────────────────────────────────────
for subplot in subplots:
    subplot.yaxis.set_minor_locator(NullLocator())
    subplot.xaxis.set_minor_locator(NullLocator())
    subplot.set_xlim(0, MAX_CLIENTS + 4)
    subplot.xaxis.set_major_locator(MultipleLocator(16))
    subplot.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5, alpha=0.7)
    subplot.set_axisbelow(True)
    subplot.set_xlabel('Clients', labelpad=2, fontsize=8)

subplots[0].set_ylabel('Latency (μs)', labelpad=3)

# ─── UNIFIED LEGEND CORRELATION PLACEMENT ──────────────────────────
leg_scheme = fig.legend(
    handles=legends_schemes, 
    bbox_to_anchor=(0.04, 0.94),  
    loc='center left',            
    edgecolor='black', 
    ncols=4, 
    borderpad=0.2, 
    handletextpad=0.3,            
    columnspacing=0.5,            
    fontsize=7.0                  
)

leg_ops = fig.legend(
    handles=legends_ops, 
    bbox_to_anchor=(0.98, 0.94),  
    loc='center right', 
    edgecolor='black', 
    ncols=1, 
    borderpad=0.15,               
    handletextpad=0.2, 
    labelspacing=0.15,            
    fontsize=6.0                  
)

# ─── FILE EXPORT ───────────────────────────────────────────────────
os.makedirs("output-plots", exist_ok=True)
plt.savefig("output-plots/ycsb-latency-split.pdf", format='pdf', bbox_inches='tight', pad_inches=0.01)
print(f"Validated complete run successfully. Output plot rendered safely.")