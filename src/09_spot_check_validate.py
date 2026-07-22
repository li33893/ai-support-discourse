
# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix
import os
import sys
import numpy as np
# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files
HUMAN_INPUT_FILE = "spot_check_blind.csv"
LLM_INPUT_FILE   = "spot_check_llm_codes.csv"

# decide kappa threshold for passing
KAPPA_THRESHOLD = 0.61

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

def gwet_ac1(human: list, llm:list):

    human_arr = np.array(human, dtype=int)
    llm_arr   = np.array(llm, dtype=int)
    n         = len(human)

    p_o  = sum(human_arr == llm_arr)/len(llm_arr)
    pi_t = (sum(human_arr) + sum(llm_arr))/(2 * n)
    pi_f = 1 - pi_t
    p_e  = 2 * pi_t * pi_f
    ac_1 = (p_o - p_e) / (1 - p_e)

    return ac_1


def kappa_score(human: list, llm:list):
    kappa = cohen_kappa_score(human, llm)
    return kappa

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

    # 03_DROP HUMAN-EXCLUDED POSTS AND CLEAN THE TYPOS
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
    
    # 04_PRINT FIVE TOP DISAGREEMENT CASES
    # agreement calculation
    
    human_type = merged_df["human_usage_intent"]
    llm_type   = merged_df["llm_usage_intent"]

    # timeframe
    human_tf = merged_df["human_timeframe"]
    llm_tf   = merged_df["llm_timeframe"]

    pct_agree_tf = (human_tf == llm_tf).mean()
    ac1_tf       = gwet_ac1(human_tf.tolist(), llm_tf.tolist())
    cohen_k   = kappa_score(human_tf.tolist(), llm_tf.tolist())

    # source
    human_src = merged_df["human_source"]
    llm_src   = merged_df["llm_source"]

    pct_agree_src = (human_src == llm_src).mean()
    ac1_src       = gwet_ac1(human_src.tolist(), llm_src.tolist())
    cohen_k   = kappa_score(human_src.tolist(), llm_src.tolist())  

    # type

    human_type = merged_df["human_usage_intent"]
    llm_type   = merged_df["llm_usage_intent"]

    pct_agree_type = (human_type == llm_type).mean()
    ac1_type       = gwet_ac1(human_type.tolist(), llm_type.tolist())
    cohen_k   = kappa_score(human_type.tolist(), llm_type.tolist()) 

    # 05_COLLECT FIVE TOP DISAGREEMENT PAIRS AND THE NUMBER OF THEM IN EACH DIMENSIONS
    




if __name__ == "__main__":
    main()


