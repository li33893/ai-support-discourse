"""
================================================================================
SCRIPT: 06_rickwood_validation.py
PURPOSE: Human-LLM agreement check on the pilot Rickwood coding (pipeline stage 6)
================================================================================

WHAT THIS SCRIPT DOES:
    1. Compares human exclusion judgments against LLM exclusion judgments
    2. Computes Cohen's kappa per Rickwood dimension (Timeframe, Source, Type),
       on the subset of posts both coders retained and coded
    3. Prints a confusion matrix and the top confusion pairs for each dimension
    4. Exports every disagreeing post for qualitative review
    5. Reports PASS/FAIL against KAPPA_THRESHOLD; a PASS clears the coding prompt
       for the full-corpus run in 07_batch_coding.py

FLOW:
    1. print_confusion_matrix(cm, labels, title, file)
       - Renders one matrix to the terminal and to the .txt report

    2. analyze_confusions(cm, labels)
       - Ranks off-diagonal cells by count
       -> returns human->LLM confusion pairs, most frequent first

    3. main()
       - PART 1: exclusion agreement (accuracy, kappa, disagreeing posts)
       - PART 2: per-dimension kappa on the both-retained subset (n < 80)
                 kappa from sklearn; po and pe derived from the confusion matrix
       - PART 3: writes the disagreement list and the matrix report
       - PART 4: PASS/FAIL summary against KAPPA_THRESHOLD

NEXT STEP: 07_batch_coding.py
================================================================================
"""

# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

from sklearn.metrics import cohen_kappa_score, confusion_matrix
import os
import pandas as pd

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files
PILOT_SAMPLE_LLM_CODED = "pilot_sample_llm_coded.csv"

# output files
RICKWOOD_DISAGREEMENTS      = "rickwood_disagreements.csv"
RICKWOOD_CONFUSION_MATRICES = "rickwood_confusion_matrices.txt"  

# decide kappa threshold for passing
KAPPA_THRESHOLD = 0.61

# Rickwood coding dimensions: display name, human column, LLM column, label order.
DIMENSIONS = [
    {
        "name":      "Timeframe",
        "human_col": "timeframe",
        "llm_col":   "llm_timeframe",
        "labels":    ["Habitual", "Episodic", "NM"]
    },
    {
        "name":      "Source",
        "human_col": "help_seeking_ecology",
        "llm_col":   "llm_source",
        "labels":    ["Primary", "Parallel", "Supplement", "Solo", "Exploration", "NM"]
    },
    {
        "name":      "Type",
        "human_col": "usage_intent",
        "llm_col":   "llm_usage_intent",
        "labels":    ["ES", "VE", "CO", "RE", "CR", "PE", "SA", "SE", "FS", "RS", "TA", "SR", "N", "OT"]
    }   
]
# ________________________________________________________________________________

# FUNCTION AREA

# ________________________________________________________________________________

# print confusion_matrix and generate a output file for the result
def print_confusion_matrix(cm, labels, title, file):
    # pre-sepcified column length
    col_width = max(len(max(labels, key=len)), 5)

    # prepare a list to latr join.() into a text
    cm_rev = []

    # append the 1st part — title
    cm_rev.append(title)

    # append the second part — header collection
    sep    = "-"*50
    cm_rev.append(sep)
    header = f"{'':>{col_width}}" + "|" + "|".join(f"{l:>{col_width}}" for l in labels) + "|" 
    cm_rev.append(header)
    cm_rev.append(sep)
    
    # append the 3rd part — cm
    for i, row in enumerate(cm, start=0):
        line = f"{labels[i]:>{col_width}}|" + "|".join(f"{row[j]:>{col_width}}" for j in range(len(labels))) + "|"
        cm_rev.append(line)
    
    cm_rev.append(sep)

    # join into full text
    text = "\n".join(cm_rev)
    # quick look
    print(text)
    # write into a txt file
    file.write(text + "\n\n")

# sort out confusion items
def analyze_confusions(cm, labels):
    # prepare an empty list to append confusion items
    confusion_list = []
    
    # confusion items
    for i in range(len(labels)):
        for j in range(len(labels)):
            if i != j and cm[i][j] > 0:
                confusion_items           = {}
                confusion_items["human"]  = labels[i]
                confusion_items["llm"]    = labels[j]
                confusion_items["counts"] = cm[i][j]
                confusion_list.append(confusion_items)
        
    confusion_list.sort(key = lambda x : x["counts"], reverse=True)

    return confusion_list

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():

    # 01_READ THE INPUT FILE
    # dir preparation
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data       = os.path.join(script_dir, "..", "data")
    outputs    = os.path.join(script_dir, "..", "outputs")
    input_file = os.path.join(data, PILOT_SAMPLE_LLM_CODED)
    cm_path    = os.path.join(outputs, RICKWOOD_CONFUSION_MATRICES)

    # input_file to dataframe
    llm_coded = pd.read_csv(input_file)

    # 02_CLEAN THE DATA
    # eliminate the postential blank space
    for col in ["timeframe", "llm_timeframe", "help_seeking_ecology", "llm_source", "usage_intent", "llm_usage_intent"]:
        llm_coded[col] = llm_coded[col].astype(str).str.strip()
    
    # 03_EXCLUSION ACCURACY CALCULATION
    # prepare a mask for excluding the columns
    llm_coded["human_excluded"] = (llm_coded["excluded"] == "Y")
    # create a new column using bool (easier for comparison), since I mistakenly inputted String "Y" instead of bool
    not_excluded = (                               
        (~llm_coded["human_excluded"]) &          
        (~llm_coded["llm_excluded"])
    )

    # exclusion accuacy calculation & export diagreement cases                                             
    exclusion_dis               = llm_coded[(llm_coded["llm_excluded"]) != llm_coded["human_excluded"]].copy() # the number disagreement cases for exclusion
    exclusion_accuracy          = 1 - len(exclusion_dis)/len(llm_coded)                                        # calcute the exclusion accuracy
    exclusion_kappa             = cohen_kappa_score(llm_coded['human_excluded'], llm_coded['llm_excluded'])    # calculate the kappa

    # print the results
    print(f"Exclusion accuracy: {exclusion_accuracy:.3f}")
    print(f"Exclusion kappa:    {exclusion_kappa:.3f}")
    print(f"Disagreements:      {len(exclusion_dis)} cases")


    # 04_PRINT THE CONFUSION MATRIX AND PUT IT INTO OUTPUTFILE
    with open(cm_path, "w", encoding="utf-8") as output_file:
        # a list to save disagreement cases
        all_disagreements = []

        # a dict to collect agreement data
        kappa_results     = {} 

        for dimension in DIMENSIONS:
            # export needed columns and make a confusion matrix
            human_col = dimension["human_col"]
            human     = llm_coded.loc[not_excluded, human_col]
            llm_col   = dimension["llm_col"]
            llm       = llm_coded.loc[not_excluded, llm_col]
            labels    = dimension["labels"]

            # save disagreement cases into all_disagreement
            llm_coded_cleaned         = llm_coded.loc[not_excluded, ["post_id", human_col, llm_col, "llm_reasoning", "coder_notes"]]
            dis                       = (llm_coded_cleaned[human_col] != llm_coded_cleaned[llm_col])
            llm_code_dis              = llm_coded_cleaned[dis].copy()
            llm_code_dis              = llm_code_dis.rename(columns={human_col: "human_code", llm_col: "llm_code"})
            llm_code_dis["dimension"] = dimension["name"]
            all_disagreements.append(llm_code_dis)

            # generate confusion matrix and calculate k(put it into dict), pe, po
            cm                               = confusion_matrix(human, llm, labels=labels)
            kappa                            = cohen_kappa_score(human, llm, labels=labels)
            kappa_results[dimension["name"]] = kappa

            po    = cm.trace() / len(human)
            pe    = (cm.sum(axis=1) * cm.sum(axis=0)).sum() / (len(human) ** 2)

            # sort out unexpected values
            human_val  = set(human)
            llm_val    = set(llm)
            allow      = set(labels)
            unexpected = (human_val | llm_val) - allow
            if len(unexpected) > 0:
                print(f"There are unexpected vlaues contained in {dimension['name']}, \nunexpected values: {unexpected}")

            # produce the title of matrix and output file names accordingly 
            fail_or_pass = "PASS" if kappa >= KAPPA_THRESHOLD else "FAIL"
            title        = f"--- {dimension['name']} (kappa={kappa:.3f}, n={len(human)}) {fail_or_pass} ---"
            print(f"\n--- {dimension['name']} ---")
            print(f"  kappa={kappa:.3f}  (po={po:.3f}, pe={pe:.3f})  {fail_or_pass}")

            # generate confusion matrix file and print the result
            print_confusion_matrix(cm, labels, title, output_file)

            # save disagreement cases file and print top 5 confusion cases
            confusions = analyze_confusions(cm, labels)
            if confusions:
                conf_lines = ["Top confusion pairs:"]
                for c in confusions[:5]:
                    conf_lines.append(f"    human={c['human']} -> llm={c['llm']}: {c['counts']}")
                conf_text = "\n".join(conf_lines)
                print(conf_text)
                output_file.write(conf_text + "\n\n")
    
    # 05_export disagreements to CSV
    dis_path = os.path.join(outputs, RICKWOOD_DISAGREEMENTS)
    dis_df   = pd.concat(all_disagreements, ignore_index=True)
    dis_df.to_csv(dis_path, index=False, encoding="utf-8-sig")
    print(f"\nDisagreements saved to {dis_path} ({len(dis_df)} rows)")

    # 06_summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    all_pass = True
    for name, k in kappa_results.items():
        status = "PASS" if k >= KAPPA_THRESHOLD else "FAIL"
        if k < KAPPA_THRESHOLD:
            all_pass = False
        print(f"  {name}: kappa={k:.3f} {status}")
    if all_pass:
        print("\nAll passed. Ready for 07_batch_coding.py.")
    else:
        print("\nSome failed. Revise SYSTEM_PROMPT in 05 and re-run.")

if __name__ == "__main__":
    main()









