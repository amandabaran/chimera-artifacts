#!/usr/bin/env python3

import re

batch_measurements = {
    '######## batch mid-points:': 'b-midpoints',
    '######## batch intervals:': 'b-interval',
    '######## batch latencies:': 'b-avg',
    '######## batch get latencies:': 'b-GET',
    '######## batch update latencies:' :'b-UPDATE',
}

measurements = {
    '######## update stats:': 'UPDATE',
    '######## get stats:': 'GET',
    '######## search stats:': 'GET', # Fallback for search-heavy logs
}

tiles = ['0.1', '25', '50', '75', '90', '95', '99', '99.9']

def parse(path):
    out = {}
    with open(path) as f:
        measurement = ""
        for line in f:
            l = line.lower().strip() # CRITICAL: .strip() handles \r\n and tail spaces
            if l == '################ batch stats:':
                break
            elif l == '################ main stats:':
                break
        if l == '################ batch stats:':
            for line in f:
                l = line.lower().strip()
                if l == '################ main stats:':
                    break
                elif l in batch_measurements:
                    measurement = batch_measurements[l]
                    assert(measurement not in out)
                    if(measurement == "b-midpoints"):
                        out[measurement] = []
                    else:
                        out[measurement + '-sums'] = []
                        out[measurement + '-counts'] = []

                elif 'ns' in l:
                    if 'ops' in l:
                        data = re.findall(r"^(\d+)ns / (\d+)ops$", l)
                        for x in data:
                            out[measurement + "-sums"].append(float(x[0]))
                            out[measurement + "-counts"].append(int(x[1]))
                    else:
                        data = re.findall(r"^(\d+)ns$", l)
                        for x in data:
                            value = float(x)
                            out[measurement].append(value)
        measurement = ""        
        for line in f:
            l = line.lower().strip()
            
            # Match headers allowing for trailing characters or colons
            if any(l.startswith(k) for k in measurements):
                matched_key = next(k for k in measurements if l.startswith(k))
                measurement = measurements[matched_key]
                
                # FIX: Always wipe/reset the sub-dictionary for this section!
                # This ensures 'GET stats' completely overwrites 'SEARCH stats' 
                # instead of accumulating or corrupting the 'psum' and 'pcount' metrics.
                out[measurement] = {}
                out[measurement]['pcount'] = 0
                out[measurement]['psum'] = 0
            elif "local tput" in l:
                measurement = ""
                assert("local tput" not in out)
                data = re.findall(r"local tput:\s*(\d+)\s*(?:kops|kpos)", l)
                assert len(data) == 1, l
                out["local tput"] = int(data[0])
            elif "aggregated tput" in l:
                measurement = ""
                assert("aggregated tput" not in out)
                data = re.findall(r"aggregated tput:\s*(\d+)kops", l)
                assert(len(data) == 1)
                out["aggregated tput"] = int(data[0])
            elif measurement != "":
                if l.startswith("average"):
                    data = re.findall(r"average latency:\s*(\d+)ns", l)
                    assert(len(data) == 1)
                    out[measurement]["avg"] = int(data[0]) / 1000
                elif "%:" in l:
                    data = re.findall(r"([0-9\.]+)\%:\s*(\d+)ns", l)
                    for x in data:
                        perc_float = float(x[0])
                        key = int(perc_float) if perc_float.is_integer() else perc_float
                        
                        # Overwrites the search values with final operation metrics smoothly
                        out[measurement][key] = int(x[1]) / 1000
                        if(perc_float > 0.5):
                            out[measurement]['pcount'] += 1
                            out[measurement]['psum'] += int(x[1]) / 1000
    return out