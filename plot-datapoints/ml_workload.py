#!/usr/bin/env python3

import os
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# --- Comprehensive Log Parser ---
def parse_ml_performance(path):
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
            
            if "######## range stats:" in clean:
                inside_block = "range"
                continue
            elif "######## put stats:" in clean:
                inside_block = "put"
                continue
            elif "########" in clean and "stats:" in clean:
                inside_block = None
                continue
                
            if inside_block and "number of measurements:" in clean:
                match = re.search(r"measurements:\s*([0-9.]+)", clean)
                if match:
                    metrics[f"{inside_block}_ops"] = int(float(match.group(1)))
                    
            if inside_block and "%:" in clean:
                match = re.search(r"([0-9.]+)\s*%:\s*([0-9.]+)\s*(us|ns)", clean)
                if match:
                    val = float(match.group(2))
                    unit = match.group(3)
                    metrics[f"{inside_block}_lats"].append(val if unit == "us" else val / 1000.0)
            
            if "ml-tracker-results:" in clean or "ml-worker-results:" in clean:
                match = re.search(r"duration_sec=([0-9.]+)", clean)
                if match:
                    metrics['duration'] = float(match.group(1))
                    
    return metrics

# =========================================================================
# --- CONFIGURATION MATRIX ---
# =========================================================================
X_THREADS = [2, 4, 8, 16]
LOG_BASE_DIR = "logs/ML/CHIMERA/3servers"

# REVERSED: RANGE -> red, PUT -> blue
COLOR_RANGE = '#d11414'   # Crimson Red (RANGE / Tracker)
COLOR_PUT   = '#1f77b4'   # Deep Blue   (PUT  / Worker)

plt.close('all')

# --- Wider figure, tight margins ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(4, 1.75))
fig.subplots_adjust(top=0.72, bottom=0.24, left=0.10, right=0.96, wspace=0.35)

# --- Wider, less-tall aspect ratio (no longer forced square) ---
ax1.set_box_aspect(0.8)
ax2.set_box_aspect(0.8)

# --- Data Arrays ---
worker_y_data = []
tracker_y_data = []
y_range_tput = []
y_put_tput_agg = []

# --- Data Extraction Loop ---
for thread_count in X_THREADS:
    folder = f"{thread_count}client"
    
    # 1. Tracker Metrics (Client 1)
    tracker_path = os.path.join(LOG_BASE_DIR, folder, "client1.txt")
    if not os.path.exists(tracker_path):
        tracker_path = os.path.join(LOG_BASE_DIR, folder, "client1.log")
        
    t_data = parse_ml_performance(tracker_path)
    avg_tracker = np.mean(t_data['range_lats']) if t_data['range_lats'] else 0.0
    tracker_y_data.append(avg_tracker)
    
    r_tput = (t_data['range_ops'] / t_data['duration'] / 1000.0) if t_data['duration'] > 0 else 0.0
    y_range_tput.append(r_tput)
    
    # 2. Worker Metrics (Clients 2 to N)
    all_worker_lats = []
    total_worker_put_ops = 0
    worker_durations = []
    
    for c in range(2, thread_count + 1):
        worker_path = os.path.join(LOG_BASE_DIR, folder, f"client{c}.txt")
        if not os.path.exists(worker_path):
            worker_path = os.path.join(LOG_BASE_DIR, folder, f"client{c}.log")
            
        w_data = parse_ml_performance(worker_path)
        if w_data['put_lats']:
            all_worker_lats.extend(w_data['put_lats'])
        total_worker_put_ops += w_data['put_ops']
        if w_data['duration'] > 0:
            worker_durations.append(w_data['duration'])
            
    avg_worker = np.mean(all_worker_lats) if all_worker_lats else 0.0
    worker_y_data.append(avg_worker)
    
    avg_worker_dur = np.mean(worker_durations) if worker_durations else 0.0
    w_tput_agg = (total_worker_put_ops / avg_worker_dur / 1000.0) if avg_worker_dur > 0 else 0.0
    y_put_tput_agg.append(w_tput_agg)

# -------------------------------------------------------------------------
# --- LEFT PLOT (Latency, single y-axis) ---
# -------------------------------------------------------------------------
line_put, = ax1.plot(X_THREADS, worker_y_data, color=COLOR_PUT, marker='o',
                    markersize=4.5, linewidth=1.8, label='PUT (Worker)')
line_rng, = ax1.plot(X_THREADS, tracker_y_data, color=COLOR_RANGE, marker='s',
                    markersize=4.5, linewidth=1.8, label='RANGE (Tracker)')

ax1.set_title('Operation Latency', pad=6, fontsize=7.5)
ax1.set_xlabel('Threads (1 Tracker + N-1 Workers)', fontsize=7.0, labelpad=3)
ax1.set_ylabel('Latency (μs)', fontsize=7.0, labelpad=2)
ax1.tick_params(axis='y', labelsize=6.5, pad=2)

max_lat = max(max(worker_y_data), max(tracker_y_data)) if (worker_y_data or tracker_y_data) else 1.0
ax1.set_ylim(0, max_lat * 1.15 if max_lat > 0 else 4.0)
ax1.yaxis.set_major_locator(MultipleLocator(0.5))

# -------------------------------------------------------------------------
# --- RIGHT PLOT (Throughput) ---
# -------------------------------------------------------------------------
ax2.plot(X_THREADS, y_put_tput_agg, color=COLOR_PUT, marker='o',
         markersize=4.5, linewidth=1.8)
ax2.plot(X_THREADS, y_range_tput, color=COLOR_RANGE, marker='s',
         markersize=4.5, linewidth=1.8)

ax2.set_title("Operation Throughput", fontsize=7.5, pad=6)
ax2.set_xlabel('Clients', fontsize=7.0, labelpad=3)
ax2.set_ylabel('Throughput (Mops)', fontsize=7.0, labelpad=2)
ax2.tick_params(axis='y', labelsize=6.5, pad=2)

max_tput = max(max(y_range_tput), max(y_put_tput_agg)) if (y_range_tput or y_put_tput_agg) else 1.0
ax2.set_ylim(0, max_tput * 1.15 if max_tput > 0 else 4.0)
ax2.yaxis.set_major_locator(MultipleLocator(1.0))

# -------------------------------------------------------------------------
# --- STRUCTURAL FINISHING PASS ---
# -------------------------------------------------------------------------
for ax in [ax1, ax2]:
    ax.set_xscale('log', base=2)
    ax.set_xticks(X_THREADS)
    ax.set_xticklabels([str(x) for x in X_THREADS], fontsize=7.5)
    ax.set_xlim(min(X_THREADS) * 0.9, max(X_THREADS) * 1.15)
    
    ax.grid(True, axis='both', linestyle='--', linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', pad=2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# -------------------------------------------------------------------------
# --- TOP-LEVEL UNIFIED LEGEND ---
# -------------------------------------------------------------------------
fig.legend(handles=[line_put, line_rng],
           labels=['PUT (Worker)', 'RANGE (Tracker)'],
           loc='upper center',
           bbox_to_anchor=(0.5, 1.00),
           ncol=2,
           fontsize=7.5,
           frameon=True,
           facecolor='white',
           edgecolor='black',
           borderpad=0.3,
           handletextpad=0.4,
           columnspacing=1.2)

# --- Save: trim all surrounding whitespace ---
os.makedirs("output-plots", exist_ok=True)
output_path = "output-plots/ml_interference_and_throughput.pdf"
fig.savefig(output_path, format='pdf', bbox_inches='tight', pad_inches=0.0)

print(f"Wider, color-swapped, whitespace-trimmed plot saved -> {output_path}")