# Deployment and Rollback Runbook

## Purpose
Provide a deterministic deploy/rollback flow that requires lint, test, smoke,
and readiness check to succeed before promotion.

## Preconditions
- the active phase allows deployment activity
- the dry-run promotion runbook has been completed for the target revision

## Procedure
1. `make lint`
2. `make test`
3. `make smoke`
4. `python scripts/deploy_check.py --repo-root .`
5. capture the correlation id and revision id for the deployment
6. promote according to the environment-switching documentation

## Validation
- all four commands above exit with status 0
- `tests/unit/test_deploy_check.py` is green
- structured logger has a `deploy.start` and `deploy.complete` entry

## Rollback / Recovery
1. trigger `TradeFlow.trigger_emergency_stop(reason="deploy_rollback")`
2. revert to the previously approved revision
3. re-run `python scripts/deploy_check.py --repo-root .`
4. follow `docs/runbooks/state_recovery.md` if positions are affected

## Escalation
- if rollback fails, open emergency-stop and state recovery runbooks together
