"""
convert sampling_first_round to json

"""
OUTPUT_FILE = "sampling_first_round.json"
INPUT_FILE  = "sampling_first_round.csv"

import pandas as pd
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir    = os.path.join(current_dir, "..", "data")
input_file  = os.path.join(data_dir, INPUT_FILE)
output_file = os.path.join(current_dir, OUTPUT_FILE)

df = pd.read_csv(input_file, encoding="utf-8-sig")

if os.path.exists(output_file):
    print("The file already exists. Check: 'sampling_first_round.json'")
    sys.exit(1)
    
df.to_json(output_file, orient="records", force_ascii=False, indent=2)
print(f"Wrote {len(df)} posts -> {output_file}")