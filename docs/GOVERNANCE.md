# Governance

## Change Management Principles
- documentation, code, and validation advance together
- each phase has an explicit approval gate
- architecture and data contract changes must be reflected in the master plan and decision log

## Required Artifacts Per Phase
1. phase document under `/docs/phases`
2. linked checklist and validation steps
3. code or configuration scoped only to the approved phase
4. tests or smoke checks proving the phase exit criteria
5. runbook updates when operations or incident handling change

## Review Workflow
1. verify the active phase and scope
2. review contracts and docs before implementation details
3. ensure extension points have examples and tests
4. confirm rollback or mitigation steps exist for operational changes
5. record merge-ready decisions in `/docs/MASTER_PLAN.md`

## Deployment and Promotion
- no deployment promotion without passing lint, tests, and smoke checks
- dry-run and simulation paths must exist before live execution paths expand
- provenance and audit trails are required for data ingestion changes

## Extension Governance
- new plugin roots require a documented owner, purpose, and validation story
- contract-breaking changes need migration notes in `/docs/extending.md`
- source expansions must update `/docs/DATA_STRATEGY.md`

## Incident and Operations Governance
- every recurring operation should have a runbook template or example
- every incident class should define detection, mitigation, recovery, and postmortem steps
- emergency changes still require follow-up documentation and decision-log updates
