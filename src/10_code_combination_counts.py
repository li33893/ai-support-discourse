"""
================================================================================
SCRIPT: 10_code_combination_counts.py
PURPOSE: Frequency table of the three-code × subreddit cells 
================================================================================

WHAT THIS SCRIPT DOES:
    1. Groups coded posts into subreddit × timeframe × intent × source cells
    2. Counts posts per cell, sorted by subreddit then descending count
    3. Adds each cell's share of the corpus and share within its subreddit

FLOW:
    1. create_code_combination_count()
       - groupby the four code columns, .size() -> count
       - proportion_in_total     = count / corpus total
       - proportion_in_community = count / that subreddit's total
       -> returns the frequency DataFrame

    2. main()
       - Reads the coded post list, writes the table as utf-8-sig CSV
       -> code_combination_counts.csv

OUTPUT FILES:
    code_combination_counts.csv  One row per code cell: count + two proportions

NEXT STEP: 11_descriptive_figures.py
================================================================================
"""

# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import pandas as pd
import os
# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files
INPUT_FILE  = "posts_list_cleaned_llm_coded.csv"
OUTPUT_FILE = "code_combination_counts.csv"

# ________________________________________________________________________________

# FUNCTION AREA

# ________________________________________________________________________________

def create_code_combination_count (input_df):
    # 
    frequency = (
        input_df
        .groupby([
            "subreddit",
            "llm_timeframe",
            "llm_usage_intent",
            "llm_source"
        ])
        .size()
        .reset_index(name="count")
        .sort_values(
            ["subreddit", "count"],
            ascending=[True, False]
       )
    )

    # each combination's proportion in total
    frequency["proportion_in_total"] = frequency["count"]/frequency["count"].sum()

    # each combination's proportion in community
    frequency["proportion_in_community"] = (
        frequency["count"]/frequency.groupby("subreddit")["count"].transform("sum")
    )

    return frequency

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():

    # 01_DIR PREPARATION
    # directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir    = os.path.join(current_dir, "..", "data")

    # input file paths
    input_file  = os.path.join(data_dir, INPUT_FILE)
    output_file = os.path.join(data_dir, OUTPUT_FILE)

    # 02_CREATE DICT OF FREQUENCY
    input_df   = pd.read_csv(input_file)
    output_df  = create_code_combination_count (input_df) 



    # 03_SAVE TO FILES
    output_df.to_csv(output_file, index=False, encoding="utf-8-sig")



if __name__ == "__main__":
    main()