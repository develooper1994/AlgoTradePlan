"""Risk-before-execution trade flow orchestrator (Phase 10)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.algotradeplan.core.intent import OrderIntent, signal_to_intent


@dataclass(frozen=True)
class TradeFlowResult:
    signal: dict[str, Any]
    order_intent: dict[str, Any] | None
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
                order_intent=None,
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
                order_intent=None,
                risk_decision={"approved": False, "reason": "hold_signal"},
                execution=None,
                halted=False,
                reason="hold_signal",
            )

        trade_intent = signal_to_intent(
            signal,
            symbol=str(context.get("symbol", "")),
            quantity=float(context.get("quantity", 0.0)),
            strategy_id=str(getattr(self.strategy, "plugin_id", "strategy")),
            price=float(context.get("price", signal.get("price", 0.0))),
        )
        if trade_intent is None:
            return TradeFlowResult(
                signal=signal,
                order_intent=None,
                risk_decision={"approved": False, "reason": "hold_signal"},
                execution=None,
                halted=False,
                reason="hold_signal",
            )

        order_intent = OrderIntent.from_trade_intent(trade_intent, metadata={"context": context})
        routed_order = order_intent.to_dict()
        decision = self.risk.evaluate(routed_order)
        if not decision.get("approved", False):
            return TradeFlowResult(
                signal=signal,
                order_intent=routed_order,
                risk_decision=decision,
                execution=None,
                halted=True,
                reason=str(decision.get("reason", "risk_rejected")),
            )

        adjusted_quantity = float(decision.get("adjusted_quantity", order_intent.quantity))
        execution = self.execution.send_order(order_intent.with_quantity(adjusted_quantity).to_dict())
        return TradeFlowResult(
            signal=signal,
            order_intent=routed_order,
            risk_decision=decision,
            execution=execution,
            halted=False,
            reason=None,
        )
