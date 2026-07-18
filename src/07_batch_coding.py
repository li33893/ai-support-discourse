"""
================================================================================
SCRIPT: 07_batch_coding.py
PURPOSE: LLM Rickwood dimension coding (full corpus)
================================================================================


WHAT THIS SCRIPT DOES:
    Apply the finalized Rickwood coding prompt to the full corpus (2,127 posts).
    For each post the model does two things:
        STEP 1  exclusion screening (EX-1 ~ EX-9)
        STEP 2  code three dimensions — Timeframe / Source / Type
    Model: claude-sonnet-4-20250514 @ temperature=0.

FLOW:
    read cleaned corpus
      -> for each post: call Claude API, parse the returned JSON
      -> collect results, merge back onto the corpus
      -> write coded corpus, print coding distribution

INPUT:
    posts_list_cleaned.csv          (2,127 posts, from 04_data_cleaning.py)

OUTPUT:
    posts_list_cleaned_llm_coded.csv   (2,127 rows)
        = input + LLM columns:
        llm_excluded, llm_reason_for_exclusion,
        llm_timeframe, llm_source, llm_usage_intent,
        llm_reasoning
        of which llm_excluded=False -> 1,994 posts go to analysis

NEXT STEP:
    08_spot_check_sample.py
________________________________________________________________________________

OTHER RELEVANT INFORMATION:

# ─── Anthropic API response structure ───

{
  "id": "msg_01XXXX",
  "type": "message",
  "role": "assistant",
  "model": "claude-sonnet-4-20250514",
  "content": [
    {
      "type": "text",
      "text": "what the model responded"
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567
  }
}

================================================================================

"""
# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import pandas as pd
import json
import time
import requests
import os
import sys
import argparse
from config_local import API_KEY
from rickwood_prompt import SYSTEM_PROMPT

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files
POSTS_LIST_CLEANED = "posts_list_cleaned"

# API request settings
MODEL            = "claude-sonnet-4-20250514"
TEMPERATURE      = 0
MAX_TOKENS       = 1000
RATE_LIMIT_DELAY = 0.6
BASE_URL         = "https://api.anthropic.com/v1/messages"
API_VERSION      = "2023-06-01"
MAX_RETRIES      = 5
TIMEOUT          = 90

# cost estimation
PRICE_IN         = 3     # $/M input tokens
PRICE_OUT        = 15    # $/M output tokens
CACHE_WRITE_MULT = 1.25  # 5-minute cache write
CACHE_READ_MULT  = 0.1   # cache hit

# ________________________________________________________________________________

# FUNCTION AREA

# ________________________________________________________________________________

def code_post(title, body):

    post    = f"TITLE: {title}\n\nBODY: {body}"
    payload = {
        "model":       MODEL,
        "temperature": TEMPERATURE,
        "max_tokens":  MAX_TOKENS,
            "system": [
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
        "messages": [{"role": "user", "content": post}]
    }
    
    try:
        resp = requests.post(
            BASE_URL,
            headers  = {
                "Content-Type":      "application/json",
                "x-api-key":         API_KEY,
                "anthropic-version": API_VERSION
            },
            json    = payload,
            timeout = TIMEOUT
        )

        resp.raise_for_status()
        text = resp.json()["content"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data

    except Exception as e:
        return _error_result(str(e))
    
# output errors as dict
def _error_result(msg):
  return {
      "excluded":             None,
      "reason_for_exclusion": None,
      "timeframe":            None,
      "source":               None,
      "usage_intent":         None,
      "confidence":           None,
      "reasoning":            f"ERROR: {msg}"
  }

# check if the file already exists, in case the file would be mistakenly covered
def if_file_exists(output_file):
    if os.path.exists(output_file):
        print("The file already exists.")
        sys.exit(1)

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main ():

    # 01_ARGUMENT PARSERS
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args   = parser.parse_args()
    
    # 02_DIR
    # dir preparation
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir    = os.path.join(current_dir, "..", "data")
    stem       = POSTS_LIST_CLEANED

    # input file
    input_file = os.path.join(data_dir, f"{stem}.csv")

    # output data file naming
    output_file = os.path.join(data_dir, f"{stem}_llm_coded.csv")

    # additional output files
    check_point_file = os.path.join(data_dir, f"{stem}_llm_checkpoint.jsonl")
    error_file       = os.path.join(data_dir, f"{stem}_errors.csv")

    # in case the old file is mistakenly covered
    if not args.resume:
        if_file_exists(output_file)

    # 03_READ THE INPUT
    input_df = pd.read_csv(input_file, encoding="utf-8-sig")
    n_total  = len(input_df)
    print(f"read: {n_total} posts")

    # 04_RESUME FROM CHECKPOINT
    completed = {}
    if args.resume and os.path.exists(check_point_file):
        with open(check_point_file, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if rec["excluded"] is not None:
                    completed[rec["post_id"]] = rec
        print(f"{len(completed)} posts already done, resuming...")

    # 05_TIME_AND_COST_ESTIMATION
    prompt_tokens     = len(SYSTEM_PROMPT) / 4                # English ~4 chars/token
    avg_input_tokens  = input_df["word_count"].mean() * 1.3   # English ~1.3 tokens/word
    avg_output_tokens = 200                                   # rough guess

    cache_write = prompt_tokens * PRICE_IN * CACHE_WRITE_MULT / 1_000_000
    cache_read  = (n_total - 1) * prompt_tokens * PRICE_IN * CACHE_READ_MULT / 1_000_000
    post_cost   = n_total * avg_input_tokens * PRICE_IN / 1_000_000
    output_cost = n_total * avg_output_tokens * PRICE_OUT / 1_000_000

    est_total    = cache_write + cache_read + post_cost + output_cost
    est_time_min = n_total * (RATE_LIMIT_DELAY + 1.5) / 60   # 1.5s avg response time

    print("-" * 25)
    print(f"Posts: {n_total}")
    print(f"Est. cost: ${est_total:.2f}")
    print(f"Est. time: ~{est_time_min:.0f} min")
    print("-" * 25)

    # 06_CONFIRM BEFORE SPENDING
    n_todo = n_total - len(completed)
    print(f"To code: {n_todo} posts ({len(completed)} already done)")
    if input("Continue? (y/n): ").strip().lower() != "y":
        print("Aborted.")
        sys.exit(0)

    # 07_CODE LOOP
    results = [] 
    error_n = 0

    for i, post in input_df.iterrows():
        post_id = post["post_id"]

        # to check if the post has already exited in the checkponit.jsonl
        if post_id in completed:
            results.append(completed[post_id])
            continue

        result            = code_post(post["title"], post["body"])
        result["post_id"] = post_id

        # retry when error occurs until runs out the trials
        if result["excluded"] is None:
            # within presecified MAX_RETIRES, try again
            for attemp in range(MAX_RETRIES):
                print(f"{result['reasoning']}, trying again ({attemp+1}/{MAX_RETRIES})...")
                # if failed again, run another time
                result = code_post(post["title"], post["body"])
                result["post_id"] = post_id
                if result["excluded"] is not None:
                    break
        
        if result["excluded"] is None:
            error_n += 1

        # if failed all the trials, save all the result recodrs in the results list as a jsonl file for later resuming
        results.append(result)

        # put the record into jsonl file
        with open(check_point_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        # progress
        if len(results) % 20 == 0:
            print(f"{len(results)}/{n_total} done, errors: {error_n}")

        # throttle
        time.sleep(RATE_LIMIT_DELAY)
    
    # 08_MERGE AND SAVE
    result_df = pd.DataFrame(results)
    result_df = result_df.drop(columns=["confidence"])
    result_df = result_df.rename(columns={
        "excluded":             "llm_excluded",
        "reason_for_exclusion": "llm_reason_for_exclusion",
        "timeframe":            "llm_timeframe",
        "source":               "llm_source",
        "usage_intent":         "llm_usage_intent",
        "reasoning":            "llm_reasoning",
    })

    out_df = input_df.merge(result_df, on="post_id", how="left")
    # check if the two df are equally long
    assert len(out_df) == len(input_df), f"row count changed: {len(input_df)} -> {len(out_df)} (duplicate post_id?)"
    out_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"saved: {output_file}")

    # 09_SUMMARY
    n_excluded = (out_df["llm_excluded"] == True).sum()
    n_coded    = (out_df["llm_excluded"] == False).sum()
    n_errors   = out_df["llm_excluded"].isna().sum()

    print("-" * 25)
    print(f"total:    {len(out_df)}")
    print(f"excluded: {n_excluded}")
    print(f"coded:    {n_coded}")
    print(f"errors:   {n_errors}")

    coded = out_df[out_df["llm_excluded"] == False]
    print(f"timeframe: {coded['llm_timeframe'].value_counts().to_dict()}")
    print(f"source:    {coded['llm_source'].value_counts().to_dict()}")
    print(f"type:      {coded['llm_usage_intent'].value_counts().to_dict()}")

    # 10_EXPORT ERRORS
    if n_errors > 0:
        err_df = out_df[out_df["llm_excluded"].isna()][["post_id", "title"]]
        err_df.to_csv(error_file, index=False, encoding="utf-8-sig")
        print(f"{n_errors} errors saved to {error_file}. rerun with --resume to retry.")


if __name__ == "__main__":
    main()





