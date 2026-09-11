import argparse
import asyncio
import json
import logging
from pathlib import Path

from dataclasses import asdict

from config import Settings
from crawler_models import PageData
from extractor import LLMExtractor
from scraper import CompanyCrawler


def _dump_pages(pages: list[PageData]) -> list[dict]:
    """PageData is a dataclass, not a Pydantic model, so it needs an
    explicit conversion before it can be handed to json.dumps."""
    return [asdict(page) for page in pages]


def load_domains(input_path: str | None, positional: list[str]) -> list[str]:
    if positional:
        return positional
    if input_path:
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Input JSON must be an array of domains.")
        return [str(x) for x in data]
    raise ValueError("Provide domains or --input domains.json")


async def run(domains: list[str], output_path: str, settings: Settings) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    crawler = CompanyCrawler(settings)
    extractor = LLMExtractor(settings)

    results = []
    total = len(domains)

    async with crawler:
        for index, domain in enumerate(domains, start=1):
            domain = domain.strip()
            print(f"\n[{index}/{total}] {domain}")

            crawl = await crawler.crawl(domain)
            if crawl.error:
                print(f"  ! crawl failed: {crawl.error}")
                results.append({
                    "domain": domain,
                    "status": "failed",
                    "error": crawl.error,
                    "source_pages": _dump_pages(crawl.pages),
                    "diagnostics": crawl.diagnostics,
                })
                continue

            print(f"  ✓ {len(crawl.pages)} pages collected")

            try:
                extracted = await extractor.extract(crawl)
                print("  ✓ structured extraction complete")
                # mode="json" converts Pydantic-specific types (HttpUrl, etc.)
                # to plain JSON-safe values; plain model_dump() leaves them
                # as HttpUrl objects, which json.dumps() below cannot encode.
                results.append(extracted.model_dump(mode="json"))
            except Exception as exc:
                logging.exception("LLM extraction failed for %s", domain)
                results.append({
                    "domain": domain,
                    "status": "partial",
                    "error": f"LLM extraction failed: {type(exc).__name__}: {exc}",
                    "source_pages": _dump_pages(crawl.pages),
                    "diagnostics": crawl.diagnostics,
                })

    Path(output_path).write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSaved {len(results)} records -> {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous company lead-enrichment agent."
    )
    parser.add_argument("domains", nargs="*", help="Company domains")
    parser.add_argument("--input", help="JSON file containing an array of domains")
    parser.add_argument("--output", default="output.json")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    settings = Settings()
    domains = load_domains(args.input, args.domains)
    asyncio.run(run(domains, args.output, settings))
