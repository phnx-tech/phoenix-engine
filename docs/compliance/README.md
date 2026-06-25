# Phoenix Engine — Compliance Documentation

**Maintainer**: AI-CO-01 (Compliance Officer)  
**Status**: Phase 0 Draft  
**Version**: 1.0

This directory contains the compliance framework artifacts that guide the engineering team for Phoenix Engine v1.0.

---

## Documents

| Document | Purpose | Primary Audience |
|----------|---------|------------------|
| [COMPLIANCE-001-public-data-only.md](COMPLIANCE-001-public-data-only.md) | Defines "public data only", detection/rejection gates, and user disclaimers | Backend Engineers, QA, Legal |
| [PLATFORM-TOS-SUMMARY.md](PLATFORM-TOS-SUMMARY.md) | Per-platform ToS risk summary and recommended mitigations | Backend Engineers, Product, Legal |
| [ETHICAL-GUARDRAILS.md](ETHICAL-GUARDRAILS.md) | Enforceable rules for UA transparency, rate limits, prohibited behaviors, audit logs, and GDPR/CCPA | Backend Engineers, DevOps, QA |
| [COMPLIANCE-TEST-PLAN.md](COMPLIANCE-TEST-PLAN.md) | pytest test scenarios for compliance gates | QA, Backend Engineers |

---

## Quick Reference: Compliance Gates

These documents support the compliance activities defined in:

- [12-definition-of-done.md](../../12-definition-of-done.md) §2.4 Phase 2 Entry Criterion **P2-E3** (platform-specific compliance briefs)
- [12-definition-of-done.md](../../12-definition-of-done.md) §3.3 Phase 2 Exit Criterion **P2-X8** (compliance review per adapter)
- [12-definition-of-done.md](../../12-definition-of-done.md) §4.5 **Compliance Gate** CG-1–CG-10
- [12-definition-of-done.md](../../12-definition-of-done.md) §4.3 **Security Gate** SG-6, SG-7

---

## Related Project Documents

- [01-project-charter.md](../../01-project-charter.md) — scope, out-of-scope, legal constraints
- [05-product-requirements.md](../../05-product-requirements.md) — compliance NFRs and feature requirements
- [10-risk-management.md](../../10-risk-management.md) — legal, compliance, and operational risks
- [12-definition-of-done.md](../../12-definition-of-done.md) — quality gates and sign-off criteria
