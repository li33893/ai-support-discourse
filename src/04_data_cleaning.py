"""
================================================================================
SCRIPT: 04_data_cleaning.py
PURPOSE: Filter the screened corpus into the final usable set (pipeline stage 4)
================================================================================

WHAT THIS SCRIPT DOES:
    1. Keeps only the posts worth analysing (relevant, not high-risk)
    2. Removes duplicate posts
    3. Keeps all of them (no down-sampling) and saves the result

FLOW:
    1. Read the screened posts  [posts_list_screened.csv]
       - Output of the LLM screening step, one row per post, with llm_ columns

    2. Filter to usable posts
       - Keeps a post only if ALL of these are true:
           a. the LLM marked it relevant        (llm_relevant is True)
           b. it is NOT a Level 3 risk post      (llm_risk_level is not 3)
           c. it is NOT flagged as psychosis     (llm_psychosis is not True)
       - Note: ad / promo posts are already handled at the screening step, not here.

    3. Remove duplicates
       - Sorts by word_count (longest first), then drops posts with the same body
       - Keeping the longest version means the fullest post survives
       - Duplicates are usually the same post cross-posted to more than one subreddit

    4. Keep everything and save
       - No down-sampling: every usable post is kept
       - Sorts by subreddit then created_utc, resets the row index
       - Prints how many were read, how many are usable, how many remain
       - Prints the subreddit distribution (count and percent)
       -> writes posts_list_cleaned.csv

OUTPUT FILE:
    posts_list_cleaned.csv   

NEXT STEP: 05_rickwood_coding.py

"""

# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import pandas as pd
import os

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files naming constants
POSTS_LIST_SCREENED = "posts_list_screened.csv"

# output files naming constants
POSTS_LIST_CLEANED = "posts_list_cleaned.csv"

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():
    # prepare directories
    script_dir       = os.path.dirname(os.path.abspath(__file__))
    data_dir         = os.path.join(script_dir, "..", "data") 
    screened_csv_dir = os.path.join(data_dir, POSTS_LIST_SCREENED)
    cleaned_csv_dir  = os.path.join(data_dir, POSTS_LIST_CLEANED)

    # read csv from data directory
    screened_df = pd.read_csv(screened_csv_dir, encoding="utf-8-sig")

    # select usable posts from the input file
    is_relevant   = screened_df["llm_relevant"] == True
    not_flagged   = ~((screened_df["llm_risk_level"] == 3) | (screened_df["llm_psychosis"] == True))
    usable_df     = screened_df[is_relevant & not_flagged].copy()
    

    # deduplicate the posts, making sure that among those posts have duplicates, only the longest posts are saved
    desc_df        = usable_df.sort_values("word_count", ascending=False).copy()
    deduplicate_df = desc_df.drop_duplicates(subset="body", keep="first")

    # save to files
    final_df = deduplicate_df.sort_values(["subreddit", "created_utc"]).reset_index(drop=True)
    final_df.to_csv(cleaned_csv_dir, index=False, encoding="utf-8-sig")

    # proportion calculation:
    sum_final    = len(final_df)
    
    # quick look
    print("Quick Look:\n")
    print(f"{len(screened_df)} posts were read from {POSTS_LIST_SCREENED},\n")
    print(f"among which {len(usable_df)} posts are usable.\n")
    print(f"After deduplication, {len(final_df)} posts remain.\n")
    print("=" * 50 + "\n")
    print("Subreddit distribution:\n")

    counts = final_df["subreddit"].value_counts()
    props  = final_df["subreddit"].value_counts(normalize=True) * 100

    for sub in counts.index:
        print(f"{sub:14s} total: {counts[sub]:5d}   proportion: {props[sub]:.1f}%")
    

if __name__ == "__main__":
    main()