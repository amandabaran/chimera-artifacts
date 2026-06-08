#!/usr/bin/env python3

import os
import re
import numpy as np
import matplotlib.pyplot as plt

# --- Corrected Log Parser for your ML Format ---
def parse_ml_latencies(path, target_block):
    """
    Parses your file by identifying the correct stats block 
    ('range' for tracker, 'put' for workers) and averaging all percentiles.
    """
    latencies = []
    if not os.path.exists(path):
        return latencies
        
    inside_target_block = False
    
    with open(path, 'r') as f:
        for line in f:
            clean = line.strip().lower()
            
            # Detect which block header we are crossing
            if "######## range stats:" in clean:
                inside_target_block = (target_block == "range")
                continue
            elif "######## put stats:" in clean:
                inside_target_block = (target_block == "put")
                continue
            elif "########" in clean and "stats:" in clean:
                # Entered some other stats block, turn off matching
                inside_target_block = False
                continue
            
            # Extract latency values if we are inside the active block
            if inside_target_block and "%:" in clean:
                match = re.search(r"([0-9.]+)\s*%:\s*([0-9.]+)\s*(us|ns)", clean)
                if match:
                    val = float(match.group(2))
                    unit = match.group(3)
                    latency_us = val if unit == "us" else val / 1000.0
                    latencies.append(latency_us)
                        
    return latencies

# =========================================================================
# --- FLEXIBLE CONFIGURATION MATRIX ---
# =========================================================================
X_THREADS = [2, 4, 8, 16]

LOG_BASE_DIR = "logs/ML/CHIMERA/3servers"
COLOR_WORKER = '#d11414'   # Crimson Red
COLOR_TRACKER = '#1f77b4'  # Deep Blue

# --- Build Layout ---
fig, ax1 = plt.subplots(figsize=(5.0, 3.40))
fig.subplots_adjust(top=0.88, bottom=0.15, left=0.13, right=0.87)

# Instantiate dual y-axis
ax2 = ax1.twinx()

# --- Processing Data Loop ---
worker_y_data = []
tracker_y_data = []

for thread_count in X_THREADS:
    folder = f"{thread_count}client"
    
    # 1. Tracker Latency: Isolated strictly to client1.txt (RANGE stats)
    tracker_path = os.path.join(LOG_BASE_DIR, folder, "client1.txt")
    if not os.path.exists(tracker_path):
        tracker_path = os.path.join(LOG_BASE_DIR, folder, "client1.log")
    
    tracker_lats = parse_ml_latencies(tracker_path, target_block="range")
    avg_tracker = np.mean(tracker_lats) if tracker_lats else 0.0
    tracker_y_data.append(avg_tracker)
    
    # 2. Worker Latency: Averaged across all OTHER clients 2 to N (PUT stats)
    all_worker_lats = []
    for c in range(2, thread_count + 1):
        worker_path = os.path.join(LOG_BASE_DIR, folder, f"client{c}.txt")
        if not os.path.exists(worker_path):
            worker_path = os.path.join(LOG_BASE_DIR, folder, f"client{c}.log")
            
        if os.path.exists(worker_path):
            worker_lats = parse_ml_latencies(worker_path, target_block="put")
            all_worker_lats.extend(worker_lats)

    avg_worker = np.mean(all_worker_lats) if all_worker_lats else 0.0
    worker_y_data.append(avg_worker)

    # Diagnostic warnings to trace unexpected empty values
    if avg_tracker == 0.0:
        print(f"Warning: No 'RANGE stats' parsed from client1 for {folder}/")
    if avg_worker == 0.0 and thread_count > 1:
        print(f"Warning: No 'PUT stats' parsed from clients 2-{thread_count} in {folder}/")

# --- Plotting Real Trends ---
ax1.plot(X_THREADS, worker_y_data, color=COLOR_WORKER, marker='o', markersize=5, 
         linewidth=2.0, label='Worker Put Latency')

ax2.plot(X_THREADS, tracker_y_data, color=COLOR_TRACKER, marker='s', markersize=5, 
         linewidth=2.0, label='Tracker RQ Latency')

# --- Structural Adjustments & Trimming ---
ax1.set_title('ML Tracker vs. Worker Interference (CN=1)', pad=12, fontsize=10, fontweight='bold')
ax1.set_xlabel('Threads (1 Tracker + N-1 Workers)', fontsize=8.5, labelpad=4)

# --- Log Scaling X Axis ---
ax1.set_xscale('log', base=2)
ax1.set_xticks(X_THREADS)
ax1.set_xticklabels([str(x) for x in X_THREADS], fontsize=8.0)
ax1.set_xlim(min(X_THREADS) * 0.8, max(X_THREADS) * 1.15)

# Left Y-Axis customization (Worker Put)
ax1.set_ylabel('Worker Put Latency (us)', color=COLOR_WORKER, fontsize=9.0, labelpad=4)
ax1.tick_params(axis='y', labelcolor=COLOR_WORKER, labelsize=8.0)
max_worker = max(worker_y_data) if worker_y_data else 1.0
ax1.set_ylim(0, max_worker * 1.15 if max_worker > 0 else 5.0) 

# Right Y-Axis customization (Tracker RQ)
ax2.set_ylabel('Tracker RQ Latency (us)', color=COLOR_TRACKER, fontsize=9.0, labelpad=4)
ax2.tick_params(axis='y', labelcolor=COLOR_TRACKER, labelsize=8.0)

min_tracker = 0.0
max_tracker = max(tracker_y_data) if tracker_y_data else 1.0
if max_tracker != min_tracker:
    ax2.set_ylim(min_tracker - 0.1 * (max_tracker - min_tracker), max_tracker + 0.1 * (max_tracker - min_tracker))
else:
    ax2.set_ylim(min_tracker * 0.9, max_tracker * 1.1 if max_tracker > 0 else 5.0)

# Clean style finishes
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax1.grid(True, axis='both', linestyle='--', linewidth=0.4, alpha=0.5)
ax1.set_axisbelow(True)

# --- Save Visual Output ---
os.makedirs("output-plots", exist_ok=True)
output_path = "output-plots/ml_interference_isolated.pdf"
fig.savefig(output_path, format='pdf', bbox_inches='tight', pad_inches=0.02)

print(f"Graph generated successfully -> saved to: {output_path}")