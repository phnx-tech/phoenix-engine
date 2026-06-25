# Compliance Test Plan

**Project**: Phoenix Engine  
**Author**: AI-CO-01 (Compliance Officer)  
**Status**: Draft — Phase 0 Foundation  
**Version**: 1.0  
**Test Framework**: pytest  
**References**:
- [01-project-charter.md](../../01-project-charter.md) §5 Success Criteria (test coverage ≥80%), §10.2 Legal Constraints
- [05-product-requirements.md](../../05-product-requirements.md) F11, F15, §4.4 Security, §4.5 Ethical Scraping
- [10-risk-management.md](../../10-risk-management.md) R-L02, R-L03, R-L05
- [12-definition-of-done.md](../../12-definition-of-done.md) §1.4 Test Additions D-T1–D-T6, §4.3 Security Gate, §4.5 Compliance Gate

---

## 1. Test Organization

```text
tests/
└── compliance/
    ├── test_public_data_only.py
    ├── test_rate_limit.py
    ├── test_user_agent.py
    ├── test_audit_log.py
    └── test_credential_encryption.py
```

---

## 2. Public-Data-Only Tests

**File**: `tests/compliance/test_public_data_only.py`

| ID | Scenario | Arrange | Act | Assert |
|----|----------|---------|-----|--------|
| C-PUB-001 | Private Instagram account rejected | Mock HTML containing "This Account is Private" | Scrape URL | `PrivateContentError` raised; status `error` |
| C-PUB-002 | Protected X/Twitter tweet rejected | Mock HTML containing "These posts are protected" | Scrape URL | `PrivateContentError` raised |
| C-PUB-003 | Login redirect rejected | Mock HTTP 302 to `/login` | Scrape URL | `AuthenticationRequiredError`; no follow |
| C-PUB-004 | CAPTCHA page rejected | Mock HTML with `g-recaptcha` | Scrape URL | `ChallengeDetectedError`; no bypass attempt |
| C-PUB-005 | Paywall page rejected | Mock HTML with `paywall` class | Scrape URL | `PaywallDetectedError` |
| C-PUB-006 | robots.txt Disallow honored | Synthetic robots.txt disallows `/private/` | Scrape `/private/x` | `RobotsDisallowedError` |
| C-PUB-007 | noindex meta honored | Mock HTML with `<meta name="robots" content="noindex">` | Scrape URL | `NoIndexError` |
| C-PUB-008 | Public generic web page allowed | Mock public article HTML | Scrape URL | Status `success`; data extracted |
| C-PUB-009 | PII redaction in public page | Mock HTML with embedded email | Scrape URL | Email redacted or field skipped |
| C-PUB-010 | Error payload schema | Trigger `PrivateContentError` | Inspect payload | Contains `error_type`, `message`, `remediation`, `docs_link` |

---

## 3. Rate-Limit Tests

**File**: `tests/compliance/test_rate_limit.py`

| ID | Scenario | Arrange | Act | Assert |
|----|----------|---------|-----|--------|
| C-RATE-001 | Default delay enforced | Mock clock; two requests to same domain | Measure interval | Interval ≥ `default_delay` |
| C-RATE-002 | Domain-specific delay enforced | Config `instagram.com: 3.0` | Two requests to instagram.com | Interval ≥ 3.0s |
| C-RATE-003 | Minimum delay floor | User config sets delay to 0.1s | Validate config | Validation error; floor enforced |
| C-RATE-004 | robots.txt crawl-delay honored | robots.txt has `Crawl-delay: 5` | Request domain | Effective delay ≥ 5s |
| C-RATE-005 | 429 triggers exponential backoff | Server returns 429 with `Retry-After: 10` | Scrape URL | Wait ≥ 10s; retry logged |
| C-RATE-006 | Global concurrency cap | Config `max_concurrent: 100`; submit 150 URLs | Start batch | No more than 100 active at once |
| C-RATE-007 | Per-domain queue isolation | 10 URLs each for 3 domains | Run batch | Each domain observes its own delay |
| C-RATE-008 | Override acknowledgment logged | User overrides robots.txt | Scrape | Audit log contains override flag |

---

## 4. User-Agent Tests

**File**: `tests/compliance/test_user_agent.py`

| ID | Scenario | Arrange | Act | Assert |
|----|----------|---------|-----|--------|
| C-UA-001 | Default UA transparent | Default config | Make HTTP request | UA contains "PhoenixEngine" and contact URL |
| C-UA-002 | Browser UA rejected | User config sets Chrome UA | Validate config | Validation error |
| C-UA-003 | Custom UA must identify Phoenix Engine | User config sets custom UA without PhoenixEngine | Validate config | Validation error unless override flag set |
| C-UA-004 | Playwright context uses configured UA | Browser mode | Capture network UA | Matches config UA |
| C-UA-005 | Stealth mode does not spoof vendor | Enable stealth | Check navigator | Vendor not falsified to Chrome/Firefox/Safari |

---

## 5. Audit Log Immutability Tests

**File**: `tests/compliance/test_audit_log.py`

| ID | Scenario | Arrange | Act | Assert |
|----|----------|---------|-----|--------|
| C-AUDIT-001 | Every scrape writes audit log | Mock successful scrape | Scrape URL | Log entry exists with required fields |
| C-AUDIT-002 | Log is append-only | Attempt to delete/modify entry | Call API | Operation rejected or not implemented |
| C-AUDIT-003 | Hash chain links entries | Write two entries | Read entries | Entry 2 `previous_event_hash` == hash(entry 1) |
| C-AUDIT-004 | Tampering detected | Write entry; corrupt file externally | Verify chain | Verification fails; corrupted entries reported |
| C-AUDIT-005 | No secrets in audit log | Scrape with cookies | Inspect log | Cookie values absent; only domain/count/usage flags |
| C-AUDIT-006 | Retention policy deletes old logs | Set retention to 1 day; advance clock | Run cleanup | Entries older than 1 day removed |
| C-AUDIT-007 | Error scrapes still logged | Trigger `ChallengeDetectedError` | Scrape URL | Log entry status `error`; error_type recorded |

---

## 6. Credential Encryption Tests

**File**: `tests/compliance/test_credential_encryption.py`

| ID | Scenario | Arrange | Act | Assert |
|----|----------|---------|-----|--------|
| C-CRYPT-001 | Cookies encrypted at rest | Import Chrome cookie JSON | Inspect storage file | Content not plaintext; AES-256-GCM header present |
| C-CRYPT-002 | Decryption with wrong passphrase fails | Encrypt cookie jar; use wrong key | Decrypt | Decryption error; no plaintext leaked |
| C-CRYPT-003 | No password storage | Attempt to persist password | Persist | Operation rejected; only session cookies allowed |
| C-CRYPT-004 | Key derivation uses salt | Same passphrase, two imports | Inspect storage | Different ciphertext due to random salt |
| C-CRYPT-005 | Cookie listing hides values | `phoenix cookies list` | Run command | Output shows domain/count/expiry; no values |
| C-CRYPT-006 | Cookie removal deletes data | Remove domain cookies | Inspect storage | No trace of removed cookies |

---

## 7. Test Data and Fixtures

Provide the following fixtures in `tests/compliance/conftest.py`:

```python
@pytest.fixture
def mock_public_article_html() -> str:
    """Valid public article HTML with schema.org markup."""

@pytest.fixture
def mock_private_instagram_html() -> str:
    """Instagram page indicating a private account."""

@pytest.fixture
def mock_captcha_page_html() -> str:
    """HTML containing a Google reCAPTCHA widget."""

@pytest.fixture
def mock_robots_txt_disallow() -> str:
    """robots.txt disallowing /private/."""

@pytest.fixture
def temp_audit_log(tmp_path) -> Path:
    """Temporary audit log directory."""

@pytest.fixture
def temp_cookie_store(tmp_path) -> Path:
    """Temporary encrypted cookie store."""
```

---

## 8. CI Integration

- Compliance tests run on every PR.
- Compliance tests must pass with ≥85% coverage of the `phoenix_engine.compliance` module.
- No live platform calls in CI; use mocked HTML/HTTP responses.
- Add a CI job `compliance-gate` that runs:

```bash
pytest tests/compliance/ -v --cov=phoenix_engine.compliance --cov-report=term-missing --cov-fail-under=85
```

---

## 9. Traceability to Quality Gates

| Test File | Compliance Gate | Security Gate |
|-----------|-----------------|---------------|
| `test_public_data_only.py` | CG-1, CG-9 | SG-7 (input validation) |
| `test_rate_limit.py` | CG-2 | — |
| `test_user_agent.py` | CG-5, CG-10 | SG-6 |
| `test_audit_log.py` | CG-6, CG-7, CG-8 | — |
| `test_credential_encryption.py` | CG-4 | SG-6 |
