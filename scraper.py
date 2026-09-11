import asyncio
import logging
from urllib.parse import urljoin, urlparse

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from cleaner import clean_html
from config import Settings
from crawler_models import CrawlResult, PageData


logger = logging.getLogger(__name__)

KEYWORDS = (
    "about", "company", "team", "leadership", "founder",
    "contact", "pricing", "press", "people", "careers"
)


def normalize_domain(domain: str) -> str:
    domain = domain.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "")
    return domain.split("/")[0]


def is_same_domain(base_domain: str, url: str) -> bool:
    host = urlparse(url).netloc.lower().split(":")[0]
    return host == base_domain or host.endswith("." + base_domain)


def relevance(url: str, anchor: str) -> int:
    value = (url + " " + anchor).lower()
    return sum(1 for word in KEYWORDS if word in value)


class CompanyCrawler:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._pw = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def __aenter__(self):
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1440, "height": 1000},
            user_agent=(
                "SoftwareBrioLeadAgent/1.0 "
                "(public-site enrichment; contact: engineering)"
            ),
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()

    async def _goto(self, page: Page, url: str) -> bool:
        for attempt in range(self.settings.max_retries + 1):
            try:
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.settings.page_timeout_ms,
                )
                if response is None:
                    return True
                if response.status >= 400:
                    logger.warning("%s returned HTTP %s", url, response.status)
                    return False

                try:
                    await page.wait_for_load_state(
                        "networkidle",
                        timeout=min(self.settings.page_timeout_ms, 8000),
                    )
                except PlaywrightTimeoutError:
                    pass

                return True

            except PlaywrightTimeoutError:
                logger.warning("Timeout: %s (attempt %s)", url, attempt + 1)
            except Exception as exc:
                logger.warning("Navigation error %s: %s", url, exc)

            if attempt < self.settings.max_retries:
                await asyncio.sleep(0.7 * (attempt + 1))

        return False

    async def crawl(self, domain: str) -> CrawlResult:
        domain = normalize_domain(domain)
        start_url = f"https://{domain}/"
        result = CrawlResult(domain=domain)

        if not self.context:
            result.error = "Crawler context is not initialized."
            return result

        page = await self.context.new_page()

        try:
            if not await self._goto(page, start_url):
                result.error = "Homepage could not be loaded."
                return result

            html = await page.content()
            text, emails, linkedin = clean_html(
                html, self.settings.max_chars_per_page
            )
            result.pages.append(
                PageData(
                    url=page.url,
                    title=await page.title(),
                    text=text,
                    emails=emails,
                    linkedin_urls=linkedin,
                )
            )

            # Discover internal links from rendered DOM.
            links = await page.locator("a[href]").evaluate_all(
                """els => els.map(a => ({
                    href: a.href,
                    text: (a.innerText || a.getAttribute('aria-label') || '').trim()
                }))"""
            )

            candidates = []
            seen = {page.url.split("#")[0]}
            for item in links:
                url = item.get("href", "").split("#")[0]
                anchor = item.get("text", "")
                if not url or url in seen:
                    continue
                if not is_same_domain(domain, url):
                    continue
                if url.startswith(("mailto:", "tel:", "javascript:")):
                    continue

                score = relevance(url, anchor)
                if score > 0:
                    candidates.append((score, url))

            candidates.sort(key=lambda x: (-x[0], len(x[1])))

            for _, url in candidates[: self.settings.max_pages_per_domain - 1]:
                await asyncio.sleep(self.settings.crawl_delay_ms / 1000)

                subpage = await self.context.new_page()
                try:
                    if not await self._goto(subpage, url):
                        result.diagnostics.setdefault("failed_pages", []).append(url)
                        continue

                    html = await subpage.content()
                    text, emails, linkedin = clean_html(
                        html, self.settings.max_chars_per_page
                    )

                    if len(text.strip()) < 80:
                        result.diagnostics.setdefault(
                            "sparse_pages", []
                        ).append(url)
                        continue

                    result.pages.append(
                        PageData(
                            url=subpage.url,
                            title=await subpage.title(),
                            text=text,
                            emails=emails,
                            linkedin_urls=linkedin,
                        )
                    )
                except Exception as exc:
                    result.diagnostics.setdefault("failed_pages", []).append(
                        {"url": url, "error": str(exc)}
                    )
                finally:
                    await subpage.close()

            result.diagnostics["pages_attempted"] = len(candidates[: self.settings.max_pages_per_domain - 1]) + 1
            result.diagnostics["pages_collected"] = len(result.pages)
            return result

        except Exception as exc:
            logger.exception("Unexpected crawl failure for %s", domain)
            result.error = f"{type(exc).__name__}: {exc}"
            return result
        finally:
            await page.close()
