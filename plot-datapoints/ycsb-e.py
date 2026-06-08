#!/usr/bin/env python3

import os
import re
import sys
import numpy as np
from prelude import plt
from matplotlib.ticker import *
from matplotlib.lines import Line2D

# --- Dynamic Layout and Toggle Switch Configurations ---
TOGGLE_COMBINED_AVERAGE = False    # Set to False to show separated lines (Range vs Update)
PLOT_MODE = 'both'                # Options: 'latency', 'throughput', or 'both'

# --- Log Parser Function ---
def parse_chimera_native(path):
    out = {}
    current_op = None
    if not os.path.exists(path):
        return out
    with open(path, 'r') as f:
        for line in f:
            if "range op for keys" in line.lower():
                continue
                
            clean = line.strip().lower()
            
            # Catch Macro Scan Latency lines directly (e.g., SWARM-KV format)
            if "average macro scan latency:" in clean:
                match = re.search(r"average macro scan latency:\s*([0-9.]+)\s*(ms|us|ns)", clean)
                if match:
                    val = float(match.group(1))
                    unit = match.group(2)
                    if unit == "ms":
                        latency_us = val * 1000.0
                    elif unit == "ns":
                        latency_us = val / 1000.0
                    else:
                        latency_us = val
                    
                    if "RANGE" not in out:
                        out["RANGE"] = {'pcount': 0, 'psum': 0, 'avg': None}
                    out["RANGE"]['avg'] = latency_us
                continue

            # Detect target operation metrics
            if "scan stats:" in clean or "range stats:" in clean or "search stats:" in clean:
                current_op = "RANGE"
                if current_op not in out:
                    out[current_op] = {'pcount': 0, 'psum': 0, 'avg': None}
            elif "get stats:" in clean:
                current_op = "GET"
                if current_op not in out:
                    out[current_op] = {'pcount': 0, 'psum': 0, 'avg': None}
            elif "update stats:" in clean or "put stats:" in clean:
                current_op = "UPDATE"
                if current_op not in out:
                    out[current_op] = {'pcount': 0, 'psum': 0, 'avg': None}
            
            # Directly capture an average value if printed by the benchmark framework
            elif current_op and "avg:" in clean or "average latency:" in clean:
                match = re.search(r"(?:avg|average latency):\s*([0-9.]+)\s*(ms|us|ns)", clean)
                if match:
                    val = float(match.group(1))
                    unit = match.group(2)
                    if unit == "ms":
                        lat = val * 1000.0
                    else:
                        lat = val if unit == "us" else val / 1000.0
                    
                    if out[current_op]['avg'] is None:
                        out[current_op]['avg'] = lat
            
            elif "local tput:" in clean:
                match = re.search(r"local tput:\s*(\d+)", clean)
                if match:
                    out["local tput"] = int(match.group(1))
            elif "aggregated tput:" in clean:
                match = re.search(r"aggregated tput:\s*(\d+)", clean)
                if match:
                    out["aggregated tput"] = int(match.group(1))
                    
            # Fallback mathematical approximation using bucketed percentile targets
            elif current_op and "%:" in clean:
                match = re.search(r"([0-9.]+)\s*%:\s*([0-9.]+)\s*(us|ns)", clean)
                if match:
                    perc = float(match.group(1))
                    val = float(match.group(2))
                    unit = match.group(3)
                    latency_us = val if unit == "us" else val / 1000.0
                    out[current_op][perc] = latency_us
                    out[current_op]['pcount'] += 1
                    out[current_op]['psum'] += latency_us
    return out

# --- Configuration & Styling Specs ---
SERVERS_CONFIG = '3servers'
WORKLOAD_LETTER = 'E'

LAT_MAX, LAT_STEP = 50, 10
TPUT_MAX, TPUT_STEP = 15.0, 3.0

schemes = {
    'SWARM-KV': { 'label': 'SWARM-KV', 'color': '#3b8df8', 'linestyle': '-' },
    'CHIMERA':  { 'label': 'CHIMERA',  'color': '#0bab0b', 'linestyle': '--' },
}

client_counts = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64]
MAX_CLIENTS = max(client_counts)

# Identify target horizontal grid intervals for rendering markers
TARGET_TICKS = [16, 32, 48, 64]

# --- Dual Legend Construction ---
# 1. System Legend (Color & Line Style)
legends_systems = [
    Line2D([0], [0], color=schemes[s]['color'], linestyle=schemes[s]['linestyle'], 
           linewidth=1.1, label=schemes[s]['label']) for s in schemes
]

# 2. Operation Legend (Markers only, kept neutral grey)
legends_ops = [
    Line2D([0], [0], color='#7f7f7f', linestyle='None', marker='s', markersize=3.5, label='Range'),
    Line2D([0], [0], color='#7f7f7f', linestyle='None', marker='d', markersize=3.5, label='Put')
]

# --- Geometric Subplot Canvas Instantiation Pass ---
PLOT_MODE = PLOT_MODE.lower().strip()
if PLOT_MODE == 'both':
    fig, axes = plt.subplots(1, 2, figsize=(4, 1.75))
    fig.subplots_adjust(top=0.72, bottom=0.24, left=0.10, right=0.96, wspace=0.35)
    lat_axis = axes[0]
    tput_axis = axes[1]
    active_axes = [lat_axis, tput_axis]
elif PLOT_MODE == 'latency':
    fig, ax = plt.subplots(1, 1, figsize=(2.40, 1.75))
    fig.subplots_adjust(top=0.72, bottom=0.24, left=0.18, right=0.95)
    lat_axis = ax
    tput_axis = None
    active_axes = [ax]
elif PLOT_MODE == 'throughput':
    fig, ax = plt.subplots(1, 1, figsize=(2.40, 1.75))
    fig.subplots_adjust(top=0.72, bottom=0.24, left=0.18, right=0.95)
    lat_axis = None
    tput_axis = ax
    active_axes = [ax]
else:
    print(f"Error: Invalid PLOT_MODE value '{PLOT_MODE}'. Select 'latency', 'throughput', or 'both'.")
    sys.exit(1)

if lat_axis:
    lat_axis.set_title("Overall Average Latency" if TOGGLE_COMBINED_AVERAGE else "Latency by Operation", pad=5, fontsize=8.5)
if tput_axis:
    tput_axis.set_title("Throughput", pad=5, fontsize=8.5)

# --- Data Loading and Processing Loop ---
for s in schemes:
    valid_clients = []
    range_lat_points = []
    upd_lat_points = []
    combined_lat_points = []
    tput_points = []
    
    ls = schemes[s]['linestyle']
    col = schemes[s]['color']
    
    for nc in client_counts:
        range_node_lats = []
        upd_node_lats = []
        all_node_lats = []
        total_tput = 0
        fusee_global_tput = None
        has_data = False
        
        for c in range(1, nc + 1):
            path = os.path.join("logs", "YCSB", f"workload-{WORKLOAD_LETTER}", s, SERVERS_CONFIG, f"{nc}client", f"client{c}.txt")
            if not os.path.exists(path):
                continue
            
            data = parse_chimera_native(path)
            has_data = True
            
            # --- Extract Independent Range Metrics ---
            for op_type in ['RANGE', 'GET']:
                if op_type in data:
                    val = None
                    if data[op_type]['avg'] is not None:
                        val = data[op_type]['avg']
                    elif data[op_type]['pcount'] > 0:
                        val = data[op_type]['psum'] / data[op_type]['pcount']
                    
                    if val is not None:
                        range_node_lats.append(val)
                        all_node_lats.append(val)
            
            # --- Extract Independent Update Metrics ---
            if 'UPDATE' in data:
                val = None
                if data['UPDATE']['avg'] is not None:
                    val = data['UPDATE']['avg']
                elif data['UPDATE']['pcount'] > 0:
                    val = data['UPDATE']['psum'] / data['UPDATE']['pcount']
                
                if val is not None:
                    upd_node_lats.append(val)
                    all_node_lats.append(val)
                    
            # Throughput Parsing
            if "aggregated tput" in data:
                fusee_global_tput = data["aggregated tput"]
            else:
                total_tput += data.get("local tput", 0)
        
        if has_data:
            valid_clients.append(nc)
            
            if TOGGLE_COMBINED_AVERAGE:
                avg_comb = sum(all_node_lats) / len(all_node_lats) if all_node_lats else 0
                combined_lat_points.append(avg_comb)
            else:
                avg_range = sum(range_node_lats) / len(range_node_lats) if range_node_lats else 0
                avg_upd = sum(upd_node_lats) / len(upd_node_lats) if upd_node_lats else 0
                range_lat_points.append(avg_range)
                upd_lat_points.append(avg_upd)
            
            if "FUSEE" in s.upper() and fusee_global_tput is not None:
                final_tput = fusee_global_tput / 1000.0
            else:
                final_tput = total_tput / 1000.0
            tput_points.append(final_tput)
            
    if valid_clients:
        # Match markevery locations against what data actually successfully processed
        current_markevery = [i for i, nc in enumerate(valid_clients) if nc in TARGET_TICKS]
        
        if lat_axis:
            if TOGGLE_COMBINED_AVERAGE:
                if any(combined_lat_points):
                    lat_axis.plot(valid_clients, combined_lat_points, color=col, 
                                  linestyle=ls, linewidth=1.1, marker='s', markersize=3.5,
                                  markevery=current_markevery)
            else:
                if any(range_lat_points):
                    lat_axis.plot(valid_clients, range_lat_points, color=col, 
                                  linestyle=ls, linewidth=1.1, marker='s', markersize=3.5,
                                  markevery=current_markevery)
                if any(upd_lat_points):
                    lat_axis.plot(valid_clients, upd_lat_points, color=col, 
                                  linestyle=ls, linewidth=1.1, marker='d', markersize=3.5,
                                  markevery=current_markevery)
            
        # Clean line path plotting for throughput with marker configurations disabled
        if tput_axis and any(tput_points):
            tput_axis.plot(valid_clients, tput_points, color=col, 
                           linestyle=ls, linewidth=1.1)

# --- Tuning and Clean Grid Pass ---
if lat_axis:
    lat_axis.set_ylim(0, LAT_MAX)
    lat_axis.yaxis.set_major_locator(MultipleLocator(LAT_STEP))
    lat_axis.set_ylabel('Latency (μs)', labelpad=3, fontsize=8.0)

if tput_axis:
    tput_axis.set_ylim(0, TPUT_MAX)
    tput_axis.yaxis.set_major_locator(MultipleLocator(TPUT_STEP))
    tput_axis.set_ylabel('Tput (Mops)', labelpad=3, fontsize=8.0)

for subplot in active_axes:
    subplot.tick_params(axis='both', which='major', pad=2.0, labelsize=7.5)
    subplot.yaxis.set_minor_locator(NullLocator())
    subplot.xaxis.set_minor_locator(NullLocator())
    
    subplot.set_xlim(0, MAX_CLIENTS + 4)
    subplot.xaxis.set_major_locator(MultipleLocator(16))
    subplot.set_xlabel('Clients', labelpad=2, fontsize=8.0)
    
    subplot.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5, alpha=0.7)
    subplot.set_axisbelow(True)

# --- Dynamic Multi-Legend Positioning Pass ---
legend_y_anchor = 0.93 if PLOT_MODE == 'both' else 0.94

# Add System Schemes Legend on the Left Side
leg_sys = fig.legend(handles=legends_systems, bbox_to_anchor=(0.10, legend_y_anchor), 
                     loc='center left', edgecolor='black', ncols=len(legends_systems), 
                     columnspacing=0.8, handletextpad=0.4, fontsize=7.0)

# Add Operation Style Legend on the Right Side (explicitly adding back to the canvas context)
leg_ops = fig.legend(handles=legends_ops, bbox_to_anchor=(0.96, legend_y_anchor), 
                     loc='center right', edgecolor='black', ncols=len(legends_ops), 
                     columnspacing=0.8, handletextpad=0.4, fontsize=7.0)
fig.add_artist(leg_sys)

# --- Save Plot ---
os.makedirs("output-plots", exist_ok=True)
avg_suffix = "combined" if TOGGLE_COMBINED_AVERAGE else "separated"
filename = f"ycsb-workload-e-{PLOT_MODE}-{avg_suffix}.pdf"
output_path = f"output-plots/{filename}"

plt.savefig(output_path, format='pdf', bbox_inches='tight', pad_inches=0.01)
print(f"Saved mode [{PLOT_MODE.upper()}] to: {output_path}")