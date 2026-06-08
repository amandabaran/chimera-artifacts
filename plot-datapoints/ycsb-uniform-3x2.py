#!/usr/bin/env python3

import os
import re
import sys
from prelude import plt
from matplotlib.ticker import *
from matplotlib.lines import Line2D

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
AGGREGATE_METRICS = True 
SERVERS_CONFIG = '3servers'

apps = [
    {'title': 'YCSB A - 50/50', 'letter': 'A', 'lat_max': 60, 'lat_step': 10, 'tput_max': 4.0,  'tput_step': 1.0},
    {'title': 'YCSB B - 95/5',  'letter': 'B', 'lat_max': 24, 'lat_step': 6,  'tput_max': 15.0, 'tput_step': 5.0},
    {'title': 'YCSB C - 100/0', 'letter': 'C', 'lat_max': 15, 'lat_step': 5,  'tput_max': 18.0, 'tput_step': 6.0}
]

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

# --- UNIFIED GRID GEOMETRY (Fixed spacing and breathing room) ---
fig, axes = plt.subplots(3, 2, figsize=(3.70, 4.25))
# Adjusted top to 0.89 to prevent title collision with legend; adjusted bottom to 0.10 to save X-axis text
fig.subplots_adjust(top=0.89, bottom=0.10, left=0.13, right=0.96, hspace=0.42, wspace=0.38)

# --- Processing & Plotting Loop ---
for row_idx, app in enumerate(apps):
    lat_axis = axes[row_idx, 0]  # Column 1: Latency
    tput_axis = axes[row_idx, 1] # Column 2: Throughput
    
    lat_axis.set_title(f"{app['title']} (Latency)", pad=4, fontsize=8.0)
    tput_axis.set_title(f"{app['title']} (Tput)", pad=4, fontsize=8.0)
    
    for s in schemes:
        valid_clients = []
        lat_points = []
        tput_points = []
        
        for nc in client_counts:
            get_ops, get_lat_sum = 0, 0
            upd_ops, upd_lat_sum = 0, 0
            total_tput = 0
            fusee_global_tput = None
            has_data = False
            
            for c in range(1, nc + 1):
                path = os.path.join("logs", "YCSB", f"workload-{app['letter']}", s, SERVERS_CONFIG, f"{nc}client", f"client{c}.txt")
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
                    
                if "aggregated tput" in data:
                    fusee_global_tput = data["aggregated tput"]
                else:
                    total_tput += data.get("local tput", 0)
            
            if has_data:
                valid_clients.append(nc)
                
                total_ops_recorded = get_ops + upd_ops
                avg_combined = ((get_lat_sum + upd_lat_sum) / total_ops_recorded) if total_ops_recorded > 0 else 0
                lat_points.append(avg_combined)
                
                if "FUSEE" in s.upper() and fusee_global_tput is not None:
                    final_tput = fusee_global_tput / 1000.0
                else:
                    final_tput = total_tput / 1000.0
                tput_points.append(final_tput)
                
        if valid_clients:
            if any(lat_points):
                lat_axis.plot(valid_clients, lat_points, color=schemes[s]['color'], 
                              linestyle=schemes[s]['lstyle'], linewidth=schemes[s]['lwidth'])
            if any(tput_points):
                tput_axis.plot(valid_clients, tput_points, color=schemes[s]['color'], 
                               linestyle=schemes[s]['lstyle'], linewidth=schemes[s]['lwidth'])

    # --- Row Boundaries and Specific Axis Tuning ---
    lat_axis.set_ylim(0, app['lat_max'])
    lat_axis.yaxis.set_major_locator(MultipleLocator(app['lat_step']))
    
    tput_axis.set_ylim(0, app['tput_max'])
    tput_axis.yaxis.set_major_locator(MultipleLocator(app['tput_step']))
    
    lat_axis.set_ylabel('Latency (μs)', labelpad=2, fontsize=7.5)
    tput_axis.set_ylabel('Tput (Mops)', labelpad=2, fontsize=7.5)
    
    # Apply X-labels explicitly to the bottom row
    if row_idx == 2:
        lat_axis.set_xlabel('Clients', labelpad=2, fontsize=7.5)
        tput_axis.set_xlabel('Clients', labelpad=2, fontsize=7.5)

# --- Grid & Labels Cleanup Pass ---
for row_idx, row in enumerate(axes):
    for subplot in row:
        subplot.tick_params(axis='both', which='major', pad=2.0, labelsize=7.5)
        subplot.yaxis.set_minor_locator(NullLocator())
        subplot.xaxis.set_minor_locator(NullLocator())
        
        subplot.set_xlim(0, MAX_CLIENTS + 4)
        subplot.xaxis.set_major_locator(MultipleLocator(16))
        
        # FIX: Ensure label visibility behaves cleanly on shared-looking grids
        if row_idx < 2:
            subplot.tick_params(labelbottom=False)
        else:
            subplot.tick_params(labelbottom=True)
            
        subplot.grid(True, which='major', axis='both', linestyle='--', linewidth=0.5, alpha=0.7)
        subplot.set_axisbelow(True)

# --- Fixed Global Shared Legend Box (Repositioned to fully eliminate frame cutoff) ---
leg_scheme = fig.legend(handles=legends_schemes, bbox_to_anchor=(0.54, 0.95), 
                        loc='center', edgecolor='black', ncols=4, 
                        borderpad=.20, handletextpad=0.5, fontsize=7.5)

# --- Save Unified Matrix ---
os.makedirs("output-plots", exist_ok=True)
plt.savefig("output-plots/ycsb-unified-matrix.pdf", format='pdf', bbox_inches='tight', pad_inches=0.01)
print("Saved matrix layout with fixed spacing successfully.")