"""
================================================================================
SCRIPT: 12_sampling.py
PURPOSE: Descriptive figures of the three codes by subreddit 
================================================================================
WHAT   Draw the first-round close-reading sample (71 posts)
       from the coded corpus, following the sampling claim.

FLOW   Load coded corpus -> clean code columns -> check for NA
       and typos -> build each slot -> draw posts at random
       -> collect leftovers -> save

INPUT  ../data/posts_list_cleaned_llm_coded.csv

OUTPUT ../data/sampling_first_round.csv
       ../data/sampling_slot_counts.csv

NEXT STEP  
================================================================================

"""

import os
import pandas as pd
 
# ---------------------------------------------------------------
# Paths
# ---------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "..", "data")
 
INPUT_FILE = os.path.join(data_dir, "posts_list_cleaned_llm_coded.csv")
PILOT_FILE = os.path.join(data_dir, "pilot_sample.csv")
SPOT_FILE = os.path.join(data_dir, "spot_check_blind.csv")
OUTPUT_FILE = os.path.join(data_dir, "sampling_first_round.csv")
COUNT_FILE = os.path.join(data_dir, "sampling_slot_counts.csv")
 
SEED = 42
RESIDUAL_N = 5
 
# ---------------------------------------------------------------
# Valid code values, used to catch typos
# ---------------------------------------------------------------
VALID_TIMEFRAME = ["Habitual", "Episodic", "NM"]
VALID_SOURCE = ["Primary", "Supplement", "Parallel", "Solo", "Exploration", "NM"]
VALID_TYPE = ["ES", "VE", "CO", "RE", "CR", "PE", "SA", "SE",
              "FS", "RS", "TA", "SR", "N", "OT"]
VALID_SUBREDDIT = ["Anxiety", "depression", "mentalhealth", "therapy", "therapyGPT"]
 
 
# ---------------------------------------------------------------
# Load and clean
# ---------------------------------------------------------------
def load_corpus():
    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df = df[df["llm_excluded"] == False]
 
    # strip outer spaces on the code columns
    for col in ["llm_timeframe", "llm_source", "llm_usage_intent", "subreddit"]:
        df[col] = df[col].str.strip()
 
    print("Loaded", len(df), "analysable posts")
    return df
 
 
# ---------------------------------------------------------------
# Check for missing values and unexpected code values
# ---------------------------------------------------------------
def check_codes(df):
    print("\n--- NA check ---")
    for col in ["llm_timeframe", "llm_source", "llm_usage_intent",
                "subreddit", "post_id", "body", "word_count"]:
        n_missing = df[col].isna().sum()
        print(col, "missing:", n_missing)
 
    print("\n--- Typo check ---")
    checks = [
        ("llm_timeframe", VALID_TIMEFRAME),
        ("llm_source", VALID_SOURCE),
        ("llm_usage_intent", VALID_TYPE),
        ("subreddit", VALID_SUBREDDIT),
    ]
    for col, valid in checks:
        found = df[col].dropna().unique()
        unexpected = [v for v in found if v not in valid]
        if len(unexpected) == 0:
            print(col, "OK")
        else:
            print(col, "unexpected values:", unexpected)
 
    print("\n--- Duplicate check ---")
    print("duplicated post_id:", df["post_id"].duplicated().sum())
 
 
# ---------------------------------------------------------------
# Drop the posts already read during development.
# The pilot and spot check samples were read by hand to build the
# frame, so they are not drawn on again here.
# ---------------------------------------------------------------
def drop_development_posts(df):
    pilot = pd.read_csv(PILOT_FILE, encoding="utf-8-sig")
    spot = pd.read_csv(SPOT_FILE, encoding="utf-8-sig",
                       encoding_errors="replace")
 
    dev_ids = set(pilot["post_id"]) | set(spot["post_id"])
    print("\nDevelopment post_ids:", len(dev_ids))
 
    matched = df["post_id"].isin(dev_ids)
    print("found in corpus:", matched.sum())
    print("not found in corpus:", len(dev_ids) - matched.sum())
 
    df = df[~matched]
    print("remaining after dropping:", len(df))
    return df
 
 
# ---------------------------------------------------------------
# Slot definition
# Each slot: name, how many posts, and the filter it uses.
# timeframe / source / usage_intent / subreddit accept a list,
# None means the dimension is not restricted.
# ---------------------------------------------------------------
SLOTS = [
    # --- 2.2.3 dominant combinations and content groups ---
    {"name": "Anxiety Episodic x SA",
     "n": 4, "timeframe": ["Episodic"], "type": ["SA"],
     "source": None, "subreddit": ["Anxiety"]},
 
    {"name": "Anxiety Habitual x SA/RE",
     "n": 5, "timeframe": ["Habitual"], "type": ["SA", "RE"],
     "source": None, "subreddit": ["Anxiety"]},
 
    {"name": "Habitual x Primary x CO/VE",
     "n": 8, "timeframe": ["Habitual"], "type": ["CO", "VE"],
     "source": ["Primary"],
     "subreddit": ["depression", "mentalhealth", "therapy"]},
 
    {"name": "therapy Habitual x TA x Primary",
     "n": 5, "timeframe": ["Habitual"], "type": ["TA"],
     "source": ["Primary"], "subreddit": ["therapy"]},
 
    {"name": "therapy Habitual x TA x Supplement",
     "n": 4, "timeframe": ["Habitual"], "type": ["TA"],
     "source": ["Supplement"], "subreddit": ["therapy"]},
 
    {"name": "therapyGPT Habitual x TA x Primary",
     "n": 5, "timeframe": ["Habitual"], "type": ["TA"],
     "source": ["Primary"], "subreddit": ["therapyGPT"]},
 
    {"name": "therapyGPT Habitual x TA x Supplement",
     "n": 4, "timeframe": ["Habitual"], "type": ["TA"],
     "source": ["Supplement"], "subreddit": ["therapyGPT"]},
 
    {"name": "therapyGPT Habitual x TA x NM",
     "n": 6, "timeframe": ["Habitual"], "type": ["TA"],
     "source": ["NM"], "subreddit": ["therapyGPT"]},
 
    # --- 2.2.4 remaining combinations across communities ---
    {"name": "Habitual x SR x not Primary",
     "n": 3, "timeframe": ["Habitual"], "type": ["SR"],
     "source": ["Supplement", "Parallel", "Solo", "Exploration", "NM"],
     "subreddit": None},
 
    {"name": "Parallel x Habitual/NM",
     "n": 3, "timeframe": ["Habitual", "NM"], "type": None,
     "source": ["Parallel"], "subreddit": None},
 
    {"name": "mentalhealth NM x SE/PE",
     "n": 4, "timeframe": None, "type": ["SE", "PE"],
     "source": ["NM"], "subreddit": ["mentalhealth"]},
 
    {"name": "therapyGPT NM x SE",
     "n": 3, "timeframe": None, "type": ["SE"],
     "source": ["NM"], "subreddit": ["therapyGPT"]},
 
    {"name": "FS",
     "n": 2, "timeframe": None, "type": ["FS"],
     "source": None, "subreddit": None},
 
    {"name": "Habitual x Supplement x CO",
     "n": 1, "timeframe": ["Habitual"], "type": ["CO"],
     "source": ["Supplement"], "subreddit": None},
 
    {"name": "Primary x SE",
     "n": 2, "timeframe": None, "type": ["SE"],
     "source": ["Primary"], "subreddit": None},
 
    {"name": "Type = N",
     "n": 1, "timeframe": None, "type": ["N"],
     "source": None, "subreddit": None},
 
    {"name": "Habitual x ES",
     "n": 4, "timeframe": ["Habitual"], "type": ["ES"],
     "source": None, "subreddit": None},
 
    # --- 2.2.5 leftover combinations ---
    {"name": "therapy leftover",
     "n": 1, "timeframe": None, "type": None,
     "source": None, "subreddit": ["therapy"]},
 
    {"name": "Anxiety leftover",
     "n": 1, "timeframe": None, "type": None,
     "source": None, "subreddit": ["Anxiety"]},
]
 
 
# ---------------------------------------------------------------
# Apply one slot's filter
# ---------------------------------------------------------------
def filter_slot(df, slot):
    sub = df.copy()
    if slot["timeframe"] is not None:
        sub = sub[sub["llm_timeframe"].isin(slot["timeframe"])]
    if slot["source"] is not None:
        sub = sub[sub["llm_source"].isin(slot["source"])]
    if slot["type"] is not None:
        sub = sub[sub["llm_usage_intent"].isin(slot["type"])]
    if slot["subreddit"] is not None:
        sub = sub[sub["subreddit"].isin(slot["subreddit"])]
    return sub
 
 
# ---------------------------------------------------------------
# Draw the sample
# Posts are drawn at random within each slot. Posts already taken
# are not taken again.
# ---------------------------------------------------------------
def draw_sample(df):
    taken = []
    used_ids = set()
    counts = []
 
    for slot in SLOTS:
        pool = filter_slot(df, slot)
        pool = pool[~pool["post_id"].isin(used_ids)]
 
        picked = pool.sample(n=slot["n"], random_state=SEED).copy()
        picked["slot"] = slot["name"]
 
        taken.append(picked)
        used_ids.update(picked["post_id"])
 
        counts.append({
            "slot": slot["name"],
            "wanted": slot["n"],
            "available": len(pool),
            "taken": len(picked),
        })
        print(slot["name"], "- wanted", slot["n"],
              "available", len(pool), "taken", len(picked))
 
    return pd.concat(taken), pd.DataFrame(counts), used_ids
 
 
# ---------------------------------------------------------------
# Residual pool: everything no slot picked up, drawn at random
# ---------------------------------------------------------------
def draw_residual(df, used_ids):
    pool = df[~df["post_id"].isin(used_ids)]
    picked = pool.sample(n=RESIDUAL_N, random_state=SEED).copy()
    picked["slot"] = "residual pool"
    print("residual pool - taken", len(picked), "from", len(pool))
    return picked
 
 
# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
if __name__ == "__main__":
    df = load_corpus()
    check_codes(df)
    df = drop_development_posts(df)
 
    print("\n--- Drawing sample ---")
    sample, counts, used_ids = draw_sample(df)
 
    residual = draw_residual(df, used_ids)
    sample = pd.concat([sample, residual])
 
    keep = ["post_id", "slot", "subreddit", "llm_timeframe", "llm_source",
            "llm_usage_intent", "word_count", "title", "body", "url"]
    sample = sample[keep]
 
    sample.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    counts.to_csv(COUNT_FILE, index=False, encoding="utf-8-sig")
 
    print("\nTotal sampled:", len(sample))
    print("Saved to", OUTPUT_FILE)
    print("Slot counts saved to", COUNT_FILE)
