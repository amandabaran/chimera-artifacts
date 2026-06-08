#!/usr/bin/env python3

import os
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# --- Comprehensive Log Parser ---
def parse_ml_performance(path):
    """
    Parses a single log file to extract:
      - Latency metrics for RANGE and PUT blocks.
      - Total duration and operations to calculate individual throughputs.
    """
    metrics = {
        'range_lats': [],
        'put_lats': [],
        'range_ops': 0,
        'put_ops': 0,
        'duration': 0.0
    }
    
    if not os.path.exists(path):
        return metrics
        
    inside_block = None
    
    with open(path, 'r') as f:
        for line in f:
            clean = line.strip().lower()
            
            # 1. Track stats blocks
            if "######## range stats:" in clean:
                inside_block = "range"
                continue
            elif "######## put stats:" in clean:
                inside_block = "put"
                continue
            elif "########" in clean and "stats:" in clean:
                inside_block = None
                continue
                
            # 2. Extract number of measurements (ops) per block
            if inside_block and "number of measurements:" in clean:
                match = re.search(r"measurements:\s*([0-9.]+)", clean)
                if match:
                    ops_count = int(float(match.group(1)))
                    metrics[f"{inside_block}_ops"] = ops_count
                    
            # 3. Collect percentiles
            if inside_block and "%:" in clean:
                match = re.search(r"([0-9.]+)\s*%:\s*([0-9.]+)\s*(us|ns)", clean)
                if match:
                    val = float(match.group(2))
                    unit = match.group(3)
                    latency_us = val if unit == "us" else val / 1000.0
                    metrics[f"{inside_block}_lats"].append(latency_us)
            
            # 4. Extract total duration
            if "ml-tracker-results:" in clean or "ml-worker-results:" in clean:
                match = re.search(r"duration_sec=([0-9.]+)", clean)
                if match:
                    metrics['duration'] = float(match.group(1))
                    
    return metrics

# =========================================================================
# --- FLEXIBLE CONFIGURATION MATRIX ---
# =========================================================================
X_THREADS = [2, 4, 8, 16]
LOG_BASE_DIR = "logs/ML/CHIMERA/3servers"

# Visual Theme Hex Colors
COLOR_PRIMARY = '#2ca02c'   # Green (Overall)
COLOR_RANGE = '#1f77b4'     # Blue (Range/Tracker Ops)
COLOR_PUT = '#d11414'       # Crimson Red (Put/Worker Ops)

# --- Build Layout (2x2 Grid) ---
fig, axes = plt.subplots(2, 2, figsize=(6.5, 5.0))
fig.subplots_adjust(top=0.90, bottom=0.12, left=0.12, right=0.95, hspace=0.32, wspace=0.28)

ax_lat_overall  = axes[0, 0]
ax_lat_internal = axes[0, 1]
ax_tput_overall = axes[1, 0]
ax_tput_internal = axes[1, 1]

# Set Titles
ax_lat_overall.set_title("Overall Latency", fontsize=9.5, fontweight='bold', pad=8)
ax_lat_internal.set_title("Operation Latency", fontsize=9.5, fontweight='bold', pad=8)
ax_tput_overall.set_title("Overall Throughput", fontsize=9.5, fontweight='bold', pad=8)
ax_tput_internal.set_title("Operation Throughput", fontsize=9.5, fontweight='bold', pad=8)

# --- Data Arrays ---
y_overall_lat, y_overall_tput = [], []
y_range_lat, y_put_lat = [], []
y_range_tput, y_put_tput_agg = [], []

# --- Data Extraction Loop ---
for thread_count in X_THREADS:
    folder = f"{thread_count}client"
    
    # 1. Tracker Metrics (Client 1)
    tracker_path = os.path.join(LOG_BASE_DIR, folder, "client1.txt")
    if not os.path.exists(tracker_path):
        tracker_path = os.path.join(LOG_BASE_DIR, folder, "client1.log")
        
    t_data = parse_ml_performance(tracker_path)
    
    # Range Latency & Throughput
    avg_range_lat = np.mean(t_data['range_lats']) if t_data['range_lats'] else 0.0
    r_tput = (t_data['range_ops'] / t_data['duration'] / 1000.0) if t_data['duration'] > 0 else 0.0
    
    y_range_lat.append(avg_range_lat)
    y_range_tput.append(r_tput)
    
    # 2. Worker Metrics (Clients 2 to N)
    worker_put_lats = []
    total_worker_put_ops = 0
    worker_durations = []
    
    for c in range(2, thread_count + 1):
        worker_path = os.path.join(LOG_BASE_DIR, folder, f"client{c}.txt")
        if not os.path.exists(worker_path):
            worker_path = os.path.join(LOG_BASE_DIR, folder, f"client{c}.log")
            
        w_data = parse_ml_performance(worker_path)
        if w_data['put_lats']:
            worker_put_lats.extend(w_data['put_lats'])
        total_worker_put_ops += w_data['put_ops']
        if w_data['duration'] > 0:
            worker_durations.append(w_data['duration'])
            
    # Calculate Aggregate Worker PUT Throughput (Sum of ops / average duration)
    avg_worker_dur = np.mean(worker_durations) if worker_durations else 0.0
    w_tput_agg = (total_worker_put_ops / avg_worker_dur / 1000.0) if avg_worker_dur > 0 else 0.0
    avg_put_lat = np.mean(worker_put_lats) if worker_put_lats else 0.0
    
    y_put_lat.append(avg_put_lat)
    y_put_tput_agg.append(w_tput_agg)
    
    # 3. Overall Consolidated Calculations
    # Combined Latency weighted by total workload volume balance
    total_ops = t_data['range_ops'] + total_worker_put_ops
    if total_ops > 0:
        combined_lat = ((avg_range_lat * t_data['range_ops']) + (avg_put_lat * total_worker_put_ops)) / total_ops
    else:
        combined_lat = 0.0
    
    y_overall_lat.append(combined_lat)
    y_overall_tput.append(r_tput + w_tput_agg)

# -------------------------------------------------------------------------
# --- RENDERING VISUAL SUBPLOTS ---
# -------------------------------------------------------------------------

# Top Left: Overall Latency
ax_lat_overall.plot(X_THREADS, y_overall_lat, color=COLOR_PRIMARY, marker='D', markersize=4.5, linewidth=1.8)

# Top Right: Individual Latencies
ax_lat_internal.plot(X_THREADS, y_range_lat, color=COLOR_RANGE, marker='s', markersize=4.5, linewidth=1.8, label='Range (Tracker)')
ax_lat_internal.plot(X_THREADS, y_put_lat, color=COLOR_PUT, marker='o', markersize=4.5, linewidth=1.8, label='Put (Workers Avg)')
ax_lat_internal.legend(fontsize=7.5, frameon=False, loc='best')

# Bottom Left: Overall Throughput
ax_tput_overall.plot(X_THREADS, y_overall_tput, color=COLOR_PRIMARY, marker='D', markersize=4.5, linewidth=1.8)

# Bottom Right: Individual Throughputs
ax_tput_internal.plot(X_THREADS, y_range_tput, color=COLOR_RANGE, marker='s', markersize=4.5, linewidth=1.8, label='Range Tput')
ax_tput_internal.plot(X_THREADS, y_put_tput_agg, color=COLOR_PUT, marker='o', markersize=4.5, linewidth=1.8, label='Put Tput (Agg)')
ax_tput_internal.legend(fontsize=7.5, frameon=False, loc='best')

# --- Formatting Subplot Structure & Aesthetics ---
for r_idx, row in enumerate(axes):
    for c_idx, ax in enumerate(row):
        # Configure matching x-scale properties
        ax.set_xscale('log', base=2)
        ax.set_xticks(X_THREADS)
        ax.set_xticklabels([str(x) for x in X_THREADS], fontsize=8.0)
        ax.set_xlim(min(X_THREADS) * 0.8, max(X_THREADS) * 1.25)
        
        # Grid line alignments
        ax.grid(True, axis='both', linestyle='--', linewidth=0.4, alpha=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis='both', labelsize=8.0, pad=2)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Strip X-axis text markers on upper tier plots
        if r_idx == 0:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel('Clients', fontsize=9.0, labelpad=3)
            
        # Left side column gets Y labels
        if c_idx == 0:
            if r_idx == 0:
                ax.set_ylabel('Latency (μs)', fontsize=9.5, labelpad=4)
            else:
                ax.set_ylabel('Throughput (Kops)', fontsize=9.5, labelpad=4)

# --- Save Plot ---
os.makedirs("output-plots", exist_ok=True)
output_path = "output-plots/ml_workload_performance.pdf"
fig.savefig(output_path, format='pdf', bbox_inches='tight', pad_inches=0.02)

print(f"2x2 Grid Performance Matrix successfully exported to: {output_path}")