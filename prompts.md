# Prompts

This document describes the prompts behind the optional **LLM brain** — the
mode where a real model decides phrasing, follow-up choice, assessment and
feedback instead of the deterministic engine. All prompt construction lives in
`interview_agent/prompts.py`; this file explains each prompt, when it is used,
and the JSON contracts it must honour.

> When the LLM is disabled (`AI_INTERVIEW_LLM_BASE_URL` unset), **no prompts are
> used at all** — the deterministic engine runs the entire interview and every
> prompt below is moot.

## At a glance

| Prompt | Constructor | Used by | Temperature | Window |
|---|---|---|---|---|
| Interviewer system prompt | `interviewer_system(profile, plan)` | `engine.InterviewSession._llm_turn` | 0.7 | last 14 transcript turns |
| Feedback system prompt | `feedback_system(profile, scores)` | `feedback._llm_feedback` | 0.4 | last 20 transcript turns |
| User turn instruction | inline in `_llm_turn` | `engine.py` | — | — |

## Interviewer prompt (`interviewer_system`)

One system message injected at the top of every LLM-powered interview turn. It
is rebuilt per session (not cached) because the profile and plan differ per
candidate.

Sections, in order:

1. **Role** — "a warm but rigorous senior AI engineering interviewer" for a
   graduate of the 31-day enterprise AI cohort. Emphasises assessing real
   understanding, one question per turn, natural phrasing.
2. **Candidate profile** — `profile["summary"]` (or the raw profile) dumped as
   JSON, so the model interviews *this* candidate's journey.
3. **Interview plan** — every planned question as a compact list:
   `{n, day, topic, question}`. The model may rephrase but must not skip.
4. **Rules** — exactly one message per turn; at most `MAX_FOLLOW_UPS` (1)
   follow-up per topic; reference what the candidate actually said; be
   encouraging on unsure answers; the engine controls progress, the model only
   reports its choice.
5. **Response format** — strict JSON, no markdown:

```json
{ "text": "<message to the candidate>",
  "action": "followup" | "advance",
  "assessment": "weak" | "solid" | "strong" }
```

- `action: "followup"` — a sharp follow-up was asked; the candidate answers again.
- `action: "advance"` — move to the next planned question.
- `assessment` is mapped to a numeric score: `weak` → 0.25, `solid` → 0.55,
  `strong` → 0.85.

### The turn the model sees

```
[system]  interviewer_system(profile, plan)
[user  ]  transcript_messages(transcript)          # last 14 turns
[user  ]  "The candidate just answered question {n} of {total}
           (Day {d} — {topic}). You may ask at most 1 follow-up on this topic
           (already asked: {count}). Respond with your JSON."
```

Engine guardrails still apply after the call: the one-follow-up-per-topic cap
is enforced regardless of what the model returns, unsure answers always advance,
and the closing/completion flow is owned by the engine.

## Feedback prompt (`feedback_system`)

A single system message sent to the model at the end of the interview to turn
the transcript into the spec's feedback schema.

Sections:

1. **Role** — "a senior technical mentor" writing honest, specific,
   encouraging, actionable end-of-interview feedback.
2. **Candidate profile** — same `profile["summary"]` as the interviewer.
3. **Per-topic assessment** — each covered topic with its average score, e.g.
   `{"Day 9 — Retrieval Augmented Generation": 0.82}`.
4. **Rules** — `summary` is 2-3 sentences naming what went well plus 1-2 areas
   to work on; `strengths` and `gaps` are 2-3 concise points, each tied to a
   specific topic and what the candidate actually said (or missed); `next` is
   3 concrete study/practice steps.
5. **Response format** — strict JSON:

```json
{ "summary": "...",
  "strengths": ["...", "..."],
  "gaps": ["...", "..."],
  "next": ["...", "..."] }
```

The turn is: system prompt → last 20 transcript turns → a user message asking
for the final JSON. Output is validated by `feedback._normalize` — it must have
a non-empty `summary` and at least one `strength` and each list is capped at 5
items, otherwise the response is discarded and the heuristic synthesizer is
used instead.

## Transcript window (`transcript_messages`)

`transcript_messages(transcript, tail=14)` trims the conversation to the most
recent 14 turns for the interviewer's context window (feedback uses the last
20 directly). This keeps token use bounded on long interviews while preserving
enough context to avoid repeating questions and to reference what the candidate
just said.

## Robustness & fallback

Prompt output is treated as best-effort, never trusted blindly:

- The request is sent with `response_format: {type: "json_object"}`; if the
  provider rejects it with a 400 (older Ollama), it is retried without it.
- Fenced markdown is stripped before parsing; if `json.loads` fails, the first
  `{...}` block is extracted as a last resort.
- Any failure — unreachable endpoint, timeout, malformed JSON, missing `text`,
  invalid feedback schema — returns `None`, and the caller falls back to the
  deterministic engine (interviewer) or the heuristic synthesizer (feedback).
  A circuit breaker in `engine.py` switches a session to fully deterministic
  mode after 2 consecutive LLM failures.

## Configuration

| Env var | Meaning |
|---|---|
| `AI_INTERVIEW_LLM_BASE_URL` | Any OpenAI-compatible `/v1` base URL (Ollama, OpenAI, Groq). Unset → LLM disabled. |
| `AI_INTERVIEW_LLM_API_KEY` | Bearer token; optional (Ollama needs none). |
| `AI_INTERVIEW_LLM_MODEL` | e.g. `qwen2.5-coder:7b`, `gpt-4o-mini`. |

The canonical source of truth for every prompt is `interview_agent/prompts.py` —
if the code and this document disagree, the code wins.
