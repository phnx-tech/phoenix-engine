# Platform Terms of Service Summary

**Project**: Phoenix Engine  
**Author**: AI-CO-01 (Compliance Officer)  
**Status**: Draft — Phase 0 Foundation  
**Version**: 1.0  
**Purpose**: Provide the per-platform ToS brief required by [12-definition-of-done.md](../../12-definition-of-done.md) §2.4 Phase 2 Entry Criterion P2-E3 and the compliance matrix required by §4.5 Compliance Gate CG-5.

> **Legal Notice**: This is a technical engineering summary, not legal advice. Platform ToS change frequently. Human Legal Counsel must review before launch.

---

## 1. Risk Legend

| Level | Meaning | Engineering Response |
|-------|---------|----------------------|
| **Low** | Public scraping is broadly tolerated or explicitly allowed with conditions | Implement baseline ethical guardrails |
| **Medium** | ToS restrict automated access but enforcement focuses on abuse | Conservative rate limits; transparent UA; public-data only |
| **High** | ToS explicitly prohibit scraping; active anti-bot/anti-scraping enforcement | Strict per-domain limits; no browser impersonation; prominent disclaimers |
| **Critical** | Aggressive legal/technical enforcement; high probability of blocks or notices | Minimum viable support only; consider P1/P2 deprecation; legal sign-off required |

---

## 2. Platform Summary Table

| Platform | Scraping Public Pages vs. ToS | Explicitly Prohibited Behaviors | Recommended Mitigations | Risk Level |
|----------|------------------------------|---------------------------------|------------------------|------------|
| **Instagram** | ToS generally prohibit automated data collection and crawling. Public post/profile pages are accessible without login but Meta actively enforces anti-bot measures. | Scraping private accounts; using fake/impersonated user agents; bulk collection; circumventing rate limits or technical protections; using scraped data to build competing products. | 3-second minimum delay; browser mode only; transparent UA; no login-required URLs; limit scroll depth. | **High** |
| **X/Twitter** | Developer Policy and ToS prohibit scraping without authorization. Public tweet permalinks are accessible, but X has historically litigated (hiQ v. LinkedIn is LinkedIn, not X) and deploys aggressive bot detection. | Accessing non-public areas; automated following/liking/posting; bypassing authentication; reverse engineering internal APIs; impersonating browsers. | 2-second minimum delay; respect robots.txt; do not scrape search/trends; transparent UA; fallback selectors. | **High** |
| **TikTok** | ToS prohibit automated access, scraping, and data extraction. Heavy JavaScript rendering and anti-bot stack. | Bulk video downloads; private account access; mimicking mobile apps; using scraped content for redistribution. | 3-second minimum delay; browser mode; block unnecessary resources; no account automation; public videos only. | **High** |
| **LinkedIn** | robots.txt and User Agreement explicitly prohibit scraping public profiles without written permission. hiQ v. LinkedIn addressed CFAA but did not invalidate contract/ToS claims. | Scraping member profiles; bypassing auth walls; using data for recruitment/product development without consent; ignoring robots.txt. | 4-second minimum delay; public company pages and public posts only; honor robots.txt strictly; do not scrape profile directories. | **Critical** |
| **Facebook** | ToS prohibit automated data collection. Public pages are reachable but Facebook aggressively fingerprints browsers and blocks scrapers. | Scraping personal profiles; private groups; events requiring login; using fake accounts; bulk harvesting. | 3-second minimum delay; public pages only; browser mode; transparent UA; no login-wall URLs. | **High** |
| **YouTube** | ToS restrict automated access to Services. Public watch pages and channel pages are accessible, but scraping is against Terms. robots.txt is relatively permissive for watch pages. | Downloading videos; bypassing age restrictions; accessing YouTube Studio; redistributing content at scale; impersonating official clients. | 1-second minimum delay; HTTP-first strategy allowed; respect robots.txt; extract metadata only; no video downloads. | **Medium** |
| **Generic Web** | Varies by site. robots.txt is the primary machine-readable signal. Copyright and database rights may apply even to public pages. | Ignoring robots.txt; hotlinking media at scale; scraping private areas; republishing substantial content without rights. | 1-second default delay; robots.txt check; transparent UA; honor noindex; stop on challenge pages. | **Low–Medium** |

---

## 3. Engineering Actions per Risk Level

### Critical (LinkedIn)

1. Gate 1: Only allow URLs that resolve to public company pages, public posts, and public job listings.
2. Gate 2: Reject any URL pattern that matches member profile directories (`/in/` URLs that redirect to auth wall).
3. Gate 3: robots.txt compliance cannot be overridden by user config without written acknowledgment logged.
4. Gate 4: Adapter marked as "high legal risk" in docs and CLI warnings.

### High (Instagram, X/Twitter, TikTok, Facebook)

1. Gate 1: Browser-only default for Instagram and TikTok; HTTP-first allowed for X and Facebook with fallback.
2. Gate 2: Transparent user-agent string (see [ETHICAL-GUARDRAILS.md](ETHICAL-GUARDRAILS.md)).
3. Gate 3: Conservative rate limits; auto-backoff on 429; pause on repeated blocks.
4. Gate 4: Clear ToS warnings in adapter docs.

### Medium (YouTube)

1. Gate 1: HTTP-first strategy; browser fallback for comments.
2. Gate 2: robots.txt honored.
3. Gate 3: No video/audio download; metadata-only extraction.

### Low–Medium (Generic Web)

1. Gate 1: robots.txt and noindex checks by default.
2. Gate 2: Transparent UA and polite delays.
3. Gate 3: User is warned that site-specific ToS may apply.

---

## 4. Compliance Matrix Template

Use this template to report adapter status at Phase 2 exit (see DoD §4.5 Compliance Gate CG-5).

| Platform | Public Data Only | Rate Limits | ToS Disclaimers | Login Wall Handling | Risk Level |
|----------|------------------|-------------|-----------------|---------------------|------------|
| Instagram | ☐ | ☐ | ☐ | Graceful error | High |
| X/Twitter | ☐ | ☐ | ☐ | Graceful error | High |
| TikTok | ☐ | ☐ | ☐ | Graceful error | High |
| LinkedIn | ☐ | ☐ | ☐ | Graceful error | Critical |
| Facebook | ☐ | ☐ | ☐ | Graceful error | High |
| YouTube | ☐ | ☐ | ☐ | Graceful error | Medium |
| Generic Web | ☐ | ☐ | ☐ | Graceful error | Low-Medium |

---

## 5. References

- [01-project-charter.md](../../01-project-charter.md) §3.2 Out-of-Scope (CAPTCHA bypass, account automation, private data, impersonation)
- [05-product-requirements.md](../../05-product-requirements.md) §4.5 Ethical Scraping Requirements
- [10-risk-management.md](../../10-risk-management.md) R-L01 Website ToS, R-L02 robots.txt, R-L05 CFAA, R-L06 Jurisdictional
- [12-definition-of-done.md](../../12-definition-of-done.md) §2.4 P2-E3, §4.5 Compliance Gate
