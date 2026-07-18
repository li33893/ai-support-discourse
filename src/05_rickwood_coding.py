"""
================================================================================
SCRIPT: 05_rickwood_coding.py
PURPOSE: LLM Rickwood dimension coding + exclusion screening (pipeline stage 5)
================================================================================

WHAT THIS SCRIPT DOES:
    1. Judges whether each post should be excluded (fails inclusion criteria, EX-1 to EX-9)
    2. Codes three Rickwood dimensions for non-excluded posts: Timeframe, Source, Type
    3. Supports checkpointing for resumable runs

FLOW:
    1. code_post(title, body)
       - Sends one post to the LLM with the coding system prompt
       - Parses the JSON verdict (exclusion + three dimensions)
       -> returns a result dict per post

    2. main()
       - Reads input, resumes from checkpoint if requested
       - Codes each post, writes one checkpoint line per post
       - Merges results back, renames LLM columns, saves output
       -> {input_stem}_llm_coded.csv

INPUT FILES:
    pilot_sample.csv          Pilot validation sample 

OUTPUT FILES:
    pilot_sample_llm_coded.csv         Original rows + LLM codes
    pilot_sample_llm_checkpoint.jsonl  Per-post checkpoint (deletable after success)

NEXT STEP: 06_rickwood_validation.py

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
import os
import json
import requests
import argparse
import time
from config_local import API_KEY
from rickwood_prompt import SYSTEM_PROMPT

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# API request settings
# payload:
MODEL            = "claude-sonnet-4-20250514"
TEMPERATURE      = 0
MAX_TOKENS       = 1000
# request:
RATE_LIMIT_DELAY = 0.5
BASE_URL         = "https://api.anthropic.com/v1/messages"
API_VERSION      = "2023-06-01"

# input files
PILOT_SAMPLE  = "pilot_sample.csv"

# ________________________________________________________________________________

# FUNCTION AREA

# ________________________________________________________________________________

# code the posts
def code_post (title, body):
  post    = f"TITLE: {title}\nBODY: {body}"
  payload = {
    "model" :       MODEL,
    "temperature" : TEMPERATURE,
    "max_tokens" :  MAX_TOKENS,
    "system" :      SYSTEM_PROMPT,
    "messages" :    [{"role" : "user", "content" : post}]
}
  
  try:
    resp = requests.post(
      BASE_URL,
      headers = {
          "Content-Type":      "application/json",
          "x-api-key":         API_KEY,
          "anthropic-version": API_VERSION
      },
      json    = payload,
      timeout = 60
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

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():

  # 01_ARGUMENT PARSERS
  parser = argparse.ArgumentParser()
  parser.add_argument("--resume", action="store_true")
  args = parser.parse_args()

  # 02_DIRECTORIES
  script_dir      = os.path.dirname(os.path.abspath(__file__))
  data_dir        = os.path.join(script_dir, "..", "data")
  stem            = os.path.splitext(PILOT_SAMPLE)[0]
  input_file      = os.path.join(data_dir, PILOT_SAMPLE)
  output_file     = os.path.join(data_dir, f"{stem}_llm_coded.csv")
  checkpoint_file = os.path.join(data_dir, f"{stem}_llm_checkpoint.jsonl")

  # 03_READ INPUT
  input_df = pd.read_csv(input_file, encoding="utf-8-sig")
  print(f"Read {len(input_df)} posts.")

  # 04_RESUME FROM CHECKPOINT
  completed = {}
  if args.resume and os.path.exists(checkpoint_file):
      with open(checkpoint_file, "r", encoding="utf-8") as f:
          for line in f:
              rec = json.loads(line)
              completed[rec["post_id"]] = rec
      print(f"{len(completed)} posts already done, resuming.")

  # 05_CODE LOOP
  results = []
  for i, row in input_df.iterrows():
      post_id = row["post_id"]

      if post_id in completed:
          results.append(completed[post_id])
          continue

      result = code_post(row["title"], row["body"])
      result["post_id"] = post_id
      results.append(result)

      with open(checkpoint_file, "a", encoding="utf-8") as f:
          f.write(json.dumps(result, ensure_ascii=False) + "\n")

      time.sleep(RATE_LIMIT_DELAY)

  # 06_MERGE + SAVE
  result_df = pd.DataFrame(results)

  result_df = result_df.rename(columns={
      "excluded":             "llm_excluded",
      "reason_for_exclusion": "llm_reason_for_exclusion",
      "timeframe":            "llm_timeframe",
      "source":               "llm_source",
      "usage_intent":         "llm_usage_intent",
      "confidence":           "llm_coding_confidence",
      "reasoning":            "llm_reasoning",
  })

  out_df = input_df.merge(result_df, on="post_id", how="left")
  out_df.to_csv(output_file, index=False, encoding="utf-8-sig")
  print(f"Saved to {output_file}")

  # 07_SUMMARY
  n_excluded = (out_df["llm_excluded"] == True).sum()
  n_coded    = (out_df["llm_excluded"] == False).sum()
  n_errors   = out_df["llm_excluded"].isna().sum()

  print("-" * 25)
  print(f"Total:    {len(out_df)}")
  print(f"Excluded: {n_excluded}")
  print(f"Coded:    {n_coded}")
  print(f"Errors:   {n_errors}")

  if n_coded > 0:
      coded = out_df[out_df["llm_excluded"] == False]
      print(f"Timeframe: {coded['llm_timeframe'].value_counts().to_dict()}")
      print(f"Source:    {coded['llm_source'].value_counts().to_dict()}")
      print(f"Type:      {coded['llm_usage_intent'].value_counts().to_dict()}")


if __name__ == "__main__":
  main()