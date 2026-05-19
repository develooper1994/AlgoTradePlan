"""Production risk engine with structured decisions and composable rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    checks: list[str]
    rejected_rules: list[str]
    adjusted_quantity: float
    original_quantity: float
    notional: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "reason": self.reason,
            "checks": self.checks,
            "rejected_rules": self.rejected_rules,
            "adjusted_quantity": self.adjusted_quantity,
            "original_quantity": self.original_quantity,
            "notional": self.notional,
            "metadata": self.metadata,
        }


class RiskEngine:
    """Composable risk engine supporting multiple rule checks.

    Rules evaluated in order; any rejection stops the chain unless
    ``allow_all_checks=True`` is passed (for reporting mode).
    """

    def __init__(
        self,
        *,
        max_notional: float = 10_000.0,
        max_position_size: float = 1_000.0,
        max_daily_loss: float = 500.0,
        max_drawdown_pct: float = 0.20,
        max_leverage: float = 5.0,
        symbol_whitelist: list[str] | None = None,
        symbol_blacklist: list[str] | None = None,
        kill_switch: bool = False,
        kill_switch_reason: str = "kill_switch_active",
    ) -> None:
        self.max_notional = max_notional
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.max_drawdown_pct = max_drawdown_pct
        self.max_leverage = max_leverage
        self.symbol_whitelist = {s.upper() for s in symbol_whitelist} if symbol_whitelist else None
        self.symbol_blacklist = {s.upper() for s in symbol_blacklist} if symbol_blacklist else set()
        self.kill_switch = kill_switch
        self.kill_switch_reason = kill_switch_reason

        # Stateful accumulators (reset per session)
        self._daily_loss: float = 0.0
        self._current_drawdown_pct: float = 0.0

    # ------------------------------------------------------------------
    # Runtime state updates
    # ------------------------------------------------------------------

    def record_loss(self, loss: float) -> None:
        """Accumulate realized loss for daily-loss check (loss should be positive)."""
        if loss > 0:
            self._daily_loss += loss

    def update_drawdown(self, drawdown_pct: float) -> None:
        self._current_drawdown_pct = drawdown_pct

    def trigger_kill_switch(self, reason: str = "manual") -> None:
        self.kill_switch = True
        self.kill_switch_reason = reason

    def reset_daily_state(self) -> None:
        self._daily_loss = 0.0

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, order_intent: dict[str, Any]) -> dict[str, Any]:
        """Evaluate order intent; return a structured dict (backward-compatible with NotionalGuard)."""
        decision = self._evaluate(order_intent)
        return decision.to_dict()

    def _evaluate(self, order_intent: dict[str, Any]) -> RiskDecision:
        context = order_intent.get("context", {})
        symbol = str(order_intent.get("symbol") or context.get("symbol") or "")
        action = str(order_intent.get("action", "")).lower()
        quantity = float(context.get("quantity", 0.0))
        price = float(context.get("price", 0.0))
        notional = price * quantity
        checks: list[str] = []
        rejected_rules: list[str] = []

        # -- Kill switch
        if self.kill_switch:
            return RiskDecision(
                approved=False,
                reason=self.kill_switch_reason,
                checks=["kill_switch"],
                rejected_rules=["kill_switch"],
                adjusted_quantity=0.0,
                original_quantity=quantity,
                notional=notional,
            )

        # -- Action check
        if action not in {"buy", "sell"}:
            return RiskDecision(
                approved=False,
                reason="unsupported_action",
                checks=["action_check"],
                rejected_rules=["action_check"],
                adjusted_quantity=0.0,
                original_quantity=quantity,
                notional=notional,
            )
        checks.append("action_check")

        # -- Non-positive notional
        if notional <= 0:
            rejected_rules.append("non_positive_notional")
            return RiskDecision(
                approved=False,
                reason="non_positive_notional",
                checks=checks + ["notional_check"],
                rejected_rules=rejected_rules,
                adjusted_quantity=0.0,
                original_quantity=quantity,
                notional=notional,
            )
        checks.append("notional_check")

        # -- Symbol whitelist
        if self.symbol_whitelist and symbol.upper() not in self.symbol_whitelist:
            rejected_rules.append("symbol_not_whitelisted")
        elif symbol.upper() in self.symbol_blacklist:
            rejected_rules.append("symbol_blacklisted")
        else:
            checks.append("symbol_check")

        # -- Max notional
        if notional > self.max_notional:
            rejected_rules.append("max_notional_exceeded")
        else:
            checks.append("max_notional")

        # -- Max position size
        if quantity > self.max_position_size:
            rejected_rules.append("max_position_size_exceeded")
        else:
            checks.append("max_position_size")

        # -- Daily loss
        if self._daily_loss >= self.max_daily_loss:
            rejected_rules.append("max_daily_loss_exceeded")
        else:
            checks.append("max_daily_loss")

        # -- Drawdown
        if self._current_drawdown_pct >= self.max_drawdown_pct:
            rejected_rules.append("max_drawdown_exceeded")
        else:
            checks.append("max_drawdown")

        # -- Leverage (notional vs position_value cap)
        effective_leverage = notional / max(quantity, 1e-9) / max(price, 1e-9) if price else 0.0
        if effective_leverage > self.max_leverage and notional > self.max_notional:
            rejected_rules.append("max_leverage_exceeded")
        else:
            checks.append("max_leverage")

        approved = not rejected_rules
        reason = "approved" if approved else rejected_rules[0]
        adjusted_quantity = quantity if approved else 0.0

        return RiskDecision(
            approved=approved,
            reason=reason,
            checks=checks,
            rejected_rules=rejected_rules,
            adjusted_quantity=adjusted_quantity,
            original_quantity=quantity,
            notional=notional,
            metadata={"notional": notional, "daily_loss": self._daily_loss, "drawdown_pct": self._current_drawdown_pct},
        )
