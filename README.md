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

# 

# \## Architecture

# 

# ```text

# Company Domains

# &#x20;     |

# &#x20;     v

# +------------------+

# | Playwright Crawler|

# +------------------+

# &#x20;     |

# &#x20;     v

# +------------------+

# | HTML Cleaning    |

# | \& Text Extraction|

# +------------------+

# &#x20;     |

# &#x20;     v

# +------------------+

# | Evidence          |

# | Preprocessing     |

# +------------------+

# &#x20;     |

# &#x20;     v

# +------------------+

# | Groq LLM          |

# | Structured JSON   |

# +------------------+

# &#x20;     |

# &#x20;     v

# +------------------+

# | Pydantic          |

# | Validation        |

# +------------------+

# &#x20;     |

# &#x20;     v

# &#x20;  output.json

