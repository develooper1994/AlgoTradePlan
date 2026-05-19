"""Risk-before-execution trade flow orchestrator (Phase 10)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TradeFlowResult:
    signal: dict[str, Any]
    risk_decision: dict[str, Any]
    execution: dict[str, Any] | None
    halted: bool
    reason: str | None


class TradeFlow:
    """Run signal -> risk -> execution with explicit halting and audit hooks."""

    def __init__(self, strategy: Any, risk: Any, execution: Any) -> None:
        self.strategy = strategy
        self.risk = risk
        self.execution = execution
        self._emergency_stop = False

    def trigger_emergency_stop(self, reason: str = "manual") -> None:
        self._emergency_stop_reason = reason
        self._emergency_stop = True

    def run(self, context: dict[str, Any]) -> TradeFlowResult:
        if self._emergency_stop:
            return TradeFlowResult(
                signal={},
                risk_decision={"approved": False, "reason": "emergency_stop"},
                execution=None,
                halted=True,
                reason=getattr(self, "_emergency_stop_reason", "emergency_stop"),
            )

        signal = self.strategy.generate_signal(context)
        action = str(signal.get("action", "hold")).lower()
        if action == "hold":
            return TradeFlowResult(
                signal=signal,
                risk_decision={"approved": False, "reason": "hold_signal"},
                execution=None,
                halted=False,
                reason="hold_signal",
            )

        order_intent = {
            "symbol": context.get("symbol"),
            "action": action,
            "context": context,
        }
        decision = self.risk.evaluate(order_intent)
        if not decision.get("approved", False):
            return TradeFlowResult(
                signal=signal,
                risk_decision=decision,
                execution=None,
                halted=True,
                reason=str(decision.get("reason", "risk_rejected")),
            )

        execution = self.execution.send_order(order_intent)
        return TradeFlowResult(
            signal=signal,
            risk_decision=decision,
            execution=execution,
            halted=False,
            reason=None,
        )
