import json
import logging
from typing import Any

from groq import AsyncGroq

from config import Settings
from models import CompanyIntelligence
from crawler_models import CrawlResult

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are a company intelligence extraction agent.

Your task is to extract structured company intelligence from public-web evidence.

IMPORTANT RULES:

1. Use ONLY information supported by the supplied evidence.
2. Do NOT invent names, roles, emails, URLs, or company information.
3. If information is unavailable, return an empty list or an appropriate empty value.
4. The company overview MUST contain exactly two concise sentences.
5. Identify the company's target audience / ideal customer profile.
6. Extract only public contact emails explicitly supported by the evidence.
7. Extract leadership or team members only when supported by the evidence.
8. Include LinkedIn URLs only when they are present in the evidence.
9. Include company LinkedIn URLs when they are present in the evidence.
10. Assign a confidence score between 0.0 and 1.0 based on evidence quality and completeness.
11. Include the source pages used for the extraction.
12. Include useful extraction notes when information is incomplete or ambiguous.
13. Do not use raw HTML as evidence. The supplied evidence has already been cleaned.
14. Do not generate token counts or cost information. Those values are added by the Python application.
"""


def build_groq_schema() -> dict:
    """
    Build the JSON schema sent to Groq.

    Groq strict JSON schema requires every property to be listed
    in the required array.

    Token/cost fields are application-generated and therefore must
    not be included in the LLM response schema.
    """

    schema = CompanyIntelligence.model_json_schema()

    application_fields = {
        "tokens_input",
        "tokens_output",
        "estimated_cost_usd",
    }

    properties = schema.get("properties", {})

    # Remove application-generated fields from the LLM schema.
    for field in application_fields:
        properties.pop(field, None)

    schema["properties"] = properties

    # Groq strict mode requires every property to be required.
    schema["required"] = list(properties.keys())

    # Make nested definitions strict as well.
    definitions = schema.get("$defs", {})

    for definition in definitions.values():
        if "properties" in definition:
            definition["required"] = list(
                definition["properties"].keys()
            )

    return schema


class LLMExtractor:
    """Extract structured company intelligence using Groq."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncGroq(
            api_key=settings.groq_api_key
        )

    @staticmethod
    def _get_page_value(page: Any, field: str, default: Any = "") -> Any:
        """Safely retrieve a field from a crawler page object."""
        try:
            value = getattr(page, field, default)

            if value is None:
                return default

            return value

        except Exception:
            return default

    def _build_evidence(self, crawl: CrawlResult) -> str:
        """
        Build compact evidence from crawled pages.

        Raw HTML is never sent to the LLM.
        """

        evidence_parts: list[str] = []
        total_chars = 0

        pages = getattr(crawl, "pages", []) or []

        for page in pages:
            url = self._get_page_value(page, "url", "")
            text = self._get_page_value(page, "text", "")

            # Some crawler versions may use `content`.
            if not text:
                text = self._get_page_value(page, "content", "")

            if not text:
                continue

            text = str(text).strip()

            if not text:
                continue

            # Limit evidence from an individual page.
            text = text[: self.settings.max_chars_per_page]

            remaining = (
                self.settings.max_total_evidence_chars
                - total_chars
            )

            if remaining <= 0:
                break

            text = text[:remaining]

            evidence_parts.append(
                f"--- SOURCE PAGE: {url} ---\n{text}"
            )

            total_chars += len(text)

        return "\n\n".join(evidence_parts)

    async def extract(
        self,
        crawl: CrawlResult,
    ) -> CompanyIntelligence:

        domain = getattr(crawl, "domain", "")

        evidence = self._build_evidence(crawl)

        if not evidence:
            logger.warning(
                "No usable evidence found for %s",
                domain,
            )

            return CompanyIntelligence(
                domain=domain,
                status="partial",
                company_overview="",
                target_audience_icp="",
                contact_emails=[],
                leadership_team=[],
                linkedin_urls=[],
                data_confidence_score=0.0,
                source_pages=[],
                extraction_notes=[
                    "No usable webpage evidence was available."
                ],
                tokens_input=0,
                tokens_output=0,
                estimated_cost_usd=0.0,
            )

        user_prompt = f"""
Extract company intelligence for:

DOMAIN:
{domain}

PUBLIC WEB EVIDENCE:
{evidence}

Return only the structured JSON object defined by the response schema.
"""

        schema = build_groq_schema()

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.groq_model,
                temperature=0,
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
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "company_intelligence",
                        "strict": True,
                        "schema": schema,
                    },
                },
            )

            raw_content = response.choices[0].message.content

            if not raw_content:
                raise ValueError(
                    "Groq returned an empty response."
                )

            data = json.loads(raw_content)

            # Ensure the domain comes from our input rather than
            # allowing the model to change it.
            data["domain"] = domain

            # Ensure status is present.
            data.setdefault("status", "success")

            # Add source pages from the crawler if the model
            # did not provide them.
            if not data.get("source_pages"):
                data["source_pages"] = [
                    self._get_page_value(page, "url", "")
                    for page in (
                        getattr(crawl, "pages", []) or []
                    )
                    if self._get_page_value(page, "url", "")
                ]

            usage = getattr(response, "usage", None)

            tokens_input = 0
            tokens_output = 0

            if usage is not None:
                tokens_input = int(
                    getattr(
                        usage,
                        "prompt_tokens",
                        0,
                    )
                    or 0
                )

                tokens_output = int(
                    getattr(
                        usage,
                        "completion_tokens",
                        0,
                    )
                    or 0
                )

            # These fields are generated by Python, not the LLM.
            data["tokens_input"] = tokens_input
            data["tokens_output"] = tokens_output
            data["estimated_cost_usd"] = 0.0

            data.setdefault(
                "extraction_notes",
                [],
            )

            result = CompanyIntelligence.model_validate(data)

            logger.info(
                "Structured extraction complete for %s",
                domain,
            )

            return result

        except Exception as exc:
            logger.exception(
                "LLM extraction failed for %s",
                domain,
            )

            return CompanyIntelligence(
                domain=domain,
                status="failed",
                company_overview="",
                target_audience_icp="",
                contact_emails=[],
                leadership_team=[],
                linkedin_urls=[],
                data_confidence_score=0.0,
                source_pages=[
                    self._get_page_value(page, "url", "")
                    for page in (
                        getattr(crawl, "pages", []) or []
                    )
                    if self._get_page_value(page, "url", "")
                ],
                extraction_notes=[
                    f"LLM extraction failed: {str(exc)}"
                ],
                tokens_input=0,
                tokens_output=0,
                estimated_cost_usd=0.0,
            )