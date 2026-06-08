#!/usr/bin/env python3

import os
import re
import numpy as np
import matplotlib.pyplot as plt

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
THINK_TIMES = [1, 5, 10, 50, 100, 500, 1000]
LOG_BASE_DIR = "logs/think-times/CHIMERA"
TOTAL_CLIENTS = 8

COLOR_RANGE = '#d11414'   # Crimson Red (RANGE / Tracker)
COLOR_PUT   = '#1f77b4'   # Deep Blue   (PUT / Workers)

plt.close('all')

# --- Layout Setup ---
# FIXED: Increased figsize slightly to give text elements breathing room
fig, ax1 = plt.subplots(1, 1, figsize=(2.5, 1.75))
fig.subplots_adjust(top=0.72, bottom=0.24, left=0.10, right=0.96)
ax1.set_box_aspect(0.75)

range_y_data = []
put_y_data = []

# --- Data Extraction Loop ---
for t_time in THINK_TIMES:
    dir_path = os.path.join(LOG_BASE_DIR, f"think{t_time}", "3servers", "8client")
    
    tracker_path = os.path.join(dir_path, "client1.txt")
    if not os.path.exists(tracker_path):
        tracker_path = os.path.join(dir_path, "client1.log")
        
    t_data = parse_ml_performance(tracker_path)
    avg_range = np.mean(t_data['range_lats']) if t_data['range_lats'] else 0.0
    range_y_data.append(avg_range)
    
    all_worker_put_lats = []
    for c in range(2, TOTAL_CLIENTS + 1):
        worker_path = os.path.join(dir_path, f"client{c}.txt")
        if not os.path.exists(worker_path):
            worker_path = os.path.join(dir_path, f"client{c}.log")
            
        w_data = parse_ml_performance(worker_path)
        if w_data['put_lats']:
            all_worker_put_lats.extend(w_data['put_lats'])
            
    avg_put = np.mean(all_worker_put_lats) if all_worker_put_lats else 0.0
    put_y_data.append(avg_put)

print("Parsed RANGE Latencies:", range_y_data)
print("Parsed PUT Latencies:", put_y_data)

# -------------------------------------------------------------------------
# --- STRUCTURAL FINISHING PASS (Fixed Equal X-Spacing) ---
# -------------------------------------------------------------------------
ax1.set_xscale('linear')
x_positions = list(range(len(THINK_TIMES)))

line_put, = ax1.plot(x_positions, put_y_data, color=COLOR_PUT, marker='o',
                    markersize=2.5, linewidth=1.8, label='PUT')
line_rng, = ax1.plot(x_positions, range_y_data, color=COLOR_RANGE, marker='s',
                    markersize=2.5, linewidth=1.8, label='RANGE')

# FIXED: Shrunk title size and fine-tuned axes font properties
ax1.set_title('Latency vs Think Time', pad=12, fontsize=7.0)
ax1.set_xlabel('Think Time (ms)', fontsize=6.5, labelpad=1)
ax1.set_ylabel('Latency ($\mu$s)', fontsize=6.5, labelpad=1)

# FIXED: Reduced xtick label sizes to 6.5 and added a slight 15-degree angle 
# to ensure '50', '100', '500', and '1000' never crash into each other.
ax1.set_xticks(x_positions)
ax1.set_xticklabels([str(x) for x in THINK_TIMES], fontsize=5.0, rotation=15)
ax1.tick_params(axis='y', labelsize=5.0, pad=2)


max_lat = max(max(put_y_data), max(range_y_data)) if (put_y_data or range_y_data) else 4.0
ax1.set_ylim(2, max_lat * 1.15 if max_lat > 2 else 5.0)
ax1.set_xlim(-0.4, len(THINK_TIMES) - 0.6)

ax1.grid(True, axis='both', linestyle='--', linewidth=0.5, alpha=0.6)
ax1.set_axisbelow(True)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# -------------------------------------------------------------------------
# --- TOP-LEVEL UNIFIED LEGEND ---
# -------------------------------------------------------------------------
fig.legend(handles=[line_put, line_rng],
           labels=['PUT (Workers 2-8)', 'RANGE (Tracker 1)'],
           loc='upper center',
           bbox_to_anchor=(0.5, 0.98),
           ncol=2,
           fontsize=6.5,
           frameon=True,
           facecolor='white',
           edgecolor='black',
           borderpad=0.2,
           handletextpad=0.3,
           columnspacing=1.0)

# --- Save Pass ---
os.makedirs("output-plots", exist_ok=True)
output_path = "output-plots/latency_vs_think_time.pdf"
fig.savefig(output_path, format='pdf', bbox_inches='tight', pad_inches=0.02)

print(f"Updated plot generated successfully -> {output_path}")