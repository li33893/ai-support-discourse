# 1. 导入 + 路径/常量
# pandas；若手写 κ 则 numpy（见 §4 决策）。
# script_dir、DATA_DIR、两个文件名常量。
# KAPPA_THRESHOLD = 0.70。

# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix
import os
import sys
# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files
HUMAN_INPUT_FILE = "spot_check_blind.csv"
LLM_INPUT_FILE   = "spot_check_llm_codes.csv"

# Rickwood coding dimensions: display name, human column, LLM column, label order.
DIMENSIONS = [
    {
        "name":      "Timeframe",
        "human_col": "human_timeframe",
        "llm_col"  : "llm_timeframe",
        "labels":    ["Habitual", "Episodic", "NM"]
    },
    {
        "name":      "Source",
        "human_col": "human_source",
        "llm_col":    "llm_source",
        "labels":    ["Primary", "Parallel", "Supplement", "Solo", "Exploration", "NM"]
    },
    {
        "name":      "Type",
        "human_col": "human_usage_intent",
        "llm_col":   "llm_usage_intent",
        "labels":    ["ES", "VE", "CO", "RE", "CR", "PE", "SA", "SE", "FS", "RS", "TA", "SR", "N", "OT"]
    }   
]

# ________________________________________________________________________________

# FUNCTION AREA

# ________________________________________________________________________________

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():

    # 01_DIR PREPARATION
    # directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir    = os.path.join(current_dir, "..", "data")

    # input file paths
    human_input_file = os.path.join(data_dir, HUMAN_INPUT_FILE)
    llm_input_file   = os.path.join(data_dir, LLM_INPUT_FILE)

    # 02_READ FILES AND CLEAN THE DATA
    human_df = pd.read_csv(human_input_file, encoding="utf-8-sig")
    llm_df   = pd.read_csv(llm_input_file, encoding="utf-8-sig")
  
    # merge two dfs into one
    llm_df    = llm_df[["post_id", "llm_timeframe", "llm_source", "llm_usage_intent"]]
    merged_df = human_df.merge(llm_df, on="post_id", how="inner")

    # 03_DROP HUMAN-EXCLUDED POSTS
    print("-"*25)
    print("Exclusion check:")
    print("-"*25)
    excluded_mask = merged_df["excluded"].astype(str).str.strip().str.upper().str.startswith("EX")
    n_excluded    = excluded_mask.sum()
    merged_df     = merged_df[~excluded_mask]
    print(f"human-excluded dropped: {n_excluded} | remaining: {len(merged_df)}")   

    # recognize typos
    print("-"*25)
    print("Check spellings of the human columns")
    print("-"*25)
    has_typo = False
    for d in DIMENSIONS:
        not_in_mask = ~(merged_df[d["human_col"]].astype(str).isin(d["labels"]))
        bad         = merged_df.loc[not_in_mask, d["human_col"]].tolist()
        print(f"{d['name']}:")
        if bad:
            has_typo = True
            print(f"{len(bad)} typos, see: {bad}\n")
        else:
            print("No typos.\n")
    if has_typo:
        print("\nIllegal values found. Fix the source file and re-run.")
        sys.exit(1)

        



if __name__ == "__main__":
    main()


