import json

from groq import AsyncGroq

from cleaner import dedupe_and_budget
from config import Settings
from crawler_models import CrawlResult
from models import CompanyIntelligence
from search import tavily_leadership_search


SYSTEM_PROMPT = """You are a lead-enrichment extraction agent.

Use ONLY the supplied public-web evidence. Do not invent facts, names, emails,
roles, URLs, or company claims.

Rules:
- company_overview must be exactly two concise sentences.
- target_audience_icp should describe the clearest supported customer audience.
- contact_emails may contain only public/generic emails supported by evidence.
- leadership_team should contain people whose name and role are supported.
- linkedin_urls should contain only LinkedIn URLs supported by evidence.
- If information is unavailable, use an empty string or empty list.
- data_confidence_score must be between 0.0 and 1.0.
"""


class LLMExtractor:

    def __init__(self, settings: Settings):
        self.settings = settings

        self.client = AsyncGroq(
            api_key=settings.groq_api_key
        )

    async def extract(self, crawl: CrawlResult) -> CompanyIntelligence:

        evidence = dedupe_and_budget(
            crawl.evidence_text,
            self.settings.max_total_evidence_chars,
        )

        deterministic_emails = sorted({
            email.lower()
            for page in crawl.pages
            for email in page.emails
        })

        deterministic_linkedin = sorted({
            url
            for page in crawl.pages
            for url in page.linkedin_urls
        })

        external_links = []

        if self.settings.tavily_api_key and not deterministic_linkedin:

            external_links = await tavily_leadership_search(
                self.settings.tavily_api_key,
                crawl.domain,
                "founder CEO leadership team",
            )

        supplemental = ""

        if deterministic_emails:
            supplemental += (
                "\n\nDETERMINISTIC EMAILS FOUND:\n"
                + "\n".join(deterministic_emails)
            )

        if deterministic_linkedin:
            supplemental += (
                "\n\nDETERMINISTIC LINKEDIN URLS FOUND:\n"
                + "\n".join(deterministic_linkedin)
            )

        if external_links:
            supplemental += (
                "\n\nEXTERNAL LINKEDIN DISCOVERY:\n"
                + "\n".join(external_links)
            )

        user_prompt = (
            f"Company domain: {crawl.domain}\n\n"
            "PUBLIC WEB EVIDENCE:\n"
            f"{evidence}"
            f"{supplemental}\n\n"
            "Extract the requested company intelligence."
        )

        schema = CompanyIntelligence.model_json_schema()

        response = await self.client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "company_intelligence",
                    "strict": True,
                    "schema": schema,
                },
            },
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("Groq returned an empty response.")

        parsed = CompanyIntelligence.model_validate(
            json.loads(content)
        )

        parsed.domain = crawl.domain
        parsed.status = "success"

        parsed.source_pages = [
            page.url for page in crawl.pages
        ]

        parsed.contact_emails = sorted(
            set(parsed.contact_emails)
            .union(deterministic_emails)
        )

        merged_linkedin = set(
            parsed.linkedin_urls
        )

        merged_linkedin.update(
            deterministic_linkedin
        )

        merged_linkedin.update(
            external_links
        )

        parsed.linkedin_urls = sorted(
            merged_linkedin
        )

        usage = getattr(response, "usage", None)

        if usage:
            parsed.tokens_input = getattr(
                usage,
                "prompt_tokens",
                0,
            )

            parsed.tokens_output = getattr(
                usage,
                "completion_tokens",
                0,
            )

            parsed.estimated_cost_usd = 0.0

        parsed.extraction_notes = [
            "Extraction is grounded in cleaned public webpage evidence.",
            "Raw HTML, scripts, styles and SVG content are excluded from the LLM context.",
            "Groq was used for structured LLM extraction.",
        ]

        if external_links:
            parsed.extraction_notes.append(
                "LinkedIn URLs were supplemented using the optional Tavily search integration."
            )

        return parsed