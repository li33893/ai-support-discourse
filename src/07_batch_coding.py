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
          llm_confidence, llm_reasoning
        of which llm_excluded=False -> 1,994 posts go to analysis

NEXT STEP:
    08_spot_check_sample.py

================================================================================

"""