# Communication & Collaboration Plan: Phoenix Engine

## Universal Data Collection Platform — AI-Agent Team Coordination Protocol

---

| **Field** | **Value** |
|-----------|-----------|
| **Project** | Phoenix Engine |
| **Document** | Communication & Collaboration Plan |
| **Version** | 1.0 |
| **Date** | July 2025 |
| **Classification** | Confidential — Internal Use Only |
| **Owner** | AI Project Manager (AI-PM-01) |
| **Approver** | Human Product Owner (Human-PO-01) |
| **Review Cycle** | Bi-weekly during active phases; monthly during maintenance |

---

## 1. Communication Philosophy

### 1.1 Core Principles

The Phoenix Engine project operates on a hybrid AI-human team model. Effective collaboration between 9 AI agents and 3 human stakeholders requires explicitly designed communication protocols. The following principles govern all project interactions:

| **Principle** | **Description** | **Implementation** |
|---------------|-----------------|-------------------|
| **Async-First** | All agent communication is asynchronous by default. No agent waits for another in real-time. | GitHub issues, PR comments, ADRs, and status files. No chat or synchronous meetings between agents. |
| **Write It Down** | Every decision, status update, and handoff is documented in a durable, searchable format. | All outputs in Markdown; committed to repository; cross-referenced. |
| **Transparent by Default** | All agent work, reasoning, and decisions are visible to all other agents unless explicitly restricted. | Open GitHub repo; shared project board; public ADRs. |
| **Human-in-the-Loop at Gates** | AI agents execute autonomously within phases; humans approve at phase gates and legal/compliance touchpoints. | Defined gate criteria; human approval required for go/no-go decisions. |
| **Conflict Resolution by Escalation** | Disagreements between agents escalate through defined levels rather than persisting indefinitely. | 24h → 48h → 72h escalation chain. |
| **Minimal Viable Communication** | Every message must contain sufficient context for the recipient to act without requesting clarification. | Templates for all communication types; context-including conventions. |

### 1.2 Agent Collaboration Model

AI agents on the Phoenix Engine team are not independent contractors — they are specialized functions within a unified delivery system. Each agent:

- **Reads** the project charter and phase plan as primary context
- **Writes** all outputs to the shared repository
- **Notifies** relevant agents through structured handoff documents
- **Escalates** blockers, disagreements, and out-of-scope requests through defined channels
- **Respects** human approval gates without override

### 1.3 Communication Taxonomy

| **Type** | **Purpose** | **Channel** | **Retention** | **Audience** |
|----------|-------------|-------------|---------------|--------------|
| Status Update | Progress reporting | Status file in repo + GitHub issue comment | Permanent | AI-PM, AI-TL, Human-PO |
| Decision Record | Architecture/technical decisions | ADR in `/docs/architecture/` | Permanent | All agents |
| Task Handoff | Work transfer between agents | Handoff doc + PR description | Permanent | Sender + Receiver |
| Code Review | Quality assurance | GitHub PR review | Permanent | AI-TL, relevant BE |
| Bug Report | Issue documentation | GitHub issue | Permanent | AI-QA, relevant BE |
| Risk Alert | Risk notification | GitHub issue + status file | Permanent | AI-PM, Human-PO |
| Compliance Query | Legal/compliance question | GitHub issue tagged `compliance` | Permanent | AI-CO, Human-LC |
| Human Request | Human-to-agent instruction | GitHub issue or ADR comment | Permanent | Specified agent |
| Gate Approval | Phase transition authorization | Gate checklist + signed approval | Permanent | Gate approver |

---

## 2. Agent Interaction Protocols

### 2.1 How the PM Agent Coordinates Dev Agents

The AI Project Manager (AI-PM-01) is the coordination hub. All development agents report status to and receive direction from the PM agent.

#### Coordination Workflow

```
AI-PM-01                    AI-BE-01/02/03
    │                            │
    ├─ 1. Task Assignment ──────►│
    │   (GitHub issue with       │
    │    context, criteria,      │
    │    deadline)               │
    │                            │
    │◄─ 2. Ack + Questions ─────┤
    │   (Within 2 hours)        │
    │                            │
    ├─ 3. Clarification ───────►│
    │   (If needed)              │
    │                            │
    │◄─ 4. Status Updates ──────┤
    │   (Daily, in status file)  │
    │                            │
    │◄─ 5. Completion + Handoff ─┤
    │   (PR + handoff doc)       │
    │                            │
    ├─ 6. Review Assignment ───►│ AI-TL-01 / AI-QA-01
    │                            │
    │◄─ 7. Review Complete ─────┤
    │                            │
    ├─ 8. Merge / Iterate ─────►│
```

#### Task Assignment Format

Every task assigned by AI-PM-01 must include:

```markdown
## Task Assignment

**Task ID**: T-XXX
**Assignee**: [Agent ID]
**Priority**: P0 / P1 / P2
**Due**: YYYY-MM-DD
**Phase**: Phase X

### Context
[2-3 sentences of background — why this task matters]

### Requirements
- [Specific requirement 1]
- [Specific requirement 2]
- [Specific requirement 3]

### Acceptance Criteria
- [ ] Criterion 1 (measurable)
- [ ] Criterion 2 (measurable)
- [ ] Criterion 3 (measurable)

### Dependencies
- Depends on: [Task IDs]
- Blocks: [Task IDs]

### References
- ADR: [link if applicable]
- Related issues: [links]
- Documentation: [links]
```

#### Daily Status Update Format

Each dev agent submits a daily status update to `/status/[agent-id]-YYYY-MM-DD.md`:

```markdown
## Status Update: [Agent Name] — YYYY-MM-DD

### Yesterday
- [Completed item with issue/PR reference]
- [Completed item with issue/PR reference]

### Today
- [Planned item]
- [Planned item]

### Blockers
- [None / Description with escalation level]

### Risks
- [None / Description with mitigation]

### Need Help From
- [No one / Agent ID — reason]
```

### 2.2 How the Tech Lead Reviews Architecture Decisions

The AI Tech Lead (AI-TL-01) owns all architecture decisions and code quality. Every significant technical decision flows through the ADR process.

#### Decision Types Requiring Tech Lead Review

| **Decision Type** | **Examples** | **Process** | **SLA** |
|-------------------|-------------|-------------|---------|
| Architecture pattern | Module structure, interface design, data flow | ADR required | 24h review |
| Dependency addition | New library, service, or tool | ADR update + security review | 24h review |
| API design | Public function signatures, CLI commands | ADR + code review | 24h review |
| Implementation approach | Algorithm choice, extraction strategy | Code review + optional ADR | 24h review |
| Refactoring | Structural code changes | PR review | 24h review |
| Performance optimization | Caching, concurrency, async patterns | PR review + benchmark | 24h review |

#### Architecture Decision Record (ADR) Process

```
1. Proposal
   Any agent identifies need for architectural decision
   │
   ▼
2. Draft ADR
   Author creates ADR following template
   Location: /docs/architecture/ADR-XXX-title.md
   │
   ▼
3. Peer Review (24h)
   AI-TL-01 reviews; consults affected agents
   │
   ▼
4. Revision (if needed)
   Author addresses feedback
   │
   ▼
5. Approval
   AI-TL-01 approves; Human-PO informed if >5% scope impact
   │
   ▼
6. Implementation
   Decision executed; ADR marked "Accepted"
   │
   ▼
7. Deprecation (if needed)
   If superseded, ADR marked "Deprecated" with reference to successor
```

#### ADR Template

```markdown
# ADR-XXX: [Title]

| **Field** | **Value** |
|-----------|-----------|
| **Status** | Proposed / Accepted / Deprecated |
| **Date** | YYYY-MM-DD |
| **Author** | [Agent ID] |
| **Decider** | AI-TL-01 |

## Context
[What is the problem we're solving?]

## Decision
[What did we decide? Be specific.]

## Consequences
### Positive
- [Benefit 1]
- [Benefit 2]

### Negative / Risks
- [Risk 1]
- [Risk 2]

## Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| [Alt 1] | ... | ... | ... |
| [Alt 2] | ... | ... | ... |

## Compliance Impact
[GDPR, CCPA, ToS implications — reviewed by AI-CO-01]

## References
- [Links to related ADRs, issues, docs]
```

### 2.3 How the QA Agent Integrates with Dev Agents

The AI QA Lead (AI-QA-01) is not a final gate — it is an integrated quality function that works alongside development throughout every phase.

#### QA Integration Model

| **Phase** | **QA Activity** | **QA Output** | **Dev Collaboration** |
|-----------|----------------|---------------|----------------------|
| Phase 0 | Test framework setup; standards definition | Test infrastructure; coverage policy | Review with AI-TL-01 |
| Phase 1 | Core engine test design; pipeline integration tests | Test suite; test data | Pair with AI-BE-01 |
| Phase 2 | Adapter test design; mocking strategy; integration tests | Per-adapter tests; mock fixtures | Pair with AI-BE-02, AI-BE-03 |
| Phase 3 | AI output validation; cost tracking tests | Validation suite; token budget tests | Pair with AI-BE-01 |
| Phase 4 | Infrastructure tests; security test cases | Storage tests; encryption tests | Pair with AI-DO-01 |
| Phase 5 | DX walkthrough testing; docs accuracy test | Walkthrough script; doc review | Pair with AI-BE-01, AI-TW-01 |
| Phase 6 | Performance testing; security audit; compliance check | Benchmarks; audit reports | Independent; reports to all |
| Phase 7 | Install validation; release verification | Validation report | Pair with AI-DO-01 |

#### QA Agent Communication Protocol

When AI-QA-01 finds an issue:

1. **Document** in GitHub issue using bug report template
2. **Classify** severity: P0 (blocking), P1 (significant), P2 (minor)
3. **Route** to responsible dev agent via issue assignment
4. **Track** in QA dashboard until resolved
5. **Verify** fix before issue closure

#### Bug Report Template

```markdown
## Bug Report: [Brief Title]

**Severity**: P0 / P1 / P2
**Component**: [Module/Adapter]
**Reporter**: AI-QA-01
**Assigned**: [Dev Agent ID]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Environment
- Python version:
- OS:
- Commit hash:

### Logs / Output
```
[Relevant log output]
```

### Acceptance Criteria for Fix
- [ ] Criterion 1
- [ ] Criterion 2
```

### 2.4 How the Compliance Agent Audits Throughout

The AI Compliance Officer (AI-CO-01) conducts continuous compliance review rather than a single audit at the end.

#### Compliance Review Touchpoints

| **Touchpoint** | **When** | **What is Reviewed** | **Output** |
|----------------|----------|---------------------|------------|
| Architecture review | Every ADR | Data handling, storage, transmission implications | Compliance comment on ADR |
| Code review | Every PR | Data minimization, logging of PII, credential handling | PR compliance check |
| Adapter review | Phase 2 | Per-platform ToS compliance, public-only extraction | Adapter compliance report |
| AI feature review | Phase 3 | Prompt data handling, retention, model provider ToS | AI ethics review |
| Infrastructure review | Phase 4 | Encryption, key management, retention policies | Security review |
| Final audit | Phase 6 | Comprehensive GDPR/CCPA/ToS compliance | Compliance certification |
| Ongoing | Post-launch | Dependency vulnerabilities, platform ToS changes | Weekly compliance check |

#### Compliance Agent Authority

- **Can block**: Any PR that introduces compliance violations
- **Must escalate**: To Human Legal Counsel if uncertainty exists
- **Cannot override**: Human Legal Counsel decisions
- **Must document**: All compliance findings in `/compliance/` directory

---

## 3. Meeting Rhythms

All project "meetings" are asynchronous structured exchanges unless explicitly noted as synchronous.

### 3.1 Daily AI Standup (Automated Status Sync)

| **Attribute** | **Value** |
|---------------|-----------|
| **Frequency** | Daily, 00:00 UTC |
| **Duration** | N/A (async) |
| **Participants** | All AI agents |
| **Format** | Status file update |
| **Owner** | AI-PM-01 (aggregation) |

**Process:**
1. Each agent updates their status file by 00:00 UTC
2. AI-PM-01 aggregates into `/status/daily-YYYY-MM-DD.md`
3. AI-PM-01 identifies blockers, risks, and coordination needs
4. AI-PM-01 creates/routes issues for any blockers
5. Human-PO receives daily summary (high-level only)

**Daily Summary Format:**

```markdown
## Daily Standup Summary — YYYY-MM-DD

### Phase Status
| Phase | Status | % Complete | Risk Level |
|-------|--------|------------|------------|
| [Phase] | [On Track / At Risk / Blocked] | [X%] | [Green/Yellow/Red] |

### Completed Yesterday
- [Item with agent and reference]

### Planned Today
- [Item with agent and reference]

### Blockers
| Agent | Blocker | Severity | Action | ETA |
|-------|---------|----------|--------|-----|
| [ID] | [Description] | [P0/P1] | [Action] | [ETA] |

### Risks
| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| [Description] | [High/Med/Low] | [High/Med/Low] | [Action] | [Agent] |

### Human Attention Needed
- [Item with context and decision needed]
```

### 3.2 Phase Gate Reviews (Entry/Exit Criteria Checklist)

| **Attribute** | **Value** |
|---------------|-----------|
| **Frequency** | At each phase transition (M0 through M8) |
| **Duration** | 24-48 hours for review cycle |
| **Participants** | All AI agents + Human PO (approver) + relevant human stakeholders |
| **Format** | Structured checklist review |
| **Owner** | AI-PM-01 (coordination); Human-PO-01 (approval) |

**Process:**
1. AI-PM-01 prepares gate checklist 48 hours before scheduled gate
2. Responsible agents submit evidence for their criteria
3. AI-QA-01 verifies test/coverage evidence
4. AI-CO-01 verifies compliance evidence
5. AI-TL-01 verifies technical evidence
6. Human-PO reviews complete package
7. Human-PO approves (PROCEED), conditions (PROCEED WITH NOTES), or rejects (REMEDIATE)

**Gate Decision Options:**

| **Decision** | **Meaning** | **Next Action** |
|--------------|-------------|-----------------|
| **PROCEED** | All criteria met; phase transition approved | Begin next phase immediately |
| **PROCEED WITH NOTES** | Minor gaps acceptable; documented remediation plan | Begin next phase; address notes in parallel |
| **REMEDIATE** | Significant gaps; phase transition blocked | Return to current phase; fix gaps; re-review |

### 3.3 Architecture Decision Records (ADR Process)

See Section 2.2 for detailed ADR process.

| **Attribute** | **Value** |
|---------------|-----------|
| **Frequency** | As needed (when architectural decision required) |
| **Duration** | 24-48 hour review cycle |
| **Participants** | Author + AI-TL-01 (decider) + consulted agents |
| **Format** | Markdown ADR document |
| **Owner** | AI-TL-01 |

### 3.4 Risk Review Sessions

| **Attribute** | **Value** |
|---------------|-----------|
| **Frequency** | Weekly (Monday 00:00 UTC) |
| **Duration** | Async; AI-PM-01 aggregates within 4 hours |
| **Participants** | AI-PM-01, AI-TL-01, Human-PO |
| **Format** | Risk register update + review |
| **Owner** | AI-PM-01 |

**Process:**
1. AI-PM-01 reviews all open risks from risk register
2. Each risk owner updates their risk status
3. AI-PM-01 assesses new risks identified in past week
4. AI-PM-01 produces risk summary with recommended actions
5. Human-PO reviews high-impact risks
6. Risk register updated in repository

**Risk Register Format:**

```markdown
| ID | Risk | Probability | Impact | Score | Owner | Status | Mitigation | Contingency |
|----|------|-------------|--------|-------|-------|--------|------------|-------------|
| R1 | [Description] | H/M/L | H/M/L | [1-9] | [Agent] | Open/Mitigated/Closed | [Action] | [Plan] |
```

*Score = Probability × Impact (1-3 scale each). Score ≥6 requires Human-PO notification.*

---

## 4. Handoff Procedures

### 4.1 Between Phases

Phase handoffs are the most critical coordination moments. Each handoff follows this protocol:

```
Phase N Complete
    │
    ▼
1. Exit criteria evidence collected
   (AI-PM-01 coordinates collection)
    │
    ▼
2. Gate review initiated
   (AI-PM-01 opens gate review issue)
    │
    ▼
3. Agent evidence submissions
   (Each responsible agent submits proof)
    │
    ▼
4. QA verification
   (AI-QA-01 validates all test evidence)
    │
    ▼
5. Compliance verification
   (AI-CO-01 validates compliance evidence)
    │
    ▼
6. Human PO review
   (Human-PO-01 reviews complete package)
    │
    ▼
7. Gate decision
   PROCEED / PROCEED WITH NOTES / REMEDIATE
    │
    ▼
Phase N+1 Begins
   (Entry criteria verified; tasks assigned)
```

#### Phase Handoff Document Template

```markdown
# Phase Handoff: [Phase N] → [Phase N+1]

**Date**: YYYY-MM-DD
**Gate Decision**: [PROCEED / PROCEED WITH NOTES / REMEDIATE]
**Decision Maker**: [Approver]

## Phase N Summary
- Duration: [Planned vs Actual]
- Deliverables: [X/Y completed]
- Budget: [Planned vs Actual]

## Exit Criteria Evidence
| Criterion | Status | Evidence | Verifier |
|-----------|--------|----------|----------|
| [EC1] | ✅/❌ | [Link] | [Agent] |

## Remediation Items (if any)
| Item | Owner | Due Date | Severity |
|------|-------|----------|----------|
| [Item] | [Agent] | [Date] | [P1/P2] |

## Phase N+1 Entry Criteria
| Criterion | Status | Notes |
|-----------|--------|-------|
| [Entry criteria] | ✅/❌ | [Notes] |

## Key Context for Phase N+1
[Critical information the next phase team needs to know]

## Known Risks
| Risk | Mitigation | Owner |
|------|------------|-------|
| [Risk] | [Action] | [Agent] |

## Task Assignments
| Task | Assignee | Due Date |
|------|----------|----------|
| [Task] | [Agent] | [Date] |
```

### 4.2 Between Agent Roles

When work transfers from one agent to another:

#### Handoff Types

| **Type** | **Trigger** | **From** | **To** | **Handoff Doc Required** |
|----------|-------------|----------|--------|--------------------------|
| Dev → QA | Implementation complete | AI-BE-* | AI-QA-01 | Yes |
| QA → Dev | Bug fix needed | AI-QA-01 | AI-BE-* | Yes (bug report) |
| Dev → Tech Lead | Architecture review needed | AI-BE-* | AI-TL-01 | Yes (PR) |
| Any → Compliance | Compliance question | Any | AI-CO-01 | Yes (tagged issue) |
| Compliance → Legal | Legal escalation | AI-CO-01 | Human-LC-01 | Yes (formal memo) |
| Any → TW | Documentation needed | Any | AI-TW-01 | Yes (context doc) |
| TW → Review | Docs ready for review | AI-TW-01 | Human-PO/DR | Yes (PR) |

#### Agent-to-Agent Handoff Template

```markdown
## Handoff: [From Agent] → [To Agent]

**Date**: YYYY-MM-DD
**Task**: [Task ID and brief description]
**Priority**: P0/P1/P2

### What Was Done
[Summary of completed work]

### Current State
[Where things stand — what's working, what's not]

### Key Decisions Made
- [Decision 1 with rationale]
- [Decision 2 with rationale]

### Known Issues / Technical Debt
- [Issue 1 — severity and context]
- [Issue 2 — severity and context]

### Next Steps Required
1. [Step 1 — with acceptance criteria]
2. [Step 2 — with acceptance criteria]

### References
- Code: [File paths]
- Tests: [Test paths]
- Docs: [Doc paths]
- ADRs: [ADR references]
- Issues: [GitHub issue links]

### Questions for Recipient
[Any specific questions the recipient needs to answer]
```

---

## 5. Escalation Matrix

### 5.1 Escalation Triggers

An escalation is triggered when any of the following conditions are met:

| **Trigger** | **Severity** | **Auto-Notify** |
|-------------|--------------|-----------------|
| Phase exit criteria not met by deadline | High | AI-PM-01, Human-PO-01 |
| Security vulnerability discovered | Critical | AI-CO-01, Human-LC-01, Human-PO-01 |
| Legal/compliance violation suspected | Critical | AI-CO-01, Human-LC-01, Human-PO-01 |
| Budget overrun >10% | High | AI-PM-01, Human-PO-01 |
| Agent disagreement unresolved >24h | Medium | AI-PM-01 |
| Agent disagreement unresolved >48h | High | AI-PM-01, Human-PO-01 |
| Platform blocks extraction (production) | Critical | AI-PM-01, AI-TL-01, Human-PO-01 |
| P0 bug open >24h | High | AI-QA-01, assigned AI-BE-*, AI-PM-01 |
| Human approval needed >48h SLA | Medium | AI-PM-01, Human-PO-01 |
| Scope change request received | Medium | AI-PM-01, Human-PO-01 |

### 5.2 Escalation Levels

```
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 1: Agent-to-Agent (0-24 hours)                       │
│                                                             │
│ Trigger: Disagreement, question, or minor blocker           │
│ Action: Direct communication between agents via GitHub      │
│         issues or PR comments                               │
│ Resolver: The agents involved                               │
│                                                             │
│ If unresolved → escalate to Level 2                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 2: AI PM Mediation (24-48 hours)                     │
│                                                             │
│ Trigger: Level 1 unresolved; or medium-impact issue         │
│ Action: AI-PM-01 intervenes; gathers context; decides or    │
│         assigns resolution path                             │
│ Resolver: AI-PM-01                                          │
│                                                             │
│ If unresolved → escalate to Level 3                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 3: Human PO Decision (48-72 hours)                   │
│                                                             │
│ Trigger: Level 2 unresolved; or high-impact issue           │
│ Action: Human-PO-01 reviews full context; makes decision    │
│         or delegates with authority                         │
│ Resolver: Human-PO-01                                       │
│                                                             │
│ If unresolved → escalate to Level 4                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 4: Steering Committee (72+ hours)                    │
│                                                             │
│ Trigger: Level 3 unresolved; or strategic impact            │
│ Action: Full Steering Committee review (Human PO + Legal +  │
│         DevRel + AI PM + AI TL)                             │
│ Resolver: Steering Committee consensus                      │
│                                                             │
│ If unresolved → Level 5 (Executive Override)               │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Escalation Response SLA

| **Level** | **Response Time** | **Resolution Target** | **Communication** |
|-----------|-------------------|----------------------|-------------------|
| Level 1 | Immediate (async) | 24 hours | GitHub issue/PR |
| Level 2 | Within 4 hours | 48 hours | GitHub issue + status update |
| Level 3 | Within 24 hours | 72 hours | Direct notification to Human-PO |
| Level 4 | Within 48 hours | 1 week | Meeting convened by AI-PM |

---

## 6. Documentation Update Cadence

### 6.1 Documentation Types and Refresh Schedules

| **Document** | **Owner** | **Update Trigger** | **Max Age** | **Location** |
|--------------|-----------|-------------------|-------------|--------------|
| Project Charter | AI-PM-01 | Scope change; monthly review | 1 month | `/docs/charter.md` |
| Phases & Milestones | AI-PM-01 | Phase transition; weekly review | 1 week | `/docs/phases-milestones.md` |
| Communication Plan | AI-PM-01 | Process change; bi-weekly review | 2 weeks | `/docs/communication-plan.md` |
| Architecture Decision Records | AI-TL-01 | New decision; deprecated decision | N/A (append-only) | `/docs/architecture/ADR-*.md` |
| API Documentation | AI-TW-01 | API change; release | 1 release | `/docs/api/` |
| README | AI-TW-01 | Feature change; release | 1 release | `/README.md` |
| Quick-Start Guide | AI-TW-01 | UX change; release | 1 release | `/docs/quickstart.md` |
| Coding Standards | AI-TL-01 | Standards change | 3 months | `/docs/development/standards.md` |
| Compliance Checklists | AI-CO-01 | Regulation change; audit | 3 months | `/compliance/` |
| Risk Register | AI-PM-01 | Weekly risk review | 1 week | `/docs/risk-register.md` |
| Status Updates | All agents | Daily | 1 day | `/status/` |
| Test Reports | AI-QA-01 | Per test run | Per run | `/reports/` |

### 6.2 Documentation Update Protocol

When any agent updates a document:

1. **Edit** the document in a feature branch
2. **Version** the document (increment version number)
3. **Summarize** changes in commit message
4. **PR** the change for review (owner reviews)
5. **Notify** affected agents of significant changes
6. **Archive** previous version in `/docs/archive/` (for major docs)

### 6.3 Documentation Quality Standards

| **Standard** | **Requirement** | **Verifier** |
|--------------|----------------|--------------|
| Accuracy | All code examples must be tested and working | AI-QA-01 |
| Completeness | All public APIs documented | AI-TW-01 |
| Clarity | Flesch Reading Ease score ≥50 for user docs | AI-TW-01 |
| Currency | No references to deprecated features | AI-TL-01 |
| Consistency | Terminology matches glossary | AI-TW-01 |
| Accessibility | All images have alt text; logical heading structure | AI-TW-01 |

---

## 7. Artifact Storage

### 7.1 Repository Structure

```
phoenix-engine/
├── .github/
│   ├── workflows/           # CI/CD configurations
│   └── ISSUE_TEMPLATE/      # Issue templates
├── src/
│   └── phoenix/             # Source code
├── tests/                   # Test suites
│   ├── unit/
│   ├── integration/
│   ├── performance/
│   └── dx/
├── docs/                    # Documentation
│   ├── architecture/        # ADRs
│   ├── development/         # Dev guides
│   ├── features/            # Feature docs
│   ├── infrastructure/      # Infra docs
│   ├── api/                 # API reference
│   └── archive/             # Archived docs
├── compliance/              # Compliance docs
│   ├── gdpr/
│   ├── ccpa/
│   └── tos/
├── reports/                 # Generated reports
│   ├── performance/
│   ├── security/
│   └── quality/
├── status/                  # Daily status updates
├── schemas/                 # JSON schemas
├── scripts/                 # Utility scripts
├── examples/                # Example code
│   └── plugin/              # Example plugin
├── CHANGELOG.md             # Release notes
├── README.md                # Project overview
├── pyproject.toml           # Package config
└── LICENSE                  # License
```

### 7.2 Naming Conventions

| **Artifact Type** | **Naming Pattern** | **Example** |
|-------------------|---------------------|-------------|
| ADR | `ADR-NNN-short-title.md` | `ADR-001-core-architecture.md` |
| Status file | `[agent-id]-YYYY-MM-DD.md` | `AI-BE-01-2025-07-15.md` |
| Test file | `test_[module].py` | `test_receiver.py` |
| Report | `[type]-YYYY-MM-DD.md` | `performance-2025-07-15.md` |
| Compliance doc | `[regulation]-[topic].md` | `gdpr-data-retention.md` |
| Release notes | `CHANGELOG.md` (single file, versioned entries) | — |
| Bug report | GitHub issue number (auto-assigned) | `#42` |

### 7.3 Storage Policies

| **Policy** | **Rule** | **Owner** |
|------------|----------|-----------|
| All code in GitHub | Single source of truth; no code outside repo | AI-DO-01 |
| All docs in repo | Documentation versioned with code | AI-TW-01 |
| Status files 30 days | Daily status files archived after 30 days | AI-DO-01 |
| Reports retained | All reports kept for project duration | AI-PM-01 |
| Compliance docs permanent | Regulatory docs kept indefinitely | AI-CO-01 |
| Issues never deleted | Closed issues remain for audit trail | AI-PM-01 |

---

## 8. Human-in-the-Loop Touchpoints

### 8.1 Mandatory Human Approval Gates

The following decisions **require** explicit human approval. AI agents cannot proceed without sign-off.

| **Touchpoint** | **When** | **Approver** | **SLA** | **Escalation if Missed** |
|----------------|----------|-------------|---------|--------------------------|
| Project kickoff | Week 1 start | Human-PO-01 | 24 hours | Project start delayed |
| Architecture lock | End of Phase 0 | Human-PO-01 + AI-TL-01 | 48 hours | Phase 0 extended |
| Adapter scope confirmation | Week 6 | Human-PO-01 | 24 hours | Adapter development paused |
| Legal/compliance sign-off | Phase 6 | Human-LC-01 | 48 hours | Launch blocked |
| Release go/no-go | Week 18 | Human-PO-01 + AI-QA-01 | 24 hours | Launch delayed |
| Launch announcement | Week 18 | Human-PO-01 + Human-DR-01 | 24 hours | Announcement delayed |
| Scope change (P0) | Any time | Human-PO-01 | 48 hours | Change rejected by default |
| Budget draw on contingency | Any time | Human-PO-01 | 24 hours | Spend rejected |
| External dependency addition | Any time | Human-PO-01 + AI-TL-01 | 48 hours | Dependency rejected |
| Public communications | Any time | Human-DR-01 + Human-PO-01 | 24 hours | Communication blocked |

### 8.2 Human Notification Triggers

Humans are notified (but approval not required) for:

| **Event** | **Notify** | **Channel** | **Timing** |
|-----------|-----------|-------------|------------|
| Phase transition | Human-PO-01 | Email + status file mention | Within 4 hours of gate decision |
| Daily summary | Human-PO-01 | Status file + email digest | Daily 06:00 UTC |
| Risk score ≥6 | Human-PO-01 | Immediate email | Within 1 hour of identification |
| Security finding | Human-LC-01 + Human-PO-01 | Immediate email | Within 1 hour of discovery |
| Budget status | Human-PO-01 | Weekly email | Monday 06:00 UTC |
| Compliance issue | Human-LC-01 | Immediate email | Within 1 hour of discovery |
| Milestone achieved | Human-PO-01 + Human-DR-01 | Email + status update | Within 4 hours |
| Community activity | Human-DR-01 | Weekly digest | Friday 06:00 UTC |

### 8.3 Human-to-Agent Instruction Protocol

When humans need to instruct AI agents:

1. **Create a GitHub issue** with the `human-request` label
2. **Include context**: What, why, and any constraints
3. **Tag the responsible agent** (or AI-PM-01 for routing)
4. **Specify priority**: P0 (urgent), P1 (normal), P2 (when convenient)
5. **AI-PM-01 confirms receipt** within 2 hours
6. **Assigned agent executes** and updates issue with progress
7. **Human reviews** output and closes issue or requests iteration

**Human Request Template:**

```markdown
## Human Request

**From**: [Human name/role]
**To**: [Agent ID or "AI-PM for routing"]
**Priority**: P0 / P1 / P2
**Due**: [Date or "none"]

### Request
[Clear description of what is needed]

### Context
[Why this is needed; background information]

### Constraints
- [Constraint 1]
- [Constraint 2]

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

### References
[Links, screenshots, or attachments]
```

---

## 9. Conflict Resolution

### 9.1 Types of Agent Disagreements

| **Type** | **Example** | **Resolution Path** |
|----------|-------------|---------------------|
| Technical approach | Two implementation options | AI-TL-01 decides; ADR documents rationale |
| Priority conflict | Which bug to fix first | AI-PM-01 decides based on impact/effort |
| Scope interpretation | Whether a feature is in-scope | Charter reference; AI-PM-01 decides; escalate to Human-PO if disputed |
| Code quality | Whether PR meets standards | AI-TL-01 decides; documented standards are reference |
| Compliance vs. velocity | Compliance requirement delays feature | AI-CO-01 has veto; Human-LC-01 mediates if disputed |
| Resource allocation | Which agent works on what | AI-PM-01 decides based on skills and load |

### 9.2 Conflict Resolution Protocol

```
Conflict Identified
    │
    ▼
1. Direct Discussion (0-12h)
   Disagreeing agents discuss via GitHub issue
   Goal: Reach consensus
   │
   ├── Resolved → Document decision, close conflict
   │
   └── Unresolved →
       │
       ▼
2. AI-PM-01 Mediation (12-24h)
   AI-PM-01 gathers context, proposes resolution
   Goal: Binding mediation
   │
   ├── Accepted → Document decision, close conflict
   │
   └── Rejected →
       │
       ▼
3. AI-TL-01 Technical Authority (24-36h)
   For technical conflicts: AI-TL-01 decides
   For non-technical: AI-PM-01 decides
   Goal: Executive decision at AI level
   │
   ├── Accepted → Document in ADR or decision log
   │
   └── Escalated →
       │
       ▼
4. Human-PO-01 Decision (36-72h)
   Human Product Owner makes final decision
   Goal: Irrevocable resolution
   │
   └── Decision logged; all agents comply
```

### 9.3 Compliance Override Protocol

Compliance conflicts have special handling:

- **AI-CO-01 can block** any work that violates compliance requirements
- **If AI-CO-01 and another agent disagree**: Work remains blocked pending resolution
- **If AI-CO-01 is uncertain**: Escalate to Human-LC-01 within 4 hours
- **Human-LC-01 decision is final** on all legal/compliance matters
- **No agent may override** Human-LC-01 on compliance questions

### 9.4 Decision Log

All significant decisions (including conflict resolutions) are logged in `/docs/decisions/decision-log.md`:

```markdown
| Date | ID | Topic | Decision | Decider | Context |
|------|-----|-------|----------|---------|---------|
| YYYY-MM-DD | D-001 | [Topic] | [Decision] | [Agent/Role] | [Link to ADR or issue] |
```

---

## 10. Tools & Infrastructure

### 10.1 Tool Inventory

| **Category** | **Tool** | **Purpose** | **Owner** | **Access** |
|--------------|----------|-------------|-----------|------------|
| **Source Control** | GitHub | Code repository, issues, PRs, project board | AI-DO-01 | All agents + humans |
| **CI/CD** | GitHub Actions | Automated testing, linting, security scans, packaging | AI-DO-01 | All agents (read) |
| **Package Registry** | PyPI | Python package distribution | AI-DO-01 | AI-DO-01 (publish) |
| **Documentation** | MkDocs + GitHub Pages | Documentation site generation and hosting | AI-TW-01 | All agents (write) |
| **Project Board** | GitHub Projects | Task tracking, Kanban board | AI-PM-01 | All agents + humans |
| **Security Scanning** | Bandit + Safety + CodeQL | Static security analysis | AI-CO-01 | All agents (read) |
| **Compliance Tracking** | GitHub Issues (tagged) | Compliance review tracking | AI-CO-01 | All agents + humans |
| **Monitoring** | GitHub Insights + Custom | Project velocity, code quality trends | AI-PM-01 | All agents (read) |
| **Communication** | GitHub Issues + Email | All structured communication | AI-PM-01 | All agents + humans |

### 10.2 GitHub Project Board Configuration

| **Column** | **Purpose** | **Entry Criteria** | **Exit Criteria** |
|------------|-------------|-------------------|-------------------|
| **Backlog** | Unprioritized work | Issue created | Prioritized by AI-PM-01 |
| **To Do** | Prioritized, ready to start | Assignment + acceptance criteria clear | Agent self-assigns |
| **In Progress** | Actively being worked | Agent assigned; status updates daily | PR opened or handoff complete |
| **In Review** | Awaiting review | PR opened; all CI checks running | Reviewer approval obtained |
| **Compliance Review** | Compliance check required | AI-CO-01 tagged | AI-CO-01 approval obtained |
| **Ready to Merge** | Approved, awaiting merge | All reviews + compliance approved | Merged to main |
| **Done** | Complete | Merged to main | Archived after 30 days |

### 10.3 CI/CD Pipeline Stages

| **Stage** | **Trigger** | **Actions** | **Gate** |
|-----------|-------------|-------------|----------|
| Lint | Every PR/commit | ruff (lint + format), mypy (types) | Must pass |
| Unit Test | Every PR/commit | pytest unit tests, coverage report | Must pass, ≥70% coverage |
| Integration Test | Every PR to main | Full integration test suite | Must pass |
| Security Scan | Every PR to main | Bandit, Safety, CodeQL | Must pass (zero critical) |
| Build | Every tag | Build wheel + sdist | Must succeed |
| Docs Build | Every PR/commit | MkDocs build | Must succeed |
| Performance | Manual / scheduled | Benchmark suite | Report only (Phase 6 gate) |

### 10.4 Access Control Matrix

| **Resource** | **AI-PM-01** | **AI-TL-01** | **AI-BE-*** | **AI-DO-01** | **AI-QA-01** | **AI-CO-01** | **AI-TW-01** | **Human-PO-01** | **Human-LC-01** | **Human-DR-01** |
|--------------|:-----------:|:------------:|:-----------:|:------------:|:------------:|:------------:|:------------:|:---------------:|:---------------:|:---------------:|
| GitHub Repo (read) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| GitHub Repo (write) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Merge to main | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PyPI publish | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Issue assignment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Compliance veto | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅* | ❌ |
| Gate approval | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Release go/no-go | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |

*Human-LC-01 can override AI-CO-01 compliance decisions

### 10.5 Communication Channel Map

| **Channel** | **Used For** | **Response SLA** | **Archive** |
|-------------|-------------|-----------------|-------------|
| GitHub Issues | Tasks, bugs, features, requests | 4 hours (ack) | Permanent |
| GitHub PR Comments | Code review, technical discussion | 24 hours | Permanent |
| GitHub Discussions | Community engagement (post-launch) | 48 hours | Permanent |
| Status Files (`/status/`) | Daily agent status | Daily by 00:00 UTC | 30 days |
| ADRs (`/docs/architecture/`) | Architecture decisions | 24 hours (review) | Permanent |
| Email (human notifications) | Human alerts and summaries | N/A (push) | Email system |
| Repository (`/docs/`, `/reports/`) | All durable documentation | N/A | Permanent |

---

## 11. Communication Plan Maintenance

### 11.1 Plan Review Schedule

| **Trigger** | **Action** | **Owner** |
|-------------|-----------|-----------|
| Bi-weekly | Review plan effectiveness; collect feedback | AI-PM-01 |
| Phase transition | Assess if communication needs changed | AI-PM-01 |
| Process failure | Root cause analysis; plan update if needed | AI-PM-01 |
| Tool change | Update tool references and access | AI-DO-01 |
| Team change | Update role assignments and RACI | AI-PM-01 |

### 11.2 Plan Effectiveness Metrics

| **Metric** | **Target** | **Measurement** |
|------------|-----------|-----------------|
| Issue response time | ≤4 hours median | GitHub issue analytics |
| PR review turnaround | ≤24 hours median | GitHub PR analytics |
| Escalation resolution | ≤48 hours for Level 2 | Escalation log |
| Human SLA compliance | ≥95% responses within SLA | Human response tracking |
| Documentation freshness | 100% docs updated within max age | Documentation audit |
| Status update completeness | 100% agents submit daily | Status file check |

---

## Appendix A: Glossary

| **Term** | **Definition** |
|----------|---------------|
| ADR | Architecture Decision Record — documents significant technical decisions |
| Agent | AI-powered team member with defined role and responsibilities |
| BE | Backend Engineer agent |
| CI/CD | Continuous Integration / Continuous Deployment |
| CO | Compliance Officer agent |
| DO | DevOps Engineer agent |
| DX | Developer Experience |
| Gate | Phase transition review point with defined criteria |
| PM | Project Manager agent |
| QA | Quality Assurance agent |
| RACI | Responsibility matrix: Responsible, Accountable, Consulted, Informed |
| SLA | Service Level Agreement — commitment for response/resolution time |
| TL | Tech Lead agent |
| TW | Technical Writer agent |
| ToS | Terms of Service |

## Appendix B: Emergency Contacts

| **Role** | **ID** | **Escalation Path** |
|----------|--------|---------------------|
| AI Project Manager | AI-PM-01 | Human-PO-01 (Level 3) |
| AI Tech Lead | AI-TL-01 | AI-PM-01 → Human-PO-01 |
| AI Compliance Officer | AI-CO-01 | Human-LC-01 (Level 3) |
| Human Product Owner | Human-PO-01 | Steering Committee (Level 4) |
| Human Legal Counsel | Human-LC-01 | External counsel (Level 5) |
| Human DevRel | Human-DR-01 | Human-PO-01 (Level 3) |

---

*This document is a living plan. Updates require AI PM approval and Human PO notification. The authoritative version resides in the project repository at `/docs/communication-plan.md`.*

**Related Documents**:
- [01-Project Charter](01-project-charter.md)
- [03-Phases & Milestones](03-phases-milestones.md)
