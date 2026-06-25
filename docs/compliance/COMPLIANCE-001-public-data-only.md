# COMPLIANCE-001 — Public Data Only Policy

**Project**: Phoenix Engine  
**Author**: AI-CO-01 (Compliance Officer)  
**Status**: Draft — Phase 0 Foundation  
**Version**: 1.0  
**References**:
- [01-project-charter.md](../../01-project-charter.md) §3.2 Out-of-Scope, §10.2 Legal Constraints C1, C2, C5
- [05-product-requirements.md](../../05-product-requirements.md) §4.5 Ethical Scraping Requirements, F11, F15
- [10-risk-management.md](../../10-risk-management.md) R-L01, R-L03, R-L05, R-O11
- [12-definition-of-done.md](../../12-definition-of-done.md) §4.5 Compliance Gate CG-1, CG-9, CR-C-1

---

## 1. Purpose

This policy defines what "public data only" means for Phoenix Engine, how the engine detects and rejects private or restricted content, and what user-facing disclaimers are required. The policy is a compliance gate input for every adapter and is enforced by code, tests, and documentation.

---

## 2. Definition of "Public Data" per Platform

| Platform | Public Data Includes | Explicitly Excluded (Private/Restricted) |
|----------|---------------------|------------------------------------------|
| **Instagram** | Public post pages, public Reel pages, public profile bios, follower/post counts, comments on public posts | Private accounts, stories, direct messages, close-friends content, logged-in-only feeds |
| **X/Twitter** | Public tweet permalinks, public profile headers, public tweet counts, public replies visible without login | Protected tweets, direct messages, draft tweets, logged-in-only search/timeline |
| **TikTok** | Public video pages, public profile pages, public video metadata and visible comments | Private videos, private accounts, direct messages, friends-only content |
| **LinkedIn** | Public company pages, public job posts, public post permalinks, public profile summaries visible without login | Full profiles behind "LinkedIn Member" wall, InMail, private network data, recruiter-only views |
| **Facebook** | Public page posts, public event pages, public page metadata | Personal profiles, private groups, friends-only posts, marketplace DMs |
| **YouTube** | Public video pages, public channel pages, public comments, transcripts where exposed | Unlisted/private videos, age-restricted content without verification, YouTube Studio data |
| **Generic Web** | Any HTML page reachable over HTTPS that returns 200 without authentication, paywall, or challenge | Pages behind login forms, paywalls, members-only areas, pages requiring session cookies to render |

---

## 3. Detection and Rejection Checklist

Engineers must implement the following checks in the URL receiver / mode selector and in every platform adapter.

### 3.1 URL-Level Gates

| # | Check | Implementation Requirement | Failure Action |
|---|-------|---------------------------|----------------|
| 3.1.1 | Scheme enforcement | Reject or auto-upgrade `http://` to `https://` (see PRD §4.4 HTTPS enforcement) | Refuse to scrape HTTP-only URLs |
| 3.1.2 | robots.txt compliance | Parse `/robots.txt` by default; honor `Disallow` and `Crawl-delay` for the Phoenix Engine user-agent | Log restriction and return `RobotsDisallowedError` |
| 3.1.3 | URL pattern allowlist | Each adapter declares allowed public URL patterns; everything else is rejected | Return `UnsupportedUrlError` |
| 3.1.4 | noindex respect | If `<meta name="robots" content="noindex">` is present, skip extraction | Return `NoIndexError` |

### 3.2 Response-Level Gates

| # | Check | Implementation Requirement | Failure Action |
|---|-------|---------------------------|----------------|
| 3.2.1 | Authentication wall detection | Detect login redirects (HTTP 302/303 to `/login`, `/accounts/login`, `/auth`, etc.), login form presence, or gated content markers | Return `AuthenticationRequiredError`; do not follow login flow |
| 3.2.2 | CAPTCHA/challenge detection | Detect common challenge strings (`captcha`, `cf-turnstile`, `g-recaptcha`, `challenge-running`) | Return `ChallengeDetectedError`; never attempt bypass |
| 3.2.3 | Paywall detection | Detect common paywall markers (`subscription`, `paywall`, `subscribe to read`, `article__paywall`) | Return `PaywallDetectedError` |
| 3.2.4 | Private account markers | Platform-specific markers (e.g., Instagram "This Account is Private", X "These posts are protected", TikTok private account banner) | Return `PrivateContentError` |

### 3.3 Content-Level Gates

| # | Check | Implementation Requirement | Failure Action |
|---|-------|---------------------------|----------------|
| 3.3.1 | Visibility metadata extraction | Extract and log any public/private visibility badge present in HTML | If visibility != public, return `PrivateContentError` |
| 3.3.2 | Field minimization | Only extract fields requested by the user config; no bulk collection of related profiles or DMs | Log skipped fields |
| 3.3.3 | PII minimization | Do not collect email addresses, phone numbers, or government IDs even if present in public HTML | Redact or skip field |

---

## 4. User-Facing Disclaimers

### 4.1 Required in README / Docs

```markdown
Phoenix Engine only collects data that is publicly accessible without authentication,
paywall circumvention, or CAPTCHA bypass. Users are responsible for ensuring their use
complies with the Terms of Service of each target platform and with applicable laws
including GDPR and CCPA. Scraping public data may still violate a platform's ToS and
can result in account suspension, IP blocking, or legal notice.
```

### 4.2 Required in CLI First-Run / `--help`

- A one-time acknowledgment prompt on first run:  
  `I understand Phoenix Engine is for public data only and I am responsible for ToS compliance. [y/N]`
- `--tos-disclaimer` flag that prints the platform-specific ToS summary from `PLATFORM-TOS-SUMMARY.md`.

### 4.3 Required in Library API Docstrings

Every `scrape()` entry point must document:

```python
"""Scrape a publicly accessible URL.

Raises:
    AuthenticationRequiredError: If the URL requires a login session.
    PrivateContentError: If the content is marked private or restricted.
    ChallengeDetectedError: If a CAPTCHA or bot challenge is encountered.
    PaywallDetectedError: If the content is behind a paywall.
"""
```

### 4.4 Required in Error Messages

When a gate rejects content, the error payload must include:

```json
{
  "status": "error",
  "error_type": "PrivateContentError",
  "message": "This content is not publicly accessible.",
  "remediation": "Only public posts/profiles can be scraped. Check the URL or remove authentication requirements.",
  "docs_link": "https://docs.phoenixengine.dev/compliance/public-data-only"
}
```

---

## 5. Engineering Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| C001-AC01 | Every adapter rejects private-account URLs before extraction | Unit test with mocked private-account HTML |
| C001-AC02 | Login redirects never trigger an authenticated crawl | Integration test with 302-to-login response |
| C001-AC03 | CAPTCHA pages are rejected and never retried | Unit test with mocked challenge HTML |
| C001-AC04 | robots.txt `Disallow` is honored by default | Test with synthetic robots.txt |
| C001-AC05 | Error payloads include `error_type`, `message`, `remediation`, and `docs_link` | Schema test on error output |
| C001-AC06 | First-run ToS acknowledgment is persisted and auditable | Test config store contains acknowledgment hash |

---

## 6. Related Compliance Documents

- [PLATFORM-TOS-SUMMARY.md](PLATFORM-TOS-SUMMARY.md)
- [ETHICAL-GUARDRAILS.md](ETHICAL-GUARDRAILS.md)
- [COMPLIANCE-TEST-PLAN.md](COMPLIANCE-TEST-PLAN.md)
