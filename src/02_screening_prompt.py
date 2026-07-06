"""
================================================================================
SCRIPT: 02_screening_prompt.py
PURPOSE: Use the LLM to keep only relevant posts, and flag risky ones (step 2)
================================================================================

WHAT THIS SCRIPT DOES (3 jobs per post):
    1. Decide if the post is about a real, personal, emotional talk with an AI
    2. Sort the post into 3 risk levels (only Level 3 is dropped on its own)
    3. Flag psychosis signs (delusions/hallucinations) — dropped for method reasons

FLOW:
─────────────────────────────────────
TASK 1: RELEVANCE SCREENING
─────────────────────────────────────
'''
My original question: Should inclusion and exclusion criteria be presented in parallel, or should exclusion operate within the already-included corpus?
In the thesis, the logic should be presented sequentially — inclusion first, exclusion second, because this reflects the actual structure of the research design. 
However, the screening prompt itself does not operate in multiple stages. For a single-pass binary classification task, presenting inclusion and exclusion side by side is more appropriate.
'''
The three conditions form a sequential filtering chain:

    Personal use (not general discussion) → emotional/mental health content (not technical discussion) → author's subjective response (not purely factual narration)

─────────────────────────────────────
TASK 2: RISK LEVEL CLASSIFICATION
─────────────────────────────────────

The underlying logic: behavioral proximity to harm

LEVEL 1. EMOTIONAL DISTRESS WITHOUT IDEATION
         Distress is contextual, not directional toward harm.
                |
                | passive/existential expression → active, explicit statement
                ↓
LEVEL 2. IDEATION WITHOUT BEHAVIORAL INTENT
         The person wants to die or self-harm, but has no plan and no ongoing behavior.
                |
                | thought → specific behavior that is happening or imminent
                ↓
LEVEL 3. BEHAVIORAL INTENT OR ONGOING SELF-HARM
         Concrete plan, timeline, ongoing act, or farewell statement.


─────────────────────────────────────
TASK 3: PSYCHOSIS FLAG (1.1%)
─────────────────────────────────────

The underlying logic: access to shared social reality

Exclusion is methodological, not ethical. Discourse analysis requires the speaker to operate within a shared symbolic system. 
Psychotic content breaks this precondition — the concessive-pivot construction cannot be analyzed as a discursive strategy if the speaker's reality testing has failed.

Flag = true: the speaker attributes real-agent properties to AI as fact, not metaphor (delusions, hallucinations, incoherent discourse structure).

Flag = false: affective or rhetorical attribution where the speaker demonstrably knows AI is AI. This is the phenomenon under study.

Boundary: delusion vs. anthropomorphization turns on whether the belief is held counterfactually ("the AI is actually alive") or affectively ("it feels like it understands me"). Hedges and uncertainty markers
distinguish the two.

INPUT FILE:
    posts_list_kw_filtered.csv   Posts that passed the keyword filter (step 1)

OUTPUT FILE:
    posts_list_screened.csv      Posts with relevance, risk level, and flags

NEXT STEP: agreement_check.py (check human vs. LLM agreement)

================================================================================

"""


# ________________________________________________________________________________

# IMPORT AREA

# ________________________________________________________________________________

import json
import time

import requests
import pandas as pd
import os

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

# input files naming constants
POSTS_LIST_FILTERED = "posts_list_kw_filtered.csv"

# output files naming constants
POSTS_LIST_SCREENED = "posts_list_screened.csv"

# prompt for screening the posts
SYSTEM_PROMPT = """You are a research assistant helping screen Reddit posts for an academic study.

The study examines how users talk about using AI tools (such as ChatGPT, Claude, Gemini, etc.) for emotional support or mental health-related conversations.

You have THREE tasks for each post:

─────────────────────────────────────
TASK 1: RELEVANCE SCREENING
─────────────────────────────────────

Decide whether the post is RELEVANT or NOT RELEVANT.

RELEVANT — ALL THREE conditions must be met:
1. The author describes a personal experience of using a specific AI tool (e.g., ChatGPT, Claude, Gemini, Grok, Copilot, or similar LLMs)
2. The interaction had emotional or mental health content (e.g., discussing feelings, seeking comfort, processing trauma, venting, asking for advice about personal problems)
3. The author reflects on, evaluates, or expresses feelings about that experience

NOT RELEVANT — if any of these apply:
- AI is mentioned only in passing, without describing an actual personal interaction
- The post discusses AI tools in general (news, capabilities, ethics, industry) without personal use
- The post discusses mental health without any mention of AI
- The post asks hypothetically about AI without describing actual use
- The author is a therapist or professional discussing AI from a clinical perspective (not personal use)

─────────────────────────────────────
TASK 2: RISK LEVEL CLASSIFICATION
─────────────────────────────────────

Classify the post into one of three risk levels. Be VERY CONSERVATIVE in escalating levels. Default to Level 1 unless there is clear, explicit evidence for a higher level.

LEVEL 1 — No acute risk (DEFAULT for most posts)
Assign this level to:
- General expressions of sadness, hopelessness, loneliness, or despair
- Passive existential questioning ("what's the point", "I don't know why I'm still here")
- Past tense references to resolved crises (desperate, but without actual self-harm activities)
- Vague or indirect references to not wanting to continue
- Expressions like "I want to get better" even alongside deep pain
- Any post where the primary content is about AI use and emotional distress is contextual

LEVEL 2 — Suicidal ideation or self-harm references without behavioral intent
Assign this level ONLY when the post contains:
- Explicit, direct statements of wanting to die ("I want to kill myself") WITHOUT any plan or timeline
- Descriptions of past self-harm acts (cutting, overdose, etc.) presented as history, not current behavior
- Active suicidal thoughts expressed as intrusive/unwanted ("I keep thinking about ending it but I don't want to")
DO NOT assign Level 2 for passive hopelessness or existential questioning — those are Level 1.

LEVEL 3 — Active behavioral intent or ongoing self-harm (WILL BE EXCLUDED from study)
Assign this level ONLY when the post contains:
- A specific plan for suicide with method, timing, or preparation ("I bought pills and plan to take them tonight")
- Description of self-harm that is currently happening or just happened ("I just cut myself")
- Explicit farewell statements indicating imminent action ("this is my last post")
DO NOT assign Level 3 for ideation alone — that is Level 2.
DO NOT assign Level 3 for past self-harm — that is Level 2.
DO NOT make the judgment based on content warnings about sensitive topics, such as “TW: suicide” used as a warning label. The judgment should be based solely on the content in the body of the post.

─────────────────────────────────────
TASK 3: PSYCHOSIS FLAG
─────────────────────────────────────

Flag whether the post shows clear signs of active psychotic symptoms. This is a METHODOLOGICAL exclusion — the study analyzes how users discursively construct autonomous relationships with AI, which requires the discourse to operate within shared social reality.

Flag as PSYCHOSIS = true ONLY when the post contains:
- Delusions: fixed false beliefs stated as fact (e.g., "the AI is actually alive and sending me secret messages", "ChatGPT is controlled by the government to monitor me")
- Hallucinations: perceptual experiences described as real (e.g., "I can hear the AI talking to me when the app is closed")
- Severe disorganized thinking that makes the post's discourse structure incoherent

DO NOT flag as psychosis:
- Emotional attachment to AI ("I feel like it understands me") — this is NOT psychosis, this is exactly what the study wants to analyze
- Anthropomorphization ("it felt like talking to a real person") — this is NOT psychosis
- Loneliness-driven statements ("ChatGPT is my only friend") — this is NOT psychosis
- Metaphorical language about AI ("it's like it has a soul") — this is NOT psychosis

─────────────────────────────────────

Respond ONLY with a JSON object in this exact format:
{
  "relevant": true or false,
  "confidence": 0.0 to 1.0,
  "reason": "one sentence explaining relevance decision",
  "risk_level": 1 or 2 or 3,
  "risk_reason": "one sentence explaining risk classification",
  "psychosis": true or false,
  "psychosis_reason": "one sentence if true, null if false"
}"""

# paste api key here
API_KEY = ""

# ________________________________________________________________________________

# FUNCTION AREA

# ________________________________________________________________________________

# send one post to the LLM and return its screening result as a dict
def screen_post(title, body):
    post = f"TITLE: {title}\n\nBODY: {body}"

    # to avoid waste tokens on extraordinarily long post, which may also has risk of being refused by API due to exceeding the model's input length limit.
    if len(post) > 3000:
        post = post[:3000] + "...[truncated]"

    payload = {
        "model" :      "claude-sonnet-4-20250514",
        "max_tokens" : 400,
        "system" :     SYSTEM_PROMPT,
        "messages" :   [
            {"role" : "user", "content" : post}
        ]
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json=payload,
            timeout=60
        )
        resp.raise_for_status()

        # resp.json() parses the API response envelope; ["content"][0]["text"]
        # pulls out the string the model wrote (may be wrapped in markdown).
        text = resp.json()["content"][0]["text"]
        # strip markdown code fences so the string is clean JSON before parsing.
        text = text.replace("```json", "").replace("```", "").strip()

        # Now parse the model's JSON string into a Python dict.
        return json.loads(text)
    except Exception as e:
        return {
                "relevant":         None,
                "confidence":       0.0,
                "reason":           f"error: {e}",
                "risk_level":       None,
                "risk_reason":      f"error: {e}",
                "psychosis":        None,
                "psychosis_reason": f"error: {e}"
        }

# ________________________________________________________________________________

# MAIN WORKFLOW AREA

# ________________________________________________________________________________

def main():
    # container for the returned dict of each posts 
    results        = []
    # the number of posts that have been screened
    screened_count = 0

    # read the data from "posts_list_kw_filtered.csv"
    df = pd.read_csv(POSTS_LIST_FILTERED, encoding="utf-8-sig")
    print(f"{len(df)} posts in 'posts_list_kw_filtered.csv' were read.")

    # screening
    for i, row in df.iterrows():
        screened_post = screen_post(str(row.get("title", "")), str(row.get("body", ""))) # covered by str in case None becomes float
        results.append(screened_post)
        time.sleep(0.3)
        screened_count += 1
        if screened_count % 50 == 0:
            print(f"{screened_count}/{len(df)} posts have been screened.")
    
    # create new columns for new data
    df["llm_relevant"]         = [r.get("relevant") for r in results]
    df["llm_confidence"]       = [r.get("confidence") for r in results]
    df["llm_reason"]           = [r.get("reason") for r in results]
    df["llm_risk_level"]       = [r.get("risk_level") for r in results]
    df["llm_risk_reason"]      = [r.get("risk_reason") for r in results]
    df["llm_psychosis"]        = [r.get("psychosis") for r in results]
    df["llm_psychosis_reason"] = [r.get("psychosis_reason") for r in results]

    # save files    
    script_dir = os.path.dirname(os.path.abspath(__file__))   
    data_dir   = os.path.join(script_dir, "..", "data")       
    os.makedirs(data_dir, exist_ok=True)

    df.to_csv(os.path.join(data_dir, POSTS_LIST_SCREENED), index=False, encoding="utf-8-sig")
    
    print("'posts_list_screened.csv' has been saved.")

    # statistical summary
    n_total = len(df)

    relevant   = df[df["llm_relevant"] == True]
    n_relevant = len(relevant)
    
    psychosis   = relevant[relevant["llm_psychosis"] == True]
    n_psychosis = len(psychosis)


    level_1    = relevant[relevant["llm_risk_level"] == 1]
    n_level_1  = len(level_1)

    level_2    = relevant[relevant["llm_risk_level"] == 2]
    n_level_2  = len(level_2)

    level_3    = relevant[relevant["llm_risk_level"] == 3]
    n_level_3  = len(level_3)

    level_3_and_psychosis   = relevant[(relevant["llm_risk_level"] == 3) & (relevant["llm_psychosis"] == True)]
    n_level_3_and_psychosis = len(level_3_and_psychosis)

    n_excluded = n_level_3 + n_psychosis - n_level_3_and_psychosis
    n_usable   = n_relevant - n_excluded

    # report
    print(f"Total posts:    {n_total}")
    print(f"Relevant:       {n_relevant} ({n_relevant/n_total:.1%})")
    print(f"  Level 1:      {n_level_1}  -> kept")
    print(f"  Level 2:      {n_level_2}  -> kept")
    print(f"  Level 3:      {n_level_3}  -> excluded")
    print(f"  Psychosis:    {n_psychosis}  -> excluded")
    print(f"Excluded (unique): {n_excluded}")
    print(f"Usable corpus:     {n_usable}")


if __name__ == "__main__":
    main()









