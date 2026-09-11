# 2–3 Minute Loom Script

## 0:00–0:20 — Intro

"Hi, this is my solution for the SoftwareBrio AI Engineer Intern take-home.

The goal is to take company domains and autonomously enrich them with company
overview, ICP, public contact points, leadership and LinkedIn information."

## 0:20–0:55 — Architecture

"At a high level, I use Playwright Chromium for JavaScript-capable browsing.
The crawler starts from the homepage, discovers relevant same-domain pages,
and prioritizes pages containing about, company, team, leadership, contact,
pricing and related keywords.

I then clean the rendered DOM before any LLM call. Scripts, styles, SVGs,
navigation and repeated boilerplate are removed, and the evidence is capped
per page and globally to control token usage."

## 0:55–1:25 — Structured extraction

"The extraction layer uses an OpenAI Responses API call with a strict JSON
Schema generated from a Pydantic model.

The model is explicitly instructed to use only supplied evidence and never
invent missing information.

Emails and LinkedIn URLs are also detected deterministically from the
rendered page, which gives us a second validation layer."

## 1:25–1:55 — Resilience

"Each page is isolated so a timeout or HTTP error does not stop the company
crawl. Each company is also isolated, so one blocked domain does not stop the
remaining targets.

There is an optional Tavily integration for external LinkedIn discovery when
the direct site does not expose profile links."

## 1:55–2:25 — Run

"Here I run the required three domains: postman.com, supabase.com and vapi.ai.

The terminal shows the number of pages collected and whether structured
extraction completed. The final output is written to output.json."

## 2:25–2:45 — Output

"The JSON contains the requested fields plus source pages, diagnostics and
token/cost metadata when available.

This design directly targets the rubric: 30 percent scraping architecture,
25 percent structured LLM extraction, and 20 percent resilience."

## Final line

"Thanks for reviewing my submission."
