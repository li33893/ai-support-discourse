"""
================================================================================
SCRIPT: 09_spot_check_validate.py
PURPOSE: Human-LLM agreement check on the held-out spot-check sample (pipeline stage 9)
================================================================================

WHAT THIS SCRIPT DOES:
    1. Merges the blind human codes with the LLM codes on post_id
    2. Drops posts the human coder excluded, then verifies every remaining human
       code is a legal label from the coding scheme
    3. Computes percent agreement, Cohen's kappa and Gwet's AC1 per Rickwood
       dimension (Timeframe, Source, Type)
    4. Counts and prints the disagreement pairs per dimension, so directional
       bias can be inspected
    5. For human categories involved in disagreements, prints correct_n,
       precision and recall, and exports these category-level results
    6. Reports PASS/FAIL against KAPPA_THRESHOLD and exports the summary table
       and the per-post disagreement list

FLOW:
    1. gwet_ac1(human, llm, categories)
       - Multi-class Gwet AC1; categories fixes q, which cannot be inferred
         from the data
       -> returns (p_o - p_e) / (1 - p_e)

    2. kappa_score(human, llm)
       - Thin wrapper over sklearn's cohen_kappa_score

    3. main()
       - 01-02: paths, read both inputs, merge on post_id
       - 03: drop human-excluded posts, then validate human labels against the
             scheme; exits on any illegal value
       - 04: per-dimension percent agreement, kappa and AC1
       - 05: disagreement pairs and category metrics per dimension
       - 06-07: results table and terminal summary
       - 08: export summary, disagreement and disagreement-category CSVs

NOTES:
    This script is derivative and fully re-runnable; it reads frozen inputs and
    writes only to outputs/. spot_check_blind.csv carries a small number of
    stray non-UTF-8 bytes, hence encoding_errors="replace" on that read only.

NEXT STEP: 10_descriptive_stats.py
================================================================================
"""
# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import pandas as pd
from sklearn.metrics import cohen_kappa_score
import os
import sys
from collections import Counter
# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files
HUMAN_INPUT_FILE   = "spot_check_blind.csv"
LLM_INPUT_FILE     = "spot_check_llm_codes.csv"
VALIDATION_SUMMARY             = "spot_check_validation_summary.csv"
DISAGREEMENTS                  = "spot_check_disagreements.csv"
DISAGREEMENT_CATEGORY_METRICS = "spot_check_disagreement_category_metrics.csv"

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

def gwet_ac1(human: list, llm: list, categories: list):
    n = len(human)
    q = len(categories)

    p_o = sum(h == l for h, l in zip(human, llm)) / n

    pi_sum = 0.0
    for k in categories:
        pi_k = (human.count(k) + llm.count(k)) / (2 * n)
        pi_sum += pi_k * (1 - pi_k)
    p_e = pi_sum / (q - 1)

    return (p_o - p_e) / (1 - p_e)


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
    outputs_dir  = os.path.join(current_dir, "..", "outputs")

    # input file paths
    human_input_file = os.path.join(data_dir, HUMAN_INPUT_FILE)
    llm_input_file   = os.path.join(data_dir, LLM_INPUT_FILE)

    # 02_READ FILES AND CLEAN THE DATA
    human_df = pd.read_csv(human_input_file, encoding="utf-8-sig", encoding_errors="replace")
    llm_df   = pd.read_csv(llm_input_file, encoding="utf-8-sig")
  
    # merge two dfs into one
    llm_df    = llm_df[["post_id", "llm_timeframe", "llm_source", "llm_usage_intent"]]
    merged_df = human_df.merge(llm_df, on="post_id", how="inner")

    # 03_DROP HUMAN-EXCLUDED POSTS AND CLEAN THE TYPOS
    print("="*58)
    print("Exclusion check:")
    print("="*58)
    excluded_mask = merged_df["excluded"].astype(str).str.strip().str.upper().str.startswith("EX")
    n_excluded    = excluded_mask.sum()

    merged_df     = merged_df[~excluded_mask]

    n_analyzed    = len(merged_df)
    n_total       = n_analyzed + n_excluded
    print(f"human-excluded dropped: {n_excluded} | remaining: {len(merged_df)}") 
    print("="*58)
    print("\n\n")  

    # recognize typos
    print("="*58)
    print("Check spellings of the human columns")
    print("="*58)
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
    print("="*58)
    print("\n\n")

    # 04_PRINT RESULTS
    print("="*58)
    print(f"AGREEMENT CALCULATION\n")
    print("-" * 58)
    print(f"{'dimension':<12}{'agree':>9}{'pct':>9}{'kappa':>9}{'AC1':>9}{'':>6}")
    print("-" * 58)
    # agreement calculation
    human_type = merged_df["human_usage_intent"]
    llm_type   = merged_df["llm_usage_intent"]

    # timeframe
    human_tf = merged_df["human_timeframe"]
    llm_tf   = merged_df["llm_timeframe"]

    pct_agree_tf = (human_tf == llm_tf).mean()
    cohen_k_tf   = kappa_score(human_tf.tolist(), llm_tf.tolist())
    ac1_tf       = gwet_ac1(human_tf.tolist(), llm_tf.tolist(), DIMENSIONS[0]["labels"])
    n_agree_tf   = (human_tf   == llm_tf).sum()
    pass_tf      = "PASS" if cohen_k_tf   >= KAPPA_THRESHOLD else "FAIL"
    print(f"{'Timeframe':<12}{f'{n_agree_tf}/{n_analyzed}':>9}{pct_agree_tf*100:>8.1f}%{cohen_k_tf:>9.3f}{ac1_tf:>9.3f}{pass_tf:>6}")

    # source
    human_src = merged_df["human_source"]
    llm_src   = merged_df["llm_source"]

    pct_agree_src = (human_src == llm_src).mean()
    cohen_k_src   = kappa_score(human_src.tolist(), llm_src.tolist())
    ac1_src       = gwet_ac1(human_src.tolist(), llm_src.tolist(), DIMENSIONS[1]["labels"])
    pass_src      = "PASS" if cohen_k_src  >= KAPPA_THRESHOLD else "FAIL"
    n_agree_src   = (human_src  == llm_src).sum()
    print(f"{'Source':<12}{f'{n_agree_src}/{n_analyzed}':>9}{pct_agree_src*100:>8.1f}%{cohen_k_src:>9.3f}{ac1_src:>9.3f}{pass_src:>6}")

    # type
    human_type = merged_df["human_usage_intent"]
    llm_type   = merged_df["llm_usage_intent"]

    pct_agree_type = (human_type == llm_type).mean()
    cohen_k_type   = kappa_score(human_type.tolist(), llm_type.tolist())
    ac1_type       = gwet_ac1(human_type.tolist(), llm_type.tolist(), DIMENSIONS[2]["labels"]) 
    n_agree_type   = (human_type == llm_type).sum()
    pass_type      = "PASS" if cohen_k_type >= KAPPA_THRESHOLD else "FAIL"
    print(f"{'Type':<12}{f'{n_agree_type}/{n_analyzed}':>9}{pct_agree_type*100:>8.1f}%{cohen_k_type:>9.3f}{ac1_type:>9.3f}{pass_type:>6}")

    print("-" * 58)

    total_agree     = n_agree_tf + n_agree_src + n_agree_type
    total_decisions = n_analyzed * 3
    mean_kappa      = (cohen_k_tf + cohen_k_src + cohen_k_type) / 3

    print(f"pooled raw agreement: {total_agree}/{total_decisions} = {total_agree/total_decisions*100:.1f}%")
    print(f"mean kappa (arithmetic mean, not a pooled statistic): {mean_kappa:.3f}")
    print(f"threshold: kappa >= {KAPPA_THRESHOLD}")
    print("=" * 58)

    print()

    print("\n\n")

    # collect disagreement pairs per dimension
    print("="*58)
    print(f"DISAGREEMENT CASES\n")
    pair_rows     = [] # to collect information of each diagreement case
    category_rows = [] # to collect metrics only for human categories involved in disagreements

    for d in DIMENSIONS:

        pairs = [] # to collect diagreed pairs for later counting

        # collecting process
        for p, h, l in zip(merged_df["post_id"], 
                           merged_df[d["human_col"]], 
                           merged_df[d["llm_col"]]):
            if h != l:
                pairs.append((h, l))
                pair_rows.append({
                    "dimension":  d["name"],
                    "post_id":    p,
                    "human_code": h,
                    "llm_code":   l,
                })
                
        # count the exact number of each pair
        counted = Counter(pairs)

        # print the results
        print("-"*58)
        print(f"{d['name']}: {len(pairs)} disagreements (human -> llm)")
        for (h, l), n in counted.most_common():
            print(f"    {h} -> {l} x{n}")

        # print correct_n, precision and recall only for human categories involved in disagreements
        disagreed_human_labels = [
            label for label in d["labels"]
            if any(h == label for h, l in pairs)
        ]

        if disagreed_human_labels:
            print()
            print(f"{'category':<14}{'correct_n':>12}{'precision':>12}{'recall':>12}")

            human_codes = merged_df[d["human_col"]]
            llm_codes   = merged_df[d["llm_col"]]

            for label in disagreed_human_labels:
                correct_n = ((human_codes == label) & (llm_codes == label)).sum()
                llm_n     = (llm_codes == label).sum()
                human_n   = (human_codes == label).sum()

                precision = correct_n / llm_n if llm_n > 0 else float("nan")
                recall    = correct_n / human_n if human_n > 0 else float("nan")

                print(f"{label:<14}{correct_n:>12}{precision:>12.3f}{recall:>12.3f}")

                category_rows.append({
                    "dimension": d["name"],
                    "category":  label,
                    "correct_n": correct_n,
                    "precision": precision,
                    "recall":    recall,
                })

        print("-"*58)

    print("="*58)

    # 05_SAVE TO OUTPUTS
    summary_path  = os.path.join(outputs_dir, VALIDATION_SUMMARY)
    dis_path      = os.path.join(outputs_dir, DISAGREEMENTS)
    category_path = os.path.join(outputs_dir, DISAGREEMENT_CATEGORY_METRICS)

    summary_df = pd.DataFrame({
        "dimension":  ["Timeframe", "Source", "Type"],
        "n":          [n_analyzed, n_analyzed, n_analyzed],
        "n_agree":    [n_agree_tf, n_agree_src, n_agree_type],
        "pct_agree":  [pct_agree_tf, pct_agree_src, pct_agree_type],
        "kappa":      [cohen_k_tf, cohen_k_src, cohen_k_type],
        "ac1":        [ac1_tf, ac1_src, ac1_type],
        "result":     [pass_tf, pass_src, pass_type],
        "n_total":    [n_total, n_total, n_total],
        "n_excluded": [n_excluded, n_excluded, n_excluded],
    })
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(pair_rows).to_csv(dis_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(category_rows).to_csv(category_path, index=False, encoding="utf-8-sig")

    print(f"\nSummary saved to          {summary_path} ({len(summary_df)} rows)")
    print(f"Disagreements saved to    {dis_path} ({len(pair_rows)} rows)")
    print(f"Category metrics saved to {category_path} ({len(category_rows)} rows)")

if __name__ == "__main__":
    main()

