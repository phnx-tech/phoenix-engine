# Ethical Guardrails

**Project**: Phoenix Engine  
**Author**: AI-CO-01 (Compliance Officer)  
**Status**: Draft — Phase 0 Foundation  
**Version**: 1.0  
**Enforcement**: These rules are enforceable in code and CI. Exceptions require Human Legal Counsel approval and must be logged.

---

## 1. References

- [01-project-charter.md](../../01-project-charter.md) §3.2 Out-of-Scope, §10.2 Legal Constraints C1–C6
- [05-product-requirements.md](../../05-product-requirements.md) §4.4 Security Requirements, §4.5 Ethical Scraping Requirements, F11, F15
- [10-risk-management.md](../../10-risk-management.md) R-L02, R-L03, R-L05, R-O08, R-O11
- [12-definition-of-done.md](../../12-definition-of-done.md) §4.3 Security Gate SG-6, §4.5 Compliance Gate CG-1–CG-10

---

## 2. Enforceable Rules

### 2.1 Transparent User-Agent String

**Rule**: Phoenix Engine must identify itself with a transparent, non-deceptive user-agent on every request. Browser impersonation is prohibited.

**Default UA**:

```text
PhoenixEngine/1.0 (+https://phoenixengine.dev/bot; contact@phoenixengine.dev)
```

**Engineering Requirements**:

| # | Requirement | Verification |
|---|-------------|--------------|
| 2.1.1 | Default UA contains "PhoenixEngine" and a contact URL | `test_user_agent_transparent` |
| 2.1.2 | User cannot configure UA to a known browser string (Chrome, Firefox, Safari) | Config validator rejects browser-like UAs |
| 2.1.3 | Custom UAs must still contain "PhoenixEngine" substring or an override flag | Validator logs override with user acknowledgment |
| 2.1.4 | Playwright browser contexts set `userAgent` explicitly; stealth mode may not spoof vendor | Code review + test |

---

### 2.2 Rate Limiting Defaults per Domain

**Rule**: Respectful per-domain rate limits are enforced and cannot be fully disabled.

**Default Minimum Delays** (seconds between requests to the same domain):

| Domain / Platform | Default Delay | Maximum Allowable User Override | Notes |
|-------------------|---------------|---------------------------------|-------|
| `instagram.com` | 3.0 | 1.0 | Browser-only default |
| `twitter.com` / `x.com` | 2.0 | 1.0 | HTTP-first allowed |
| `tiktok.com` | 3.0 | 1.0 | Browser-only default |
| `linkedin.com` | 4.0 | 2.0 | Critical risk; stricter default |
| `facebook.com` | 3.0 | 1.0 | Browser mode recommended |
| `youtube.com` | 1.0 | 0.5 | HTTP-first allowed |
| Generic web | 1.0 | 0.5 | robots.txt may increase delay |

**Engineering Requirements**:

| # | Requirement | Verification |
|---|-------------|--------------|
| 2.2.1 | `default_delay >= 1.0s` always; config validator rejects lower values | `test_rate_limit_minimum` |
| 2.2.2 | Per-domain overrides cannot go below the "Maximum Allowable" in the table | `test_rate_limit_domain_floor` |
| 2.2.3 | robots.txt `Crawl-delay` is honored and raises the effective delay if higher | `test_robots_crawl_delay` |
| 2.2.4 | Exponential backoff on HTTP 429; respect `Retry-After` header | `test_rate_limit_backoff` |
| 2.2.5 | Global concurrency cap default 100; user can lower but not raise above 200 | `test_concurrency_cap` |
| 2.2.6 | Rate limiter maintains per-domain token bucket / queue state | Unit test with mocked clock |

---

### 2.3 Prohibited Behaviors

The following are **explicitly out of scope** per the Project Charter §3.2 and must be impossible or blocked by default.

| Prohibition | Definition | Enforcement |
|-------------|------------|-------------|
| **No CAPTCHA bypass** | Any attempt to solve, bypass, or delegate CAPTCHA/Cloudflare/hCaptcha challenges | Code does not integrate CAPTCHA-solving services; challenge pages raise `ChallengeDetectedError` |
| **No account automation** | Automated posting, liking, following, messaging, or any write/action operation | Adapter interface is read-only; no POST/PUT/DELETE actions to social platforms |
| **No impersonation** | Deceptive browser fingerprinting, forged headers, or fake account credentials | Config validator rejects browser-like UAs; no credential storage beyond session cookies |
| **No private data** | Extraction of non-public content (private accounts, DMs, groups, paywalled content) | Gates in [COMPLIANCE-001-public-data-only.md](COMPLIANCE-001-public-data-only.md) |
| **No paywall circumvention** | Bypassing subscription walls, incognito article limits, or soft paywalls | `PaywallDetectedError`; do not strip cookies to reset counters |
| **No auth bypass** | Using leaked tokens, credential stuffing, or session juggling to access walled content | Only user-imported session cookies; no password storage |

---

### 2.4 Audit Logging Requirements

**Rule**: Every scrape action creates an immutable, tamper-evident audit log entry.

**Required Log Fields**:

```json
{
  "event_type": "scrape",
  "event_id": "uuid",
  "timestamp": "2025-01-20T10:30:00Z",
  "source_url": "https://...",
  "domain": "example.com",
  "scraper_name": "instagram-post",
  "strategy": "browser",
  "user_agent": "PhoenixEngine/1.0 (...)",
  "status": "success|partial|error",
  "error_type": null,
  "rate_limit_delay_ms": 3000,
  "robots_txt_compliant": true,
  "cookies_used": false,
  "archive_path": "/archive/...",
  "previous_event_hash": "sha256:..."
}
```

**Engineering Requirements**:

| # | Requirement | Verification |
|---|-------------|--------------|
| 2.4.1 | Every scrape produces one log entry before output is returned | `test_audit_log_per_scrape` |
| 2.4.2 | Log entries are append-only; no delete or update API | `test_audit_log_immutable` |
| 2.4.3 | Hash chain links each entry to the previous entry (SHA-256) | `test_audit_log_hash_chain` |
| 2.4.4 | Log storage is local by default; cloud export is opt-in | Config review |
| 2.4.5 | Logs retained for 90 days by default; configurable | `test_audit_retention` |
| 2.4.6 | Sensitive cookie values are never written to audit log | `test_audit_no_secrets` |

---

### 2.5 GDPR / CCPA-Aligned Data Minimization

**Rule**: Collect only the data explicitly requested; pseudonymize where possible; support deletion.

**Engineering Requirements**:

| # | Requirement | Verification |
|---|-------------|--------------|
| 2.5.1 | Adapter extracts only fields declared in the scrape config | `test_data_minimization_fields` |
| 2.5.2 | Email addresses, phone numbers, and government IDs are redacted by default | `test_pii_redaction` |
| 2.5.3 | Output schema tags personal data fields with `pii: true` | Schema validation test |
| 2.5.4 | User can export all archived data and audit logs for a domain | `test_data_export` |
| 2.5.5 | User can delete all archived data and audit logs for a domain | `test_data_deletion` |
| 2.5.6 | Retention policy auto-deletes archives older than configured days | `test_retention_policy` |
| 2.5.7 | No PII sent to external LLM providers during AI-assisted extraction | `test_no_pii_to_llm` |

---

## 3. Configuration Guardrails

Example `config.yaml` with guardrails enforced:

```yaml
rate_control:
  default_delay: 1.0
  max_concurrent: 100
  per_domain:
    instagram.com: 3.0
    x.com: 2.0
    twitter.com: 2.0
    tiktok.com: 3.0
    linkedin.com: 4.0
    facebook.com: 3.0
    youtube.com: 1.0

scraping:
  user_agent: "PhoenixEngine/1.0 (+https://phoenixengine.dev/bot; contact@phoenixengine.dev)"
  allow_user_agent_override: false   # requires explicit opt-in + acknowledgment
  robots_txt_enabled: true
  challenge_bypass_enabled: false    # hardcoded false; no config override
  archive_enabled: true
  archive_retention_days: 90

security:
  cookie_encryption: AES-256-GCM
  audit_log_immutable: true
```

---

## 4. Violation Handling

| Severity | Example | Response |
|----------|---------|----------|
| **Block** | User config sets UA to Chrome, delay to 0.1s | Refuse startup / refuse scrape; log incident |
| **Warn** | robots.txt override flag set | Log explicit acknowledgment; continue |
| **Alert** | Repeated 429s from one domain | Auto-increase delay 2x; notify user |
| **Escalate** | Legal notice received | Suspend adapter; notify Human Legal Counsel |

---

## 5. Sign-Off

| Role | ID | Status |
|------|----|--------|
| AI Compliance Officer | AI-CO-01 | Draft |
| Human Legal Counsel | Human-LC-01 | ☐ Pending |
