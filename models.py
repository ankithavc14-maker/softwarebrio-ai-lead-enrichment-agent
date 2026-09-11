from pydantic import BaseModel, ConfigDict, Field


class TeamMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    role: str
    linkedin_url: str


class CompanyIntelligence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    status: str = "success"

    company_overview: str = Field(
        description="A concise two-sentence summary of what the company does."
    )

    target_audience_icp: str = Field(
        description="Who the product is primarily built for."
    )

    contact_emails: list[str] = Field(
        default_factory=list,
        description="Only public or generic emails explicitly found in the evidence."
    )

    leadership_team: list[TeamMember] = Field(
        default_factory=list,
        description="Leadership or team members supported by the evidence."
    )

    linkedin_urls: list[str] = Field(
        default_factory=list,
        description="LinkedIn URLs found or externally discovered."
    )

    data_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Estimated quality and completeness of extracted data."
    )

    source_pages: list[str] = Field(default_factory=list)
    extraction_notes: list[str] = Field(default_factory=list)

    tokens_input: int = 0
    tokens_output: int = 0
    estimated_cost_usd: float = 0.0