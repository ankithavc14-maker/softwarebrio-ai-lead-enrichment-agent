from dataclasses import dataclass, field


@dataclass
class PageData:
    url: str
    title: str
    text: str
    emails: list[str] = field(default_factory=list)
    linkedin_urls: list[str] = field(default_factory=list)


@dataclass
class CrawlResult:
    domain: str
    pages: list[PageData] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)
    error: str | None = None

    @property
    def evidence_text(self) -> str:
        chunks = []
        for page in self.pages:
            chunks.append(
                f"### SOURCE: {page.url}\n"
                f"TITLE: {page.title}\n"
                f"{page.text}"
            )
        return "\n\n".join(chunks)
