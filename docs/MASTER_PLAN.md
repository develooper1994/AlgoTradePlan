# MASTER PLAN

## Purpose
This document is the canonical phased blueprint for AlgoTradePlan. Code should advance only when the active phase has matching documentation, approval criteria, and validation coverage.

## Objectives
- keep the platform modular, auditable, and safe for staged production hardening
- require documented extension points before feature growth
- treat data ingestion, quality, storage, and provenance as first-class contracts
- preserve a decision log for every material planning choice

## Current Blueprint
1. **Phase-gated delivery**: every phase defines scope, checklist, and tests before implementation moves forward
2. **Plugin-first architecture**: data, strategy, risk, execution, and reconciliation integrations live behind explicit interfaces
3. **Multi-domain data foundation**: market, news, and macro sources share ingestion, storage, quality, and provenance contracts
4. **Auditability by default**: lineage, revisions, replay inputs, and operational runbooks are part of the baseline
5. **Governed change management**: docs, review, deploy, and extension rules stay aligned

## Phase Index
| Phase | Focus | Canonical Doc |
| --- | --- | --- |
| 01 | Planning, documentation, and governance baseline | `/docs/phases/01.md` |
| 02 | Core contracts, ids, and runtime scaffolding | `/docs/phases/02.md` |
| 03 | Test harness and hello-world pipeline | `/docs/phases/03.md` |
| 04 | Data contracts and source abstractions | `/docs/phases/04.md` |
| 05 | Data ingestion, storage, quality, provenance | `/docs/phases/05.md` |
| 06 | Research and feature-engineering lanes | `/docs/phases/06.md` |
| 07 | Strategy and model plugin skeletons | `/docs/phases/07.md` |
| 08 | Configuration and environment switching | `/docs/phases/08.md` |
| 09 | Observability and debug foundation | `/docs/phases/09.md` |
| 10 | Risk controls and execution readiness | `/docs/phases/10.md` |
| 11 | Reconciliation and state recovery | `/docs/phases/11.md` |
| 12 | Backtest, simulation, and dry-run promotion | `/docs/phases/12.md` |
| 13 | Deployment workflow and operational readiness | `/docs/phases/13.md` |
| 14 | Security, dependency, and compliance guardrails | `/docs/phases/14.md` |
| 15 | Extension lifecycle and contributor workflow | `/docs/phases/15.md` |
| 16 | Production acceptance and continuous governance | `/docs/phases/16.md` |

## Active Phase Rule
- only the active phase may introduce new modules or interfaces
- the next phase cannot begin until the current phase checklist and tests are approved
- every phase must leave behind durable docs, example extensions, and validation evidence

## Decision Log
### D-001: Documentation is a delivery gate
All phases require explicit goals, requirements, validation steps, and tests under `/docs/phases`.

### D-002: Data expansion is domain-first
Market, news, and macro data are the minimum supported source families and must use pluggable source abstractions.

### D-003: Provenance is mandatory
Every ingestion path must preserve request context, source identity, storage receipts, and revision metadata for replay and audit.

### D-004: Extension points ship with examples
Each plugin root must include at least one example implementation and test coverage built with deterministic fakes or mocks.

### D-005: Governance is part of the product
Review, deploy, runbook, and change-management rules live beside code and must evolve with the platform.
