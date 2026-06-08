#!/usr/bin/env python3

import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt  # Changed prelude to standard plt, change back if needed
from matplotlib.ticker import *
from matplotlib.patches import Patch

# --- Unified Log Parser Function ---
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
            elif "aggregated tput:" in clean:
                match = re.search(r"aggregated tput:\s*(\d+)", clean)
                if match:
                    out["aggregated tput"] = int(match.group(1))
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

# --- Configuration & Styling Specs ---
# Adjust limits here based on your scaling performance data
apps = [
    {'title': 'YCSB A (50/50)', 'letter': 'A', 'lat_max': 40, 'lat_step': 10, 'tput_max': 4.0,  'tput_step': 1.0},
    {'title': 'YCSB B (95/5)',  'letter': 'B', 'lat_max': 40, 'lat_step': 10, 'tput_max': 10.0, 'tput_step': 2.0}
]

reg_counts = ['100reg', '1000reg', '10000reg', '100000reg']
x_labels = ['100', '1K', '10K', '100K']
x_indexes = np.arange(len(reg_counts))

scheme_colors = {
    'SWARM-KV': '#3b8df8', 
    'CHIMERA':  '#0bab0b', 
    'DM-ABD':   '#d11414', 
    'FUSEE':    '#f4860b', 
}

TARGET_CLIENTS = 32 

# --- Tight Bar Geometry ---
num_schemes = len(scheme_colors)
total_group_width = 0.85  
bar_width = total_group_width / num_schemes

# --- Build Layout ---
# Returned to the 2x2 grid layout 
fig, axes = plt.subplots(2, 2, figsize=(4.60, 3.40))
fig.subplots_adjust(top=0.84, bottom=0.11, left=0.12, right=0.97, hspace=0.35, wspace=0.25)

# --- Processing & Plotting Loop ---
for col_idx, app in enumerate(apps):
    lat_ax = axes[0, col_idx]  
    tput_ax = axes[1, col_idx] 
    
    lat_ax.set_title(app['title'], pad=10, fontsize=8.5)
    
    data_matrix = {s: {'lat': [], 'tput': []} for s in scheme_colors.keys()}
    
    for reg_str in reg_counts:
        for s in scheme_colors.keys():
            get_ops, get_lat_sum = 0, 0
            upd_ops, upd_lat_sum = 0, 0
            total_tput = 0
            fusee_global_tput = None
            has_data = False
            
            for c in range(1, TARGET_CLIENTS + 1):
                # Dynamically maps to workload-A or workload-B, using reg-scaling folders
                path = os.path.join("logs", "reg-scaling", f"workload-{app['letter']}", s, reg_str, "3servers", f"{TARGET_CLIENTS}client", f"client{c}.txt")
                if not os.path.exists(path):
                    print(f"Missing file: {path}")
                    continue
                
                data = parse_chimera_native(path)
                has_data = True
                
                if 'GET' in data:
                    get_ops += data['GET'].get('pcount', 0)
                    get_lat_sum += data['GET'].get('psum', 0)
                if 'UPDATE' in data:
                    upd_ops += data['UPDATE'].get('pcount', 0)
                    upd_lat_sum += data['UPDATE'].get('psum', 0)
                    
                if "aggregated tput" in data:
                    fusee_global_tput = data["aggregated tput"]
                else:
                    total_tput += data.get("local tput", 0)
                
            if has_data:
                total_ops = get_ops + upd_ops
                avg_lat = (get_lat_sum + upd_lat_sum) / total_ops if total_ops > 0 else 0
                data_matrix[s]['lat'].append(avg_lat)
                
                if "FUSEE" in s.upper() and fusee_global_tput is not None:
                    final_tput = fusee_global_tput / 1000.0
                else:
                    final_tput = total_tput / 1000.0
                data_matrix[s]['tput'].append(final_tput)
            else:
                data_matrix[s]['lat'].append(0)
                data_matrix[s]['tput'].append(0)

    # --- Sequentially Plot Dynamic Bars Side-by-Side ---
    for idx, s in enumerate(scheme_colors.keys()):
        offset = (idx - (num_schemes - 1) / 2) * bar_width
        
        lat_ax.bar(x_indexes + offset, data_matrix[s]['lat'], width=bar_width, 
                   color=scheme_colors[s], edgecolor='black', linewidth=0.5)
                   
        tput_ax.bar(x_indexes + offset, data_matrix[s]['tput'], width=bar_width, 
                   color=scheme_colors[s], edgecolor='black', linewidth=0.5)

    # --- Structural Adjustments & Trimming Plot Margins ---
    for ax in [lat_ax, tput_ax]:
        ax.set_xticks(x_indexes)
        ax.set_xlim(-0.5, len(reg_counts) - 0.5)
        ax.tick_params(axis='both', labelsize=7.5, pad=1.5)
        ax.grid(True, axis='y', linestyle='--', linewidth=0.4, alpha=0.5)
        ax.set_axisbelow(True)

    # Format Y ranges
    lat_ax.set_ylim(0, app['lat_max'])
    lat_ax.yaxis.set_major_locator(MultipleLocator(app['lat_step']))
    lat_ax.set_xticklabels([]) 
    
    tput_ax.set_ylim(0, app['tput_max'])
    tput_ax.yaxis.set_major_locator(MultipleLocator(app['tput_step']))
    tput_ax.set_xticklabels(x_labels, fontsize=8.0)
    tput_ax.set_xlabel('Registers', fontsize=8.5, labelpad=2)

    # Labels strictly on the outer perimeter column
    if col_idx == 0:
        lat_ax.set_ylabel('Latency (μs)', labelpad=1, fontsize=8)
        tput_ax.set_ylabel('Tput (Mops)', labelpad=1, fontsize=8)

# --- Construct Global Dynamic Legend ---
legend_patches = [
    Patch(facecolor=color, edgecolor='black', linewidth=0.5, label=s) 
    for s, color in scheme_colors.items()
]

# Grid calculation bounds for legend matches original layout
fig.legend(handles=legend_patches, bbox_to_anchor=(0.54, 0.95), loc='center', 
           edgecolor='black', ncols=num_schemes, borderpad=.20, handletextpad=0.4, 
           columnspacing=1.0, fontsize=8.0)

# --- Save Visuals ---
os.makedirs("output-plots", exist_ok=True)
fig.savefig("output-plots/reg_scaling_new.pdf", format='pdf', bbox_inches='tight', pad_inches=0.01)

print("Saved combined figure with separated legend and subplot titles.")