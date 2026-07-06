"""
================================================================================
SCRIPT: 03_agreement.py
PURPOSE: Human-LLM agreement check on relevance screening (pipeline stage 3)
================================================================================

WHAT THIS SCRIPT DOES:
    1. Builds a blind sample for a human to judge relevance by hand
    2. Compares human judgments against LLM screening judgments
    3. Reports agreement via Cohen's Kappa + Gwet's AC1

FLOW:
    1. generate_sample()
       - Draws 100 from llm_relevant==True and 100 from ==False
       - Exports only human-visible columns (blind to LLM verdict)
       -> agreement_sample.csv, agreement_sample_llm_labels.csv

    2. calculate_agreement()
       - Merges human + LLM labels on post_id
       - Reports agreement %, Kappa, AC1, confusion matrix (TP/TN/FP/FN)
       -> agreement_disagreements.csv

OUTPUT FILES:
    agreement_sample.csv             Blind sample, human_relevant hand-typed
    agreement_sample_llm_labels.csv  Held-out LLM verdicts
    agreement_disagreements.csv      Human-LLM disagreement cases

NEXT STEP: 04_data_cleaning.py
================================================================================
"""

# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import os
import numpy as np
from sklearn.metrics import cohen_kappa_score
import pandas as pd

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________
# input files
POST_LIST_SCREENED = "posts_list_screened.csv"

# output files
AGREEMENT_SAMPLE             = "agreement_sample.csv"             
AGREEMENT_SAMPLE_LLM_LABELS  = "agreement_sample_llm_labels.csv"  
AGREEMENT_DISAGREEMENT       = "agreement_disagreements.csv" 

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


def generate_sample(screened_file, human_file, llm_file):
    screened_df = pd.read_csv(screened_file, encoding="utf-8-sig")
    # sample 100 rows labeled with True(relevant) and False(irrelevant) respectively
    relevant                   = screened_df[screened_df["llm_relevant"]].sample(n=100, random_state=42)
    not_relevant               = screened_df[~(screened_df["llm_relevant"])].sample(n=100, random_state=42)
    # prepare llm and human dataframe
    llm_df                     = pd.concat([relevant, not_relevant])
    human_df                   = llm_df[["post_id", "subreddit", "title", "body", "url"]].copy()
    human_df["human_relevant"] = ""
    llm_label_df               = llm_df[["post_id", "llm_relevant", "llm_confidence", "llm_reason"]].copy()

    # save the csv files
    human_df.to_csv(human_file, index=False, encoding="utf-8-sig")
    llm_label_df.to_csv(llm_file, index=False, encoding="utf-8-sig")

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():
    # 00_INSTRUCTION
    print("-"*25)
    print("00_Instruction")
    print("-"*25)
    print("Uncomment `generate_sample` in `02_SAMPLING` to start.\nIf you have already run it once, be careful before uncommenting it, \nbecause the file will be completely rerun and regenerated as a new file.")

    # 01_DIRECTORIES
    # dir preparation
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir   = os.path.join(script_dir, "..", "data")

    # dir of input files
    screened_file = os.path.join(data_dir, POST_LIST_SCREENED)
    # dir of output files
    human_file    = os.path.join(data_dir, AGREEMENT_SAMPLE)
    llm_file      = os.path.join(data_dir, AGREEMENT_SAMPLE_LLM_LABELS)
    agr_dis_file  = os.path.join(data_dir, AGREEMENT_DISAGREEMENT)

    # 02_SAMPLING
    # The blind sample was drawn once (seed=42) and hand-labelled.
    # generate_sample() is kept for provenance; it is not re-run here,
    # since re-running would overwrite the hand-labelled sample.
    # generate_sample(screened_file, human_file, llm_file)

    # 03_CALCULATE THE AGREEMENT
    # read the files
    human_df     = pd.read_csv(human_file, encoding="utf-8-sig")
    llm_df       = pd.read_csv(llm_file, encoding="utf-8-sig")
    # merge human and llm files
    agreement_df = human_df.merge(llm_df, on="post_id", how="inner")
    screened_df  = pd.read_csv(screened_file, encoding="utf-8-sig")
    agreement_df = agreement_df.merge(
        screened_df[["post_id", "llm_risk_level", "llm_psychosis"]],
        on="post_id", how="inner"
    )
    # exclude the posts of high risk & psychosis symptoms
    agreement_df = agreement_df[
        (agreement_df["llm_risk_level"] != 3) &
        (agreement_df["llm_psychosis"] != True)
    ]

    # agreement calculation
    human = agreement_df["human_relevant"]
    llm   = agreement_df["llm_relevant"]

    pct_agree = (human == llm).mean()
    ac1       = gwet_ac1(human.tolist(), llm.tolist())
    cohen_k   = kappa_score(human.tolist(), llm.tolist())

    # print the result
    print("-"*25)
    print("01_Results")
    print("-"*25)
    print(f"Remaining posts after excluding the posts of high risk & psychosis symptoms: {len(agreement_df)}")   # 应为 195
    print(f"Percent agreement: {pct_agree:.3f}")
    print(f"Cohen's kappa:     {cohen_k:.3f}")
    print(f"Gwet's AC1:        {ac1:.3f}")

    # 04_CONFUSION MATRIX
    tp = ((human == True)  & (llm == True)).sum()    # both sides judged it as relevant
    tn = ((human == False) & (llm == False)).sum()   # both sides judged it as irrelevant
    fp = ((human == False) & (llm == True)).sum()    # human judged it as irrelevant, llm judged it as relevant
    fn = ((human == True)  & (llm == False)).sum()   # human judged it as relevant, llm judged it as irrelevant

    # export disagreement cases
    disagreement_cases = agreement_df[agreement_df["human_relevant"] != agreement_df["llm_relevant"]][
        ["post_id", "title", "human_relevant", "llm_relevant", "llm_reason"]
    ].copy()

    disagreement_cases.to_csv(agr_dis_file, index=False, encoding="utf-8-sig")

    print("-"*25)
    print("03_Confusion")
    print("-"*25)
    print(f"Disagreement case in total: {len(disagreement_cases)}\n")
    print(f"TP: {tp} | both sides judged it as relevant\n")
    print(f"TN: {tn} | both sides judged it as irrelevant\n")
    print(f"FP: {fp} | human judged it as irrelevant, llm judged it as relevant\n")
    print(f"FN: {fn} | human judged it as relevant, llm judged it as irrelevant\n")
    print("-"*25)
    print("Disagreement cases:\n")
    for _, row in disagreement_cases.iterrows():
        print(f"post_id: {row['post_id']}")
        print(f"title:   {row['title']}")
        print(f"human_relevant: {row['human_relevant']} | llm_relevant: {row['llm_relevant']}")
        print(f"llm_reason: {row['llm_reason']}")
        print("-"*25)



if __name__ == "__main__":
    main()