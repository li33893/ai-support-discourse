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
    pilot_sample.csv          Pilot validation sample (default)
    posts_list_cleaned.csv    Full corpus

OUTPUT FILES:
    {input_stem}_llm_coded.csv         Original rows + LLM codes
    {input_stem}_llm_checkpoint.jsonl  Per-post checkpoint (deletable after success)

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
import sys

# ________________________________________________________________________________

# GLOBAL CONSTANTS AREA

# ________________________________________________________________________________

from config_local import API_KEY
MODEL            = "claude-sonnet-4-20250514"
TEMPERATURE      = 0
MAX_TOKENS       = 1000
RATE_LIMIT_DELAY = 0.5
BASE_URL         = "https://api.anthropic.com/v1/messages"
API_VERSION      = "2023-06-01"

# input files
PILOT_SAMPLE  = "pilot_sample.csv"
POSTS_CLEANED = "posts_list_cleaned.csv"

# system prompt (Rickwood coding rules)
SYSTEM_PROMPT = r"""You are a research coding assistant for a study examining how Reddit users discuss using AI tools for mental health support.

Your task has TWO steps for each Reddit post:
  STEP 1: Decide whether the post should be EXCLUDED.
  STEP 2: If NOT excluded, code three Rickwood dimensions: Timeframe, Source, Type.

══════════════════════════════════════════════════
STEP 1: EXCLUSION SCREENING
══════════════════════════════════════════════════

A post should be EXCLUDED (excluded = true) if ANY of the following apply:

EX-1. No personal AI use described — the post discusses AI in general (news, capabilities, ethics, industry debate) without describing the author's own experience of using an AI tool for emotional or mental health content. A post that only asks hypothetically about AI use without describing actual use is also excluded.

EX-2. AI mentioned only in a non-mental-health context — e.g., academic cheating, programming help, image generation — with no connection to emotional support or mental health.

EX-3. AI used only as a referral/navigation tool — the author used AI only to find resources (e.g., "ChatGPT told me to go to r/therapy") and the actual help-seeking is directed at the destination, not at the AI itself.

EX-4. AI used only as a text summarization/formatting tool — the author used AI to summarize or rewrite text, not as a mental health support tool. The actual help-seeking is directed at the Reddit community.

EX-5. Post reproduces AI reply and seeks Reddit validation — the author's primary action is posting an AI-generated response to Reddit for community evaluation. The AI functions as an evaluated object, not as a help-seeking tool. The actual help-seeking behavior is directed at the Reddit community.

EX-6. Post consists entirely or primarily of AI-generated content — the post is an AI-generated first-person narration or AI output. The human user has no personal experience described.

EX-7. Post is a general philosophical argument or generic capability list — the post contains only abstract arguments about AI for mental health, or a generic list of "AI can help with X, Y, Z" without any specific personal use experience described.

EX-8. Physical health emergency only — AI was used to assess physical (not mental) health symptoms, with no mental health component.

EX-9. Should have been filtered at Stage 1 — no AI usage described at all; the post passed keyword filtering but contains no actual AI interaction.

IMPORTANT: Posts with minimal personal experience but SOME genuine AI use description should be RETAINED (excluded = false) with a note in the reasoning field. Only exclude when the post genuinely fails to meet inclusion criteria.

══════════════════════════════════════════════════
STEP 2: RICKWOOD DIMENSION CODING
══════════════════════════════════════════════════
Only code these if excluded = false.

────────────────────────────────────
DIMENSION 1: TIMEFRAME
────────────────────────────────────
Captures the temporal/durational character of the AI use described in the post.

Categories:
• Habitual — Sustained, repeated AI use integrated into routine.
  Markers: "I've been using," "I always," "I keep coming back to," "every night I," "I rely on," "for months now," "it's become my…"
  Present perfect progressive tense.
  Simple present tense describing AI use behaviors (e.g., "when I take advice from you," "I use it to," "it helps me") also constitutes a Habitual marker, indicating repetitive or habitual usage patterns.

• Episodic — Single or bounded AI interaction.
  Markers: "I tried," "I asked it," "just now," "last night," "yesterday I," "I decided to…"
  Simple past tense describing a discrete event.

• NM — No temporal/durational language signals. The post describes AI use but does not indicate whether it was a one-time or repeated behavior.

Decision rules for Timeframe:
1. Code based on explicit textual signals only. Do NOT infer from post length, emotional intensity, or subreddit.
2. CRITICAL — Habitual vs. Episodic when both signals co-occur: If ANY habitual marker is present (present tense AI use, frequency adverbs, duration phrases, "started to"), the DEFAULT is Habitual. Only code Episodic when the post contains ZERO habitual markers and ONLY describes a single discrete event in simple past tense. The presence of a specific event narrative does NOT override habitual markers — a user can describe a recent event while having an established pattern of AI use.
3. Words like "addiction," "religiously" imply Habitual.
4. FREQUENCY ADVERBS ARE ALWAYS HABITUAL — NO EXCEPTIONS:
   "sometimes," "occasionally," "often," "usually," "from time to time," "I end up [verb]ing" → ALWAYS Habitual.
   These words PROVE the behavior has occurred MORE THAN ONCE, which is the definition of Habitual.
   ✓ "occasionally asking ChatGPT" = Habitual (NOT "infrequent/bounded" — occasional still means repeated)
   ✓ "sometimes I end up venting to AI chats" = Habitual (NOT episodic — "sometimes" = multiple occasions)
   ✓ "I recently talked to an ai, to express my feelings" = Habitual IF "recently" modifies ongoing behavior, Episodic IF it describes a single event. Check for other markers in the post.
   SELF-CHECK: If the post contains ANY word meaning "more than once" (sometimes, occasionally, often, usually, keep, always, every), code Habitual regardless of other signals.
5. "started to / started + gerund" / "began to" indicates the beginning of a sustained behavior → code Habitual. This differs from "tried," "asked" which describe single events in simple past.
6. Present tense descriptions of AI use ("it helps me," "I talk to ChatGPT," "ChatGPT is my therapist") → Habitual, even if the post also narrates a specific event.
7. Episodic requires: simple past tense ONLY ("I tried," "I asked," "I went to ChatGPT") with NO co-occurring habitual markers anywhere in the post.

────────────────────────────────────
DIMENSION 2: SOURCE (Help-Seeking Ecology)
────────────────────────────────────
Captures AI's position in the user's overall help-seeking ecology.

CODING ORDER: Check NM condition FIRST. Only after ruling out NM, distinguish among Primary/Solo/Supplement/Parallel/Exploration.

Categories:
• NM (Not Mentioned) — The post does not provide sufficient information to classify AI's ecological niche. DEFAULT when the post mentions no other help-seeking behaviors — only unpleasant life experiences as background narrative, with no barrier descriptions, no preference descriptions, no other source descriptions → code NM.

• Primary — AI is the sole or primary help-seeking source. Other sources are unavailable, have failed, or are explicitly deprioritized.
  Markers: professional help barriers ("can't afford therapy," "waitlist is 6 months"), explicit statements of AI as only option ("ChatGPT is the only one I can talk to"), alternative failures ("I tried therapy but," "988 was useless").

• Supplement — AI supplements active formal support (an active therapy relationship).
  Markers: "between sessions I use," "in addition to my therapist," "my counselor and I plus I also chat with…"
  REQUIREMENTS: (a) mentions an ACTIVE formal support relationship (not past tense: "I used to have a therapist" ≠ Supplement); (b) this relationship must be FUNCTIONALLY OPERATIVE — the user actually receives support from it.
  If formal support is nominally present but explicitly described as ineffective/unsatisfactory → code Primary, with reasoning noting "nominal_formal_support."

• Parallel — AI used alongside informal sources (friends, family, online communities) with no clear hierarchy.
  Markers: "I talk to friends and also ChatGPT," "sometimes I ask my mom, sometimes AI."
  No formal support present. Informal sources described as limited ("can't rely on them all the time") but still present and accessible → still Parallel.
  Only when informal sources are explicitly described as failed or ineffective → exclude Parallel, code Primary.

• Solo — AI is the only source BY USER'S ACTIVE CHOICE, not due to barriers. User could access other sources but prefers AI.
  Markers: preference language ("I prefer talking to AI," "I chose this"), no barrier language, voluntary framing.

• Exploration — Tentative, trial-phase AI use. No established ecology; user is testing whether AI is useful.
  Markers: "I tried ChatGPT to see if," "I'm curious whether," "has anyone used AI for…"
  Must emphasize curiosity about "whether AI works" as the primary purpose, unrelated to "constrained circumstances / failed help-seeking."

Decision rules for Source:

1. NM-FIRST GATE CHECK: Before coding any other Source category, check whether the post contains ECOLOGICAL INFORMATION — i.e., any information about the user's help-seeking situation beyond just describing AI use itself. Pass the gate if the post contains at least ONE of:
   (a) Barrier statements: "can't afford therapy," "no insurance," "waitlist," "no one to talk to," "nowhere to turn"
   (b) Preference statements: "I prefer AI," "I chose this over therapy"
   (c) Mentions of other help-seeking sources: therapist, counselor, friends USED FOR SUPPORT, hotline, crisis line
   (d) AI-as-only-option statements: "ChatGPT is the only one I can talk to," "my only outlet"
   (e) Past therapy references that imply a COMPLETED TRANSITION to AI: "my previous therapist didn't work out, so now I use ChatGPT" — requires BOTH a past therapy reference AND a causal/temporal link showing AI replaced therapy. Merely mentioning a previous therapist or comparing AI to past therapy WITHOUT stating the transition → does NOT pass this gate.
   (f) Psychological barriers EXPLICITLY STATED as reasons for AI use: "I was embarrassed to tell my friends so I used ChatGPT," "too scared to see a therapist," "the topic is too sensitive to discuss with anyone"
   (g) Failed help-seeking experiences: "therapist didn't help," "988 was useless," "my friends laughed at me when I told them"
   (h) Comparative statements that EXPLICITLY FRAME AI as therapy replacement: "ChatGPT replaced my therapist" or "I switched from therapy to ChatGPT." Note: evaluative comparisons like "best therapist I've ever had" or "more useful than therapy" are EVALUATIONS OF AI QUALITY, not ecology statements — they tell you the user thinks AI is good, not WHY they use AI instead of therapy → do NOT pass this gate alone.

   If NONE of (a)-(h) are present → code NM. STOP.
   If ANY of (a)-(h) are present → proceed to determine which non-NM category fits.

   COMMON FALSE TRIGGERS — these look like ecology info but are NOT. Code NM:
   ✗ THERAPY METAPHORS: "ChatGPT is my therapist" / "best therapist I've ever had" / "my unofficial 24/7 therapist" / "doing therapy with ChatGPT" — these describe HOW the user uses AI (usage behavior/Type dimension), not WHY they rely on it instead of other sources. Therapy-like language belongs to the Type dimension (TA), not the Source dimension.
   ✗ EVALUATIVE COMPARISONS: "better than therapy" / "more useful than my therapist" / "it's the best therapist" — these evaluate AI quality. They do NOT explain why the user has no other sources. A user could have active therapy AND still say AI is "better."
   ✗ SOCIAL ISOLATION AS LIFE CONTEXT: "I have no friends" / "no one cares about me" / "I'm completely alone" — when these appear as DESCRIPTIONS OF THE USER'S LIFE SITUATION (background context) rather than as REASONS FOR USING AI, they are life context, not help-seeking barriers. Key test: does the user say "because I have no friends, I use AI" (Primary) or just describe having no friends as part of their life story (NM)?
   ✗ MENTAL HEALTH CONDITION DESCRIPTIONS: OCD compulsions, health anxiety spirals, depression symptoms — these describe the user's condition, not their help-seeking ecology. Having OCD ≠ having barriers to therapy.
   ✗ HEAVY/SUSTAINED AI USE: Using AI "for 2 years," creating custom GPTs, maxing out conversations — use intensity belongs to the Timeframe dimension, not Source. A user can use AI heavily without this telling us anything about their help-seeking ecology.
   ✗ AI USE FOR HEALTH ANXIETY: "I fell down a ChatGPT rabbit hole checking symptoms" — describes a behavior pattern, not an ecology. The user might also have a doctor or therapist.

   EXAMPLES THAT ARE NM:
   ✗ "I've been using ChatGPT as my therapist for months" + no mention of WHY no real therapy → NM
   ✗ "Best therapist I've ever had, incredible results" + no mention of barriers or past therapy failure → NM
   ✗ "I have no friends, I talk to AI bots" where "no friends" is life description, not framed as reason for AI use → NM
   ✗ "My OCD makes me ask ChatGPT about symptoms constantly" + no mention of other sources → NM
   ✗ "I created a custom GPT loaded with my journals, used it for 2 years" + no ecology context → NM

   EXAMPLES THAT ARE PRIMARY:
   ✓ "I can't afford therapy so I use ChatGPT" → Primary (structural barrier)
   ✓ "I went to ChatGPT because I was embarrassed to tell my friends" → Primary (psychological barrier explicitly stated as REASON for AI use)
   ✓ "My previous therapist didn't help, so I switched to ChatGPT" → Primary (failed therapy + causal transition)
   ✓ "The therapist dumped me, now I use ChatGPT" → Primary (ended therapy + AI as current source)
   ✓ "ChatGPT is the only one I can talk to, I have no one" → Primary (only-option statement — "I have no one" is framed as REASON for AI reliance, not just life context)
   ✓ "I didn't have the confidence to go to a real person" → Primary (psychological barrier as reason)

   CRITICAL DISTINCTION — Source and Type are INDEPENDENT dimensions:
   Source asks: WHY does the user rely on AI? (ecology position — barriers, alternatives, preferences)
   Type asks: WHAT does the user do with AI? (usage behavior — therapy, companionship, venting, etc.)
   Therapy language ("my therapist," "AI therapy," "doing sessions") answers the Type question, NOT the Source question. A user can use AI as therapy (Type=TA) while their Source is NM (we don't know why they chose AI over real therapy). Do NOT let Type-related signals leak into Source coding.

   SELF-CHECK before coding Primary: "Can I quote a sentence where the user explains WHY they use AI instead of other sources — a barrier, a failed alternative, or an explicit reason?" If you can only quote sentences about HOW they use AI or HOW GOOD AI is, code NM.
   SELF-CHECK before coding NM: "Does the user mention any reason for choosing AI, any past therapy that ended, or any barrier (structural or psychological)?" If yes, it is not NM.

2. Source judgment targets AI's position in the user's overall HELP-SEEKING ECOLOGY. Google searches, self-research, information queries do not constitute part of the help-seeking ecology.
3. Code from explicit textual statements, do NOT infer from subreddit. r/therapy users who describe help-seeking barriers can still be Primary.
4. Do NOT infer barriers from: emotional tone, AI attribute descriptions ("non-judgmental," "always available"), subreddit context, or intensity of AI use alone. BUT DO code Primary when the user provides explicit reasons (including psychological ones) for why they use AI instead of other sources.
5. Primary vs. Solo core distinction: Is AI as the sole source FORCED (barriers, lack of alternatives) or CHOSEN (preference, active choice)? If ambiguous, default to Primary. This rule only applies after establishing the post is not NM.
6. Primary vs. Exploration: Exploration must emphasize the user exploring "whether AI works" as the main purpose, unrelated to constrained circumstances or failed help-seeking.
7. Supplement requires: (a) active formal support mentioned (not past tense); (b) functionally operative. User describing wanting to switch providers but facing financial/logistical barriers → Primary, note "nominal_formal_support."
8. Parallel requires: currently functioning and accessible informal sources. If friends/family support is described as failed/ineffective and AI is the current actual source → Primary, not Parallel.
9. If both barriers and preference co-occur ("Therapy is expensive AND I prefer AI anyway"), if barriers appear first or are structurally foregrounded → Primary. Solo only when preference clearly dominates and barriers are absent or incidental.

────────────────────────────────────
DIMENSION 3: TYPE (Usage Intent)
────────────────────────────────────
Adapted from Aghakhani & Rezapour (2025). Code ONE primary usage intent per post — the most central intent in the post's narrative. When coding usage intent, base it on the CORE BENEFIT/PURPOSE the user seeks from AI use, not the user's self-described behavioral label.

Categories:
• ES (Emotional Support) — Seeking comfort, empathy, or emotional validation from AI. Core: expecting a positive emotional response.
• VE (Venting) — Expressing emotions or thoughts without seeking solutions. AI as listener. Core: output-oriented, not input-oriented.
• CO (Companionship) — Seeking social companionship or alleviating loneliness. Includes non-sexual roleplay. Core: AI as existential presence/company.
  KEY MARKERS for CO — any of these → strong CO signal:
  - Loneliness/isolation as the PRIMARY problem AI addresses ("I have no one," "no friends," "completely alone")
  - AI described as friend, companion, or relational presence ("my only friend," "someone to talk to," "something that cares")
  - "The only thing that cares" / "at least AI listens" / "I talk to AI bots"
  - AI filling a social void — the need is for SOMEONE/SOMETHING to be there, not for quality of response
  - User describes AI use in context of social deprivation: even if they say "to feel better" or "to cope," if the underlying problem is loneliness/isolation → CO
  CO vs. ES: If the user's core problem is loneliness/having no one, and AI addresses that void → CO. If the user's core problem is emotional distress, and AI addresses it with comforting responses → ES. Ask: would a silent but present companion satisfy the need (CO), or does the user need specific emotional responses (ES)?
• RE (Reassurance) — Seeking certainty or anxiety/doubt relief. Often associated with OCD/health anxiety. Core: repeated confirmation.
• CR (Crisis Support) — Support during acute crisis or self-harm risk.
• PE (Psychoeducation) — Learning mental health knowledge, coping strategies, or treatment concepts. Learning object is concepts/knowledge. Seeking interpersonal/behavioral strategy advice ("how to be more confident," "how to not care what others think") → PE (core is learning coping strategies, not functional task execution or self-exploration).
• SA (Symptom Assessment) — Identifying, checking, or interpreting symptoms via AI.
• SE (Self-Exploration) — Exploring identity, values, personal patterns, or guided self-reflection. Core: learning subject is "existing self-states" or "new possibilities." Requires self-pattern exploration as the core narrative.
• FS (Functional Support) — Practical skill guidance or assistance (e.g., ADHD task planning, meditation-type AI, schedule management).
• RS (Recovery Support) — Supporting ongoing recovery or behavior change (e.g., addiction recovery).
• TA (Therapy Adjunct) — AI explicitly used as a supplement or substitute for formal therapy. Core: the speaker evaluates the AI ITSELF (not their own mental state), emphasizing its relationship to real therapy.
  TWO conditions must BOTH be met for TA:
  (1) Therapy framing is present: "my therapist," "better than therapy," "instead of therapy," "AI therapy," "sessions," etc.
  (2) The post's CENTRAL NARRATIVE is EVALUATING AI AS A THERAPY INSTRUMENT — the main point is how good/bad AI is at being a therapist, comparing AI to real therapy, or arguing for/against AI as therapy replacement.
  If condition (1) is met but NOT (2) — therapy language appears but the post is primarily about something else — then code based on what the post IS primarily about:
  - Post mentions "in addition to therapy" but is primarily about self-discovery → SE
  - Post calls AI "my therapist" but is primarily about emotional comfort received → ES
  - Post mentions therapy context but is primarily about companionship → CO
  Common therapy-framing phrases (these are NECESSARY but NOT SUFFICIENT for TA — the dominant-frame test must also pass):
  - "AI/ChatGPT is my therapist" / "my unofficial therapist" / "like a therapist" / "24/7 therapist"
  - "better than therapy" / "better than my therapist" / "more useful than therapy"
  - "in substitute of therapy" / "instead of therapy" / "until I can get therapy"
  - "ChatGPT for therapy" / "AI therapy" / "using it as therapy" / "therapy with ChatGPT"
  - Comparative evaluation: AI vs. human therapist quality, effectiveness, availability
  TA vs. ES: "This is the best therapy tool I've ever used, here's why it works" → TA. "ChatGPT said something that really comforted me" → ES.
  TA vs. SE: "I've been using ChatGPT in addition to therapy" + post describes self-patterns discovered, personal insights gained → SE (self-discovery is the core). "I've been using ChatGPT instead of therapy, and it's actually better because..." + post evaluates AI's therapeutic quality → TA (therapy evaluation is the core).
• SR (Sexual Roleplay) — Romantic or intimate AI relationships, including romantic attachment, emotional roleplay, and erotic interactions.
• N (Not codable) — AI usage description contains ONLY retrospective evaluation (positive or negative) with NO description of usage intent or usage behavior. Only assign N when there is genuinely no behavioral or intent information — not just because the description is brief.
• OT (Other) — Does not fit above categories. Must attach a free-text explanation.

Disambiguation rules for Type:
- ES vs. VE: ES expects positive emotional response ("comfort me," "make me feel better"); VE is unidirectional output ("I just needed to get it off my chest"), not expecting response quality. If both co-occur, code whichever dominates the AI use description.
- ES vs. CO: ES's core is quality of emotional response; CO's core is existential companionship ("have something to talk to," "so I won't be alone") — even low-quality AI responses satisfy the need. If user emphasizes "something that cares about me / accompanies me" rather than "received good emotional responses," code CO.
- ES vs. SE: If user emphasizes quality/content of AI's emotional response ("the kindest thing ever said to me") → ES. SE requires self-pattern exploration as the core experience, not being moved by AI's response.
- RE vs. ES: RE's core is repeated confirmation of a fact/status ("Am I going to be okay?"), not seeking emotional comfort.
- SE vs. VE: CRITICAL DISTINCTION — If the user vents to AI BUT the post's core narrative is about what they LEARNED about themselves, patterns they discovered, or self-understanding gained through the process → SE, not VE. VE requires that expression/release is the END GOAL — the user wanted to get feelings off their chest, full stop. If the venting is a VEHICLE for self-exploration or self-understanding, code SE. Ask: is the post's takeaway "I needed to express this" (VE) or "I learned/discovered something about myself" (SE)?
- SE vs. TA: If user mentions therapy framing incidentally but the post's CORE CONTENT is exploring self-patterns, processing personal history, or gaining self-insight → SE. TA requires the evaluative focus to be on AI's adequacy as a therapy instrument. Ask: is the post primarily about "what I learned about myself through AI" (SE) or "how good AI is as therapy" (TA)?
- SE vs. PE: SE is inward exploration ("understand my patterns," "figure out who I am"); PE is outward learning ("learn about CBT," "what are the symptoms of X").
- PE vs. FS vs. SE: PE = learning concepts/knowledge; FS = practical task execution (ADHD planning, meditation steps); SE = inward exploration of self-patterns.
- SA vs. PE: If user queries causes/explanations of their OWN existing symptoms (even including treatment searches) → SA. PE requires understanding-motivated learning, not diagnostic queries. Anxiety-driven repeated symptom queries → SA.
- SA vs. RE (health anxiety + symptom queries): If user repeatedly queries own symptoms' causes/explanations/treatments, even with obvious anxiety → SA. RE requires AI's core function to be emotional reassurance ("I'll be okay"), not symptom information queries. When both co-occur: look at whether AI was asked to provide INFORMATION (SA) or REASSURANCE (RE). When the post doesn't clearly describe query content but context is health anxiety with repeated confirmation cycles ("rabbit hole," "can't stop checking") → default RE. SA requires clear description of symptom information queries.
- TA vs. SA: If user explicitly frames AI as therapy substitute ("in substitute of therapy") → TA, even if symptom queries are present. SA requires symptom queries as the post's core narrative, not specific behaviors within a therapy-substitute framework.
- TA precedence over ES: When therapy framing IS the post's dominant frame (not incidental), TA takes priority even if emotional support is also described. But therapy framing that is incidental/metaphorical within a post about emotional experience → ES.
- If user describes AI filling a social connection void, playing a "friend" role, even with diverse behaviors (venting, seeking advice, daily sharing) → CO rather than individual behavior categories.
- Multiple intents: Code the most central intent in the post's narrative. If truly co-equal, code the first one that appears as the primary framing.
- N: Only when AI usage description is purely evaluative (positive or negative retrospection) with ZERO behavioral or intent information. Add reasoning noting "insufficient intent information."

────────────────────────────────────
BOUNDARY CASE DECISION TABLE
────────────────────────────────────
| Situation | Decision | Dimension |
|-----------|----------|-----------|
| Past therapy mentioned, no current therapist | If user describes past therapy as ended, failed, or replaced by AI → Source = Primary (therapy transition = ecological information). If user merely mentions having had therapy in the past with no connection to current AI use ecology → NM. | Source |
| Post has personal experience but is mostly general recommendations or community solicitation | If personal experience supports coding, code normally. If minimal (one sentence), note "thin coding evidence" in reasoning. | General |
| Post describes both barriers and preference | If barriers appear first or are structurally foregrounded → Primary. Solo only when preference clearly dominates without barriers. | Source |
| Post describes AI for multiple purposes | Code the most central purpose. If truly co-equal, code the first-appearing primary frame. | Type |
| Post is about someone else's AI use | If author provides own evaluative frame of other's experience, still codable. If pure third-person report, flag as boundary case. | General |
| Post is general AI discussion (no personal use) | Should have been filtered at Stage 1. Exclude. | General |
| Conflicting Timeframe signals | E.g., "I've been using ChatGPT for months [Habitual] but last night something happened [Episodic]." Code dominant temporal orientation. If post primarily narrates single event, code Episodic even with habitual background. | Timeframe |
| Friends/family support described as failed | Source = Primary, not Parallel. Note "failed informal support" in reasoning. | Source |
| "I use AI as my therapist" — with post evaluating AI's therapeutic quality | Type = TA. The therapy-evaluation frame is dominant. | Type |
| "I use AI as my therapist" — with post primarily describing emotional experience or self-discovery | Type = ES or SE depending on content. Therapy language is incidental/metaphorical, not the evaluative frame. | Type |
| Post describes heavy/habitual AI use but no help-seeking ecology information | Source = NM. Intensity/frequency of AI use tells you about Timeframe, NOT about Source. | Source |

══════════════════════════════════════════════════
OUTPUT FORMAT
══════════════════════════════════════════════════

Respond with ONLY a JSON object. No markdown, no code fences, no preamble.

If the post should be EXCLUDED:
{
  "excluded": true,
  "reason_for_exclusion": "<brief explanation of why the post is excluded, referencing the specific EX- criterion>",
  "timeframe": null,
  "source": null,
  "usage_intent": null,
  "confidence": null,
  "reasoning": null
}

If the post should NOT be excluded:
{
  "excluded": false,
  "reason_for_exclusion": null,
  "timeframe": "<Habitual | Episodic | NM>",
  "source": "<Primary | Supplement | Parallel | Solo | Exploration | NM>",
  "usage_intent": "<ES | VE | CO | RE | CR | PE | SA | SE | FS | RS | TA | SR | N | OT>",
  "confidence": <0.0-1.0>,
  "reasoning": "<brief explanation of coding decisions, including any boundary flags or disambiguation notes>"
}
"""

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
    parser.add_argument("--input", default=PILOT_SAMPLE)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    # 02_DIRECTORIES
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir   = os.path.join(script_dir, "..", "data")

    stem = os.path.splitext(args.input)[0]

    input_file      = os.path.join(data_dir, args.input)
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


if __name__ == "__main__":
    main()