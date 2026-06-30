"""
================================================================================
SCRIPT: 01_collect.py
PURPOSE: Data collection + keyword pre-screening (pipeline stage 1)
================================================================================

WHAT THIS SCRIPT DOES:
    1. Downloads raw Reddit posts from the target subreddits (Arctic Shift API)
    2. Keeps only posts that talk about AI

FLOW:
    1. Set the run size
       - TEST_MODE = True  -> small test run (1 subreddit, 1 month, max 300)
       - TEST_MODE = False -> full run (5 subreddits, 38 months, no cap)

    2. Download raw posts  [fetch_posts_arcticshift()]
       - Goes through each subreddit, then each month
       - Asks the API for posts page by page, using time as the marker
       - Skips posts already seen, and handles errors (too-big time window,
         network problems, same-second posts)
       - Saves title, body, and other info into one big list
       -> writes posts_list_raw.csv

    3. Keyword filter  [keyword_filter()]
       - Keeps a post only if ALL of these are true:
           a. it mentions AI (a keyword or the word "ai")
           b. it has at least 50 words
           c. the body is real text (not deleted, removed, or empty)
       -> writes posts_list_kw_filtered.csv

    4. Save hit-rate log
       - For each subreddit and month: how many raw, how many kept, what percent
       -> writes posts_list_kw_hit_log.json

OUTPUT FILES:
    posts_list_raw.csv          All posts, before filtering
    posts_list_kw_filtered.csv  Posts that passed the keyword filter
    posts_list_kw_hit_log.json  How many posts were kept, by subreddit and month

NEXT STEP: screening_prompt.py (use the LLM to check if posts are relevant)

________________________________________________________________________________

OTHER RELEVANT INFORMATION:

# ─── Arctic Shift API response structure ───
# resp.json() returns a dict (the outermost layer):
#   data                       -> dict
#     └─ data["data"]          -> list of posts (up to 100 per request)
#         └─ each item (p)     -> dict (one post)
#
# Fields on each post (p):
#   p["id"]           -> str    unique Reddit post id (used for dedup via seen_ids)
#   p["created_utc"]  -> int    Unix timestamp in seconds (used to advance current_after)
#   p["title"]        -> str    post title
#   p["selftext"]     -> str    post body (may be empty, "[deleted]", or "[removed]")
#   p["score"]        -> int    net upvotes
#   p["permalink"]    -> str    relative URL path (prepend "https://reddit.com" for full link)
#
# Notes:
#   - Field names are fixed (Reddit's data format), but a field may be missing or empty.
#   - Use p["id"] directly (every post has one); use p.get("title", "") for optional fields.

================================================================================
"""

# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import requests
import pandas as pd
import time
import json
import re
from datetime import datetime, timezone
import calendar
import os

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# test mode switch
TEST_MODE = True

# set the period limit when test mode is on
PER_PERIOD_LIMIT = 300 if TEST_MODE else 100000

# full list of subreddits
SUBREDDITS = [
    "depression",
    "Anxiety",
    "mentalhealth",
    "therapy",
    "therapyGPT"
]

# time periods list (filled at runtime in main)
TIME_PERIODS = []

# full lists of keywords
# type 1 
KEYWORDS_PLAIN = [
    "chatgpt",
    "claude",
    "gemini",
    "grok",
    "gpt",
    "copilot",
    "deepseek",
    "ai chatbot",

    # related to general name of LLMs
    "llm",
    "large language model",
    "artificial intelligence",
]
# type 2 
KEYWORDS_REGEX = [
    r"\bai\b",   # matches standalone "ai" only — \b is word boundary, prevents matching "ai" inside words like "email" or "said"
    r"\bai-",    # matches "ai-" prefix e.g. ai-generated, ai-powered — no right boundary so anything after "ai-" is accepted
]

# output files naming constants
POSTS_LIST_RAW        = "posts_list_raw.csv"
POSTS_LIST_FILTERED   = "posts_list_kw_filtered.csv"
POSTS_LIST_KW_HIT_LOG = "posts_list_kw_hit_log.json"

# ________________________________________________________________________________

# FUNCTION AREA

# ________________________________________________________________________________

# time periods generator
def gen_time_periods(lower_year, lower_month, upper_year, upper_month):

    year    = lower_year
    month   = lower_month
    time_periods = []

    while (year, month) <= (upper_year, upper_month):

        # last day of the month
        _, last_day = calendar.monthrange(year, month)  # monthrange returns tuple: (day of the week of the 1st, number of days in the month)


        start_of_pt = datetime(year, month, 1, tzinfo=timezone.utc)
        end_of_pt   = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        name_of_pt  = f"{year}{month:02d}"

        time_period = (start_of_pt, end_of_pt, name_of_pt)
        time_periods.append(time_period)

        year, month = (year + 1, 1) if month == 12 else (year, month + 1)

    return time_periods


# keyword filtering function
def keyword_filter(text):
    text_lower = text.lower()

    for pattern in KEYWORDS_REGEX:
        if re.search(pattern,text_lower):
            return True
    
    for plain in KEYWORDS_PLAIN:
        if plain in text_lower:
            return True
        
    return False


# words counting
def word_count(text):
    return len(text.split())
    

# check if body is valid (not deleted/removed/empty/missing)
def is_body_valid (body):
    return body not in ["[deleted]", "[removed]", "", None]


# fetch posts via arcticshift
def fetch_posts_arcticshift(subreddit, after, before, limit=100000):
    # KEY UNDERSTANDING: API only recognizes timestamp, not line.
    # The mechanism of paging is like this: the latter start point is exactly the former end point.
    # So there is a possibility that several posts happened to be posted at the same timestamp.
    # Here, set() is to deduplicate the ids.

    # API endpoint
    base_url    = "https://arctic-shift.photon-reddit.com/api/posts/search"

    # container of the collected posts
    all_posts = []
    # the record of the ids that have been seen so far
    seen_ids = set()
    # the start number of the current page, default is after
    current_after = after
    # this variable is to defense the flase signal of empty
    consecutive_empty = 0

    while len(all_posts) < limit:

        # request parameters
        params      = {
            "subreddit": subreddit,        
            "after":     current_after, # I only want the posts after this timestamp  (usually the end time of last 100 posts' collection)
            "before":    before,        # I only want the posts before this timestamp (usaully the end time of this time period) 
            "limit":     100,              
            "sort":      "asc",
        }

        # FETCH THE POSTS
        try:
            resp = requests.get(base_url, params = params, timeout = 30)
            resp.raise_for_status()
            data  = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}. Retrying in 5 seconds.")
            time.sleep(5)
            continue

        posts = data.get("data",[])
        # 01-THE FIRST CIRCUMSTANCE — "the data["data"] is empty"
        # sometimes API can briefly "jitter" and return an empty list in multiple reasons like: server load, transient timeout
        # so we should take some measure to avoid losing data
        # if the data["data"] is empty in 3 consecutive sessions, stop right there, because there is no more page to turn
        if not posts:
            consecutive_empty += 1
            if consecutive_empty >= 3:   
                break
            time.sleep(1)                
            continue
        consecutive_empty = 0            
                
        # 02-THE SECOND CIRCUMSTANCE — "the data["data"] is equal to the limit(100)"
        # if the data["data"] is equal to the limit, it means that it is highly possible that this is not the last page
        # deduplicate the posts
        new_posts = [post for post in posts if post["id"] not in seen_ids]

        # if there are still new posts, it means the last timestamp of previous session have more posts that had not been collected
        # then, firstly, the new id should be recorded in seen_id lists
        # secondly, there is no need to handle the current_after, since it will work just fine
        # thirdly, newly collected posts should be finally put into all_posts list
        if new_posts:
            for post in new_posts:
                seen_ids.add(post["id"])
            all_posts.extend(new_posts)
            current_after = max(int(post["created_utc"]) for post in posts)
        # if there are no more new posts, it means the posts in the last timestamp of previous session had been fully collected
        # then, timestamp should be move furhter to make sure there won't be any more duplicates in the next session
        else:
            current_after = max(int(post["created_utc"]) for post in posts) + 1
        
        # 03-THIRD CIRCUMSTANCE — "data["data"] is not empty but did not reach the limit"
        # this is the sign of current page is the last page, so we should discontinue at the end of the session (discontinue the while loop)
        if len(posts) < 100:
            break

        time.sleep(0.5)
   
    return all_posts[:limit]

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():

    # 01 - GENERATE THE TIME_PERIODS LIST
    global TIME_PERIODS # tell Python: this is the glodal one
    
    print("Change TEST_MODE in global constant area to True to run the testing mode, otherwise to run formal collection.")
    print("Input the time range of the collection (yyyymm, ex: 202501, 6 digits). note: if you are running the testing mode, 202501 must be included in the time range.")
    st_input = input("Covering from: ")
    et_input = input("to: ")

    try:
        lower_year  = int(st_input[:4])
        lower_month = int(st_input[4:6])
        upper_year  = int(et_input[:4])
        upper_month = int(et_input[4:6])
    except ValueError:
        print("Invalid format. Use 6 digits like 202501.")
        return

    TIME_PERIODS = gen_time_periods(lower_year, lower_month, upper_year, upper_month)
    
    # quick look: TIME_PERIODS
    print("\nInspection: time periods to run: ")
    for time_period in TIME_PERIODS:
        print(f"{time_period[2]}  {time_period[0]} ~ {time_period[1]}")

    # 02 - FETCH POSTS
    # raw posts list
    all_raw_posts      = []
    # posts filtered by keywords
    all_filtered_posts = []
    # hit rates log for each month of the communities: {"community":{"month":{...}}}
    kw_hit_log         = {}

    # settings for test mode
    subreddit_to_run    = ["Anxiety"] if TEST_MODE else SUBREDDITS
    time_periods_to_run = [time_period for time_period in TIME_PERIODS if time_period[2] == "202501"] if TEST_MODE else TIME_PERIODS

    # MAIN STRUCTURE — DOUBLE LOOPS (for subreddit(for time period))
    for subreddit in subreddit_to_run:
        # to record the hit rates
        kw_hit_log[subreddit] = {}

        # fetch posts
        for start_dt, end_dt, period_name in time_periods_to_run:

            kw_hit_log[subreddit][period_name] = {}

            # variables for hit rates calculation
            hit_count = 0
            raw_count = 0

            # call for the function for fetching the posts
            after_ts  = int(start_dt.timestamp())
            before_ts = int(end_dt.timestamp())
            posts     = fetch_posts_arcticshift(subreddit, after_ts, before_ts, limit=PER_PERIOD_LIMIT)

            # handling each post
            for post in posts:
                title    = post.get("title", "")
                selftext = post.get("selftext", "")
                full_text = f"{title} {selftext}"

                row = {
                    "post_id":     post["id"],
                    "subreddit":   subreddit,
                    "period":      period_name,
                    "title":       title,
                    "body":        selftext,
                    "full_text":   full_text,
                    "created_utc": post.get("created_utc"),
                    "score":       post.get("score"),
                    "url":         "https://reddit.com" + post.get("permalink", ""),
                    "word_count":  word_count(full_text),
                    "body_valid":  is_body_valid(selftext),
                }

                all_raw_posts.append(row)
                raw_count += 1

                if keyword_filter(full_text):
                    all_filtered_posts.append(row)
                    hit_count += 1
                
            # hit rates calculation
            hit_rate = hit_count / raw_count if raw_count > 0 else 0
            # save the result of hit rates
            kw_hit_log[subreddit][period_name] = {
                "raw_count":        raw_count,
                "keyword_hits":     hit_count,
                "keyword_hit_rate": round(hit_rate, 4),
            }

            print(f"{subreddit} {period_name}: {raw_count} raw, {hit_count} hits")


# 03 - SAVE TO FILES
    script_dir = os.path.dirname(os.path.abspath(__file__))   
    data_dir   = os.path.join(script_dir, "..", "data")       
    os.makedirs(data_dir, exist_ok=True)

    df_raw = pd.DataFrame(all_raw_posts)
    df_raw.to_csv(os.path.join(data_dir, POSTS_LIST_RAW), index=False, encoding="utf-8-sig")

    df_filtered = pd.DataFrame(all_filtered_posts)
    df_filtered.to_csv(os.path.join(data_dir, POSTS_LIST_FILTERED), index=False, encoding="utf-8-sig")

    with open(os.path.join(data_dir, POSTS_LIST_KW_HIT_LOG), "w", encoding="utf-8") as f:
        json.dump(kw_hit_log, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Raw: {len(all_raw_posts)}, Filtered: {len(all_filtered_posts)}")    

if __name__ == "__main__":
    main()