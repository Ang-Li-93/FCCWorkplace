#!/usr/bin/env python3
import re
from collections import defaultdict

################################################
#  1. We'll store final counts in a 4x4 table:
#   W+ can be e, mu, tau, had
#   W- can be e, mu, tau, had
categories = ["e", "mu", "tau", "had"]
count_table = { (wp, wm): 0 for wp in categories for wm in categories }

################################################
#  2. We'll define a function that classifies 
#     a W's daughters as e/μ/τ/had
def classify_decay(daughters, lines_dict):
    """
    daughters: list of line numbers that the W decays into
    lines_dict: { line_num: {'name': 'E+', 'daughters': [...]}, ... }
    returns 'e', 'mu', 'tau', or 'had'
    """
    # gather the names
    names = [ lines_dict[d]['name'] for d in daughters if d in lines_dict ]
    # The presence of e± plus neutrino => 'e'
    if ({"E+", "E-"} & set(names)) and ({"NUE", "ANUE"} & set(names)):
        return "e"
    # mu± plus neutrino => 'mu'
    if ({"MU+", "MU-"} & set(names)) and ({"NUM", "ANUM"} & set(names)):
        return "mu"
    # tau± plus neutrino => 'tau'
    if ({"TAU+", "TAU-"} & set(names)) and ({"NUT", "ANUT"} & set(names)):
        return "tau"
    
    # else => 'had'
    return "had"

################################################
#  3. We'll parse the entire listing
lines_dict = {}
event_index = None

def parse_event_and_update_counts():
    # we parse the W decays in lines_dict
    # find W+ line, W- line
    wplus = [ k for k,v in lines_dict.items() if v["name"] == "W+" ]
    wminus= [ k for k,v in lines_dict.items() if v["name"] == "W-" ]
    if len(wplus)==1 and len(wminus)==1:
        wp_line = wplus[0]
        wm_line = wminus[0]
        wp_cat = classify_decay(lines_dict[wp_line]["daughters"], lines_dict)
        wm_cat = classify_decay(lines_dict[wm_line]["daughters"], lines_dict)
        count_table[(wp_cat, wm_cat)] += 1

filename = "/afs/cern.ch/work/l/lia/private/FCC/FCCWorkplace/decayttbar.out"
with open(filename, "r") as f:
    for rawline in f:
        line = rawline.strip()
        # detect new event
        if line.startswith("---"):
            # first, if we had an old event, parse it
            if event_index is not None:
                parse_event_and_update_counts()
            
            # then read new event index
            match = re.match(r"---\s+(\d+)\s+(\d+)", line)
            if match:
                event_index = int(match.group(1)) # or group(2)
                lines_dict = {}
            else:
                event_index = None
        else:
            # parse typical line: e.g. "  9 W+  11 12  0  ..."
            splitted = line.split()
            if len(splitted)<2:
                continue
            try:
                line_num = int(splitted[0])
                part_name= splitted[1]
                # next columns might be mother/daughter lines 
                # but in your listing, we see " 9 W+  11 12  0 ..."
                # splitted[2] splitted[3] splitted[4] might be daughters
                d1 = int(splitted[2])
                d2 = int(splitted[3])
                # ignoring splitted[4], splitted[5] if any
                lines_dict[line_num] = {
                    'name': part_name,
                    'daughters': [d for d in (d1,d2) if d>0]
                }
            except:
                pass

# parse last event
if event_index is not None:
    parse_event_and_update_counts()

################################################
# 4. Print the final table
print("W+ \\ W-   |   e     mu    tau   had   ")
print("---------------------------------------")
for wp in categories:
    row_counts = []
    for wm in categories:
        row_counts.append( count_table[(wp, wm)] )
    # format the row
    print(f"W+ {wp:3s}  |", " ".join(f"{x:5d}" for x in row_counts))

print("\nTotal events counted =", sum(count_table.values()))