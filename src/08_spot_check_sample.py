"""
================================================================================
SCRIPT: 08_spot_check_sample.py
PURPOSE: Draw the held-out spot-check sample for human-LLM agreement validation
         (pipeline stage 8)
================================================================================

WHAT THIS SCRIPT DOES:
    1. Filters the coded corpus down to an eligible pool
       (drops pilot posts and LLM-excluded posts)
    2. Draws a fixed 50-post random sample (seed=42) for validation
    3. Writes a blind file for independent human coding, plus the matching
       LLM codes for later comparison

FLOW:
    1. Read inputs
       - posts_list_cleaned_llm_coded.csv   (2,127 coded posts)
       - pilot_sample.csv                   (80 pilot-coded posts)

    2. Filter to eligible pool  [03_FILTERING]
       - Exclude posts already used in pilot coding
       - Exclude posts the LLM marked as excluded (llm_excluded == True)
       -> 2,127 -> 2,047 (after pilot) -> 1,923 (after llm_excluded)

    3. Sample  [04_SAMPLING]
       - Draw 50 posts with a fixed seed for a reproducible draw
       - Build two column views of the same 50 posts:
           a. blind : post_id, subreddit, title, body, word_count
                      + empty human_timeframe / human_source /
                        human_usage_intent / notes
           b. llm   : the 5 base columns
                      + llm_timeframe / llm_source / llm_usage_intent

    4. Save  [05_SAVE TO FILES]
       - Refuse to write if either output already exists (protects the
         frozen, human-coded blind file from being overwritten)
       -> writes spot_check_blind.csv and spot_check_llm_codes.csv

OUTPUT FILES:
    spot_check_blind.csv       50 posts, no codes, for independent human coding
    spot_check_llm_codes.csv   Same 50 posts with the LLM's Rickwood codes,
                               for comparison after human coding is done

NEXT STEP: 09_spot_check_validate.py (compare human vs LLM codes, compute kappa)

================================================================================
"""

# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import pandas as pd
import os
import sys

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files
INPUT_FILE = "posts_list_cleaned_llm_coded.csv"
PILOT_FILE = "pilot_sample.csv"

# output files
HUMAN_OUTPUT_FILE = "spot_check_blind.csv"
LLM_OUTPUT_FILE   = "spot_check_llm_codes.csv"

# sampling constants
N_SAMPLE = 50
SEED     = 42

# coding items
HUMAN = ["human_timeframe", "human_source", "human_usage_intent", "notes"]

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():
    # 01_DIR PREPARATION
    # directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir    = os.path.join(current_dir, "..", "data")

    # input file paths
    input_file = os.path.join(data_dir, INPUT_FILE)
    pilot_file = os.path.join(data_dir, PILOT_FILE)

    # output file paths
    human_output_file = os.path.join(data_dir, HUMAN_OUTPUT_FILE)
    llm_output_file   = os.path.join(data_dir, LLM_OUTPUT_FILE)

    # 02_READ FILES
    input_df = pd.read_csv(input_file, encoding="utf-8-sig")
    pilot_df = pd.read_csv(pilot_file, encoding="utf-8-sig")

    # 03_FILTERING
    # exclude the posts invloved in pilot coding
    pilot_ids     = pilot_df["post_id"]
    no_pilot_mask = ~input_df["post_id"].astype(str).isin(pilot_ids)
    e_pilot_df    = input_df[no_pilot_mask]

    # exclude the posts are coded as "excluded"
    no_excluded_mask = ~e_pilot_df["llm_excluded"] 
    full_df          = e_pilot_df[no_excluded_mask]

    # print the statistical result of filtering for scrutiny
    print("-"*25)
    print("Statistical result of filtering process:\n")
    print("-"*25)
    print(f"inputted corpus in total:           {len(input_df)} posts\n")
    print(f"after excluding pilot coded posts:  {len(e_pilot_df)} posts\n")
    print(f"after excluding llm-excluded posts: {len(full_df)} posts.\n")
    print("-"*25)

    # 04_SAMPLING
    sample_df = full_df.sample(n=N_SAMPLE, random_state=SEED)

    # human
    human_df  = sample_df[["post_id", "subreddit", "title", "body", "word_count"]].copy()
    for col in HUMAN:
        human_df[col] = ""

    # llm
    llm_df = sample_df[["post_id", "subreddit", "title", "body", "word_count", "llm_timeframe", "llm_source", "llm_usage_intent"]].copy()

    # in case the files are mistakenly covered
    if os.path.exists(human_output_file) or os.path.exists(llm_output_file):
        print("At least one of the files already exist. Check: 'spot_check_blind.csv' or 'spot_check_llm_codes.csv'")
        sys.exit(1)

    # 05_SAVE TO FILES
    human_df.to_csv(human_output_file, index=False, encoding="utf-8-sig")
    llm_df.to_csv(llm_output_file, index=False, encoding="utf-8-sig")
    print("Files have been successfully saved.")

    
if __name__ == "__main__":
    main()

