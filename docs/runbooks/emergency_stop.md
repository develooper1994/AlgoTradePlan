# Emergency Stop Runbook

## Purpose
Halt new order submission across all environments while preserving audit trail.

## Preconditions
- caller has maintainer-level authorization
- `TradeFlow` instance is reachable (in-process or through orchestration entry point)

## Procedure
1. call `TradeFlow.trigger_emergency_stop(reason="<reason>")` on the active flow
2. confirm subsequent `TradeFlow.run(...)` calls return `halted=True`
3. capture correlation id and reason in the structured logger
4. notify on-call channel

## Validation
- `tests/adapters/test_trade_flow.py::TradeFlowTest::test_emergency_stop_blocks_subsequent_runs`
- structured log entry recorded with `event="emergency_stop"`

## Rollback / Recovery
- instantiate a fresh `TradeFlow` once the incident is resolved and the active
  phase approves resumption

## Escalation
- if the venue still receives orders after the stop, follow the reconciliation
  recovery runbook
