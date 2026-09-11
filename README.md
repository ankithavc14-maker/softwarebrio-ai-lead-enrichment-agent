# AI Lead Enrichment Agent

A Python autonomous lead-enrichment agent that crawls public company websites and uses an LLM to extract structured company intelligence.

Built for the **SoftwareBrio AI Engineer Intern Practical Take-Home Assignment**.

---

## Assignment Overview

The objective is to build an autonomous lead-enrichment agent that accepts company domains, gathers publicly available information from the web, and produces structured company intelligence using an LLM.

This implementation processes the following required domains:

- `postman.com`
- `supabase.com`
- `vapi.ai`

---

## What the Agent Does

For each company domain, the agent:

1. Reads company domains from an input JSON file.
2. Uses **Playwright** to browse the company's public website.
3. Discovers relevant pages such as:
   - About
   - Team
   - Company
   - Contact
   - Pricing
   - Careers
4. Handles JavaScript-rendered webpages.
5. Extracts the useful page content.
6. Removes unnecessary HTML content such as scripts, styles, SVGs and navigation.
7. Converts webpages into clean text before sending evidence to the LLM.
8. Applies configurable page and evidence limits for token optimization.
9. Uses **Groq** for structured LLM extraction.
10. Validates the extracted data using **Pydantic**.
11. Collects publicly available contact emails and LinkedIn URLs.
12. Assigns a data-confidence score.
13. Records source pages and extraction notes.
14. Continues processing when individual pages or requests fail.
15. Saves the final structured results to `output.json`.

---

## Extracted Company Intelligence

For every company, the agent extracts:

| Field | Description |
|---|---|
| Company Overview | Concise two-sentence description of the company |
| Target Audience / ICP | Primary users or customer profile |
| Contact Emails | Publicly available contact emails |
| Leadership / Team | Names and roles discovered from public sources |
| LinkedIn URLs | Company and relevant individual LinkedIn URLs |
| Data Confidence Score | Confidence score from `0.0` to `1.0` |
| Source Pages | URLs used as evidence |
| Extraction Notes | Additional extraction information |
| LLM Token Usage | Input and output token counts |
| Estimated Cost | Application-level cost metadata |

---

# Architecture

The agent follows a modular pipeline from company domains to structured company intelligence.

| Step | Component | Responsibility |
|---|---|---|
| **1** | Company Domains | Reads target domains from `domains.json` |
| **2** | Playwright Crawler | Browses public pages and handles JavaScript-rendered content |
| **3** | HTML Cleaning | Removes scripts, styles, SVGs, navigation and irrelevant HTML |
| **4** | Evidence Preprocessing | Selects useful text and applies character/evidence limits |
| **5** | Groq LLM | Extracts structured company intelligence |
| **6** | Pydantic Validation | Validates the extracted response against the defined schema |
| **7** | Structured JSON | Produces the final enrichment results |

## Data Flow

```text
Company Domains
      │
      ▼
Playwright Crawler
      │
      ▼
Public Web Pages
      │
      ▼
HTML Cleaning
      │
      ▼
Clean Text / Evidence
      │
      ▼
Groq LLM
      │
      ▼
Structured Extraction
      │
      ▼
Pydantic Validation
      │
      ▼
Structured JSON Output
      │
      ▼
output.json
