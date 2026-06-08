#!/usr/bin/env python3

import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import *
from matplotlib.lines import Line2D

# --- Unified Workload E Log Parser ---
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
            elif current_op and ("avg:" in clean or "average latency:" in clean):
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
LAT_MAX, LAT_STEP = 40, 10      
TPUT_MAX, TPUT_STEP = 20.0, 4.0

# Focus folders & target labels
range_sizes = ['range2', 'range4', 'range8', 'range16', 'range32']
x_labels = ['2', '4', '8', '16', '32']
x_indexes = np.arange(len(range_sizes))

# Trimmed down styling configuration to only target SWARM-KV and CHIMERA
scheme_colors = {
    'SWARM-KV': '#3b8df8', 
    'CHIMERA':  '#0bab0b', 
}

scheme_markers = {
    'SWARM-KV': 'o', 
    'CHIMERA':  's', 
}

TARGET_CLIENTS = 32 

# --- Build Canvas Layout (1x2 Plot) ---
fig, axes = plt.subplots(1, 2, figsize=(4, 1.75))
fig.subplots_adjust(top=0.76, bottom=0.22, left=0.12, right=0.96, wspace=0.35)

lat_ax = axes[0]
tput_ax = axes[1]

lat_ax.set_title("Scan Latency", pad=6, fontsize=8.5)
tput_ax.set_title("Throughput", pad=6, fontsize=8.5)

# --- Data Arrays Initialization ---
data_matrix = {s: {'lat': [], 'tput': []} for s in scheme_colors.keys()}

# --- Processing Loop ---
for rng_str in range_sizes:
    for s in scheme_colors.keys():
        range_node_lats = []
        total_tput = 0
        fusee_global_tput = None
        has_data = False
        
        for c in range(1, TARGET_CLIENTS + 1):
            path = os.path.join("logs", "rq_sizes", "workload-E", s, rng_str, "3servers", f"{TARGET_CLIENTS}client", f"client{c}.txt")
            if not os.path.exists(path):
                print(f"Warning: Missing log file {path}, skipping...")
                continue
            
            data = parse_chimera_native(path)
            has_data = True
            
            # Target scan operations
            for op_type in ['RANGE', 'GET']:
                if op_type in data:
                    val = None
                    if data[op_type]['avg'] is not None:
                        val = data[op_type]['avg']
                    elif data[op_type]['pcount'] > 0:
                        val = data[op_type]['psum'] / data[op_type]['pcount']
                    
                    if val is not None:
                        range_node_lats.append(val)
            
            if "aggregated tput" in data:
                fusee_global_tput = data["aggregated tput"]
            else:
                total_tput += data.get("local tput", 0)
                
        if has_data:
            avg_lat = sum(range_node_lats) / len(range_node_lats) if range_node_lats else 0
            data_matrix[s]['lat'].append(avg_lat)
            
            if "FUSEE" in s.upper() and fusee_global_tput is not None:
                final_tput = fusee_global_tput / 1000.0
            else:
                final_tput = total_tput / 1000.0
            data_matrix[s]['tput'].append(final_tput)
        else:
            data_matrix[s]['lat'].append(np.nan)
            data_matrix[s]['tput'].append(np.nan)

# --- Line Plot Generation ---
for s in scheme_colors.keys():
    lat_ax.plot(x_indexes, data_matrix[s]['lat'], color=scheme_colors[s], 
                marker=scheme_markers[s], markersize=3.5, linewidth=1.1)
               
    tput_ax.plot(x_indexes, data_matrix[s]['tput'], color=scheme_colors[s], 
                marker=scheme_markers[s], markersize=3.5, linewidth=1.1)

# --- Ticks and Layout Styling ---
for ax in [lat_ax, tput_ax]:
    ax.set_xticks(x_indexes)
    ax.set_xticklabels(x_labels, fontsize=7.5)
    ax.set_xlim(-0.2, len(range_sizes) - 0.8)
    ax.tick_params(axis='both', which='major', pad=2.0, labelsize=7.5)
    ax.grid(True, linestyle='--', linewidth=0.4, alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel('Range Size', labelpad=2, fontsize=8.0)

lat_ax.set_ylim(0, LAT_MAX)
lat_ax.yaxis.set_major_locator(MultipleLocator(LAT_STEP))
lat_ax.set_ylabel('Latency (μs)', labelpad=2, fontsize=8.0)

tput_ax.set_ylim(0, TPUT_MAX)
tput_ax.yaxis.set_major_locator(MultipleLocator(TPUT_STEP))
tput_ax.set_ylabel('Tput (Mops)', labelpad=2, fontsize=8.0)

# --- Global Top Legend Context (Only 2 columns now) ---
legend_elements = [
    Line2D([0], [0], color=color, marker=scheme_markers[s], markersize=3.5, linewidth=1.1, label=s)
    for s, color in scheme_colors.items()
]

fig.legend(handles=legend_elements, bbox_to_anchor=(0.54, 0.94), loc='center', 
           edgecolor='black', ncols=len(scheme_colors), borderpad=.20, handletextpad=0.4, 
           columnspacing=1.0, fontsize=7.5)

# --- Save Figure Pass ---
os.makedirs("output-plots", exist_ok=True)
output_path = "output-plots/range-size-scaling.pdf"
fig.savefig(output_path, format='pdf', bbox_inches='tight', pad_inches=0.01)

print(f"Plot filtered for SWARM-KV and CHIMERA and saved to: {output_path}")