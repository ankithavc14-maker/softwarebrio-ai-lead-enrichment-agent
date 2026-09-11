# \# AI Lead Enrichment Agent

# 

# A Python autonomous lead-enrichment agent that crawls public company websites and uses a Large Language Model (LLM) to extract structured company intelligence.

# 

# \## Assignment

# 

# Built for the SoftwareBrio AI Engineer Intern practical take-home assignment.

# 

# The agent processes:

# 

# \- `postman.com`

# \- `supabase.com`

# \- `vapi.ai`

# 

# \## What It Does

# 

# For each company domain, the agent:

# 

# 1\. Opens the company website using Playwright.

# 2\. Discovers relevant public pages such as About, Team, Company, Contact, Pricing and Careers.

# 3\. Handles JavaScript-rendered content.

# 4\. Removes scripts, styles, SVGs, navigation and other unnecessary HTML.

# 5\. Converts webpage content into clean text before sending it to the LLM.

# 6\. Extracts structured company intelligence using Groq.

# 7\. Validates the response using Pydantic.

# 8\. Collects public contact emails and LinkedIn URLs.

# 9\. Assigns a data-confidence score.

# 10\. Continues processing even when individual pages fail.

# 

# \## Extracted Fields

# 

# The structured output contains:

# 

# \- Company overview

# \- Target audience / ICP

# \- Public contact emails

# \- Leadership / team members

# \- LinkedIn profile URLs

# \- Company LinkedIn URLs

# \- Data confidence score

# \- Source pages

# \- Extraction notes

# \- LLM token usage

# \- Estimated cost

# \## Architecture

# 

# The agent follows a modular pipeline from company domains to structured company intelligence.

# 

# | Step | Component | Responsibility |

# |---|---|---|

# | \*\*1\*\* | 📋 Company Domains | Reads target domains from `domains.json` |

# | ↓ | | |

# | \*\*2\*\* | 🌐 Playwright Crawler | Browses public pages and handles JavaScript-rendered content |

# | ↓ | | |

# | \*\*3\*\* | 🧹 HTML Cleaning | Removes scripts, styles, SVGs, navigation and irrelevant content |

# | ↓ | | |

# | \*\*4\*\* | 📝 Evidence Preprocessing | Selects relevant text and applies token limits |

# | ↓ | | |

# | \*\*5\*\* | ⚡ Groq LLM | Extracts company intelligence using structured output |

# | ↓ | | |

# | \*\*6\*\* | 🛡️ Pydantic Validation | Validates the response against the defined schema |

# | ↓ | | |

# | \*\*7\*\* | 📦 Structured JSON | Produces the final enrichment results |

# 

# \### Data Flow

# 

# ```text

# postman.com ─┐

# supabase.com ├──→ Playwright → Clean Text → Evidence → Groq LLM

# vapi.ai ─────┘                                      ↓

# &#x20;                                           Pydantic Validation

# &#x20;                                                    ↓

# &#x20;                                               output.json

