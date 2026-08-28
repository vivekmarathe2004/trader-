"""
High-fidelity Simulated Paper Trading Broker (MockBroker).
Simulates realistic order fills, slippage distributions, commissions, and SL/TP tick processing.
"""
import uuid
import time
import random
from typing import List, Dict, Optional, Any
from app.execution.broker_interface import BaseBroker
from app.execution.models import OrderRequest, OrderResult, NormalizedPosition, BrokerConfig
from app.execution.enums import OrderSide, OrderType, OrderState, ExecutionMode
from app.execution.state_machine import order_state_machine
from app.services.unified_provider import unified_provider
from app.core.config import settings
from app.core.logging import logger, format_ist_timestamp


class MockBroker(BaseBroker):
    broker_id = "MOCK_BROKER"
    name = "Paper Trading Broker (Simulated)"

    def __init__(self, initial_equity: float = 100000.0):
        self.equity: float = initial_equity
        self.balance: float = initial_equity
        self.currency: str = "USD"
        self._positions: Dict[str, NormalizedPosition] = {}
        self._closed_trades: List[Dict[str, Any]] = []
        self._is_connected: bool = True

    async def connect(self) -> bool:
        self._is_connected = True
        return True

    async def disconnect(self):
        self._is_connected = False

    def get_balance(self) -> Dict[str, float]:
        self._update_open_positions_pnl()
        unrealized = sum(p.unrealized_pnl for p in self._positions.values())
        curr_equity = round(self.balance + unrealized, 2)
        return {
            "equity": curr_equity,
            "free_balance": round(self.balance, 2),
            "unrealized_pnl": round(unrealized, 2),
            "currency": self.currency,
        }

    def get_positions(self) -> List[NormalizedPosition]:
        self._update_open_positions_pnl()
        return list(self._positions.values())

    async def place_order(self, request: OrderRequest, approved_lots: float) -> OrderResult:
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        client_id = request.client_order_id or f"CLI-{uuid.uuid4().hex[:6].upper()}"

        # State transition: SIGNAL -> RISK_CHECK -> ORDER_CREATED -> ORDER_SUBMITTED -> FILLED -> POSITION_OPEN
        order_state_machine.transition(order_id, OrderState.RISK_CHECK)
        order_state_machine.transition(order_id, OrderState.ORDER_CREATED)
        order_state_machine.transition(order_id, OrderState.ORDER_SUBMITTED)

        quote = unified_provider.get_latest_quote(request.symbol)
        base_price = quote["ask"] if request.side == OrderSide.BUY else quote["bid"]
        
        # Slippage: random 0.1 to 0.4 pips
        pip_size = settings.get_pip_size(request.symbol)
        slippage_pips = random.uniform(0.1, 0.4)
        slippage_amount = slippage_pips * pip_size
        fill_price = base_price + slippage_amount if request.side == OrderSide.BUY else base_price - slippage_amount
        fill_price = round(fill_price, 5 if pip_size < 0.001 else 2)

        # Commission: $3.50 per lot
        commission = round(approved_lots * 3.50, 2)
        self.balance -= commission

        order_state_machine.transition(order_id, OrderState.FILLED)

        pos_id = f"POS-{uuid.uuid4().hex[:8].upper()}"
        pos = NormalizedPosition(
            position_id=pos_id,
            symbol=request.symbol.upper(),
            side=request.side.value,
            lots=approved_lots,
            entry_price=fill_price,
            current_price=fill_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            initial_sl=request.stop_loss,
            break_even_active=False,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            broker=self.broker_id,
            status="OPEN",
            strategy_id=request.strategy_id or "SUPERTREND_TREND_FOLLOWING",
            strategy_version=request.strategy_version or "v1.0.0",
            opened_at_ist=format_ist_timestamp(),
        )
        self._positions[pos_id] = pos
        order_state_machine.transition(order_id, OrderState.POSITION_OPEN)
        order_state_machine.transition(pos_id, OrderState.POSITION_OPEN)

        logger.info(f"[MockBroker] Order {order_id} filled: {pos.side} {pos.lots} lots {pos.symbol} @ {fill_price} (SL: {pos.stop_loss}, TP: {pos.take_profit})")

        return OrderResult(
            success=True,
            order_id=order_id,
            client_order_id=client_id,
            symbol=request.symbol.upper(),
            side=request.side.value,
            order_state=OrderState.POSITION_OPEN,
            fill_price=fill_price,
            fill_quantity=approved_lots,
            slippage=round(slippage_pips, 2),
            commission=commission,
        )

    async def close_position(self, position_id: str, reason: str = "MANUAL_CLOSE") -> bool:
        pos = self._positions.get(position_id)
        if not pos:
            return False

        order_state_machine.transition(position_id, OrderState.CLOSING)

        quote = unified_provider.get_latest_quote(pos.symbol)
        exit_price = quote["bid"] if pos.side == "BUY" else quote["ask"]

        pip_size = settings.get_pip_size(pos.symbol)
        units = pos.lots * settings.get_lot_units(pos.symbol)
        
        if pos.side == "BUY":
            pnl_pips = (exit_price - pos.entry_price) / pip_size
            pnl_usd = (exit_price - pos.entry_price) * units
        else:
            pnl_pips = (pos.entry_price - exit_price) / pip_size
            pnl_usd = (pos.entry_price - exit_price) * units

        pnl_usd = round(pnl_usd, 2)
        pnl_pips = round(pnl_pips, 2)

        self.balance += pnl_usd
        pos.realized_pnl = pnl_usd
        pos.status = "CLOSED"

        del self._positions[position_id]
        order_state_machine.transition(position_id, OrderState.CLOSED)
        order_state_machine.transition(position_id, OrderState.RECONCILED)

        # Notify RiskEngine of realized PnL delta
        from app.risk.engine import risk_engine
        risk_engine.update_equity(self.balance, pnl_usd)

        closed_trade = {
            "trade_id": f"TRD-{uuid.uuid4().hex[:8].upper()}",
            "position_id": position_id,
            "symbol": pos.symbol,
            "side": pos.side,
            "lots": pos.lots,
            "entry_price": pos.entry_price,
            "exit_price": exit_price,
            "pnl": pnl_usd,
            "pnl_pips": pnl_pips,
            "strategy_id": getattr(pos, "strategy_id", "SUPERTREND_TREND_FOLLOWING"),
            "strategy_version": getattr(pos, "strategy_version", "v1.0.0"),
            "exit_reason": reason,
            "opened_at_ist": getattr(pos, "opened_at_ist", format_ist_timestamp()),
            "closed_at_ist": format_ist_timestamp(),
        }
        self._closed_trades.append(closed_trade)

        # Notify AutoTrader
        try:
            from app.trading.auto_trader import auto_trader
            auto_trader.record_closed_trade(closed_trade)
        except Exception as e:
            logger.debug(f"AutoTrader notification on close: {e}")

        logger.info(f"[MockBroker] Position {position_id} closed ({reason}): PnL ${pnl_usd:+.2f} ({pnl_pips:+.1f} pips)")
        return True

    def modify_position(self, position_id: str, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> bool:
        pos = self._positions.get(position_id)
        if not pos:
            return False
        if stop_loss is not None:
            pos.stop_loss = stop_loss
        if take_profit is not None:
            pos.take_profit = take_profit
        order_state_machine.transition(position_id, OrderState.POSITION_MODIFIED)
        return True

    def _update_open_positions_pnl(self):
        closed_ids = []
        for pos_id, pos in list(self._positions.items()):
            quote = unified_provider.get_latest_quote(pos.symbol)
            curr_p = quote["bid"] if pos.side == "BUY" else quote["ask"]
            pos.current_price = curr_p

            pip_size = settings.get_pip_size(pos.symbol)
            units = pos.lots * settings.get_lot_units(pos.symbol)

            # Check SL / TP hits
            if pos.side == "BUY":
                unrealized = (curr_p - pos.entry_price) * units
                if pos.stop_loss and curr_p <= pos.stop_loss:
                    reason = "TRAILING_STOP_HIT" if pos.stop_loss > pos.entry_price else ("BE_HIT" if pos.break_even_active else "SL_HIT")
                    closed_ids.append((pos_id, reason))
                elif pos.take_profit and curr_p >= pos.take_profit:
                    closed_ids.append((pos_id, "TP_HIT"))
            else:
                unrealized = (pos.entry_price - curr_p) * units
                if pos.stop_loss and curr_p >= pos.stop_loss:
                    reason = "TRAILING_STOP_HIT" if pos.stop_loss < pos.entry_price else ("BE_HIT" if pos.break_even_active else "SL_HIT")
                    closed_ids.append((pos_id, reason))
                elif pos.take_profit and curr_p <= pos.take_profit:
                    closed_ids.append((pos_id, "TP_HIT"))

            pos.unrealized_pnl = round(unrealized, 2)

        # Process automatic SL/TP executions
        import asyncio
        for pos_id, reason in closed_ids:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.close_position(pos_id, reason))
            except RuntimeError:
                try:
                    event_loop = asyncio.get_event_loop()
                    if event_loop.is_running():
                        asyncio.run_coroutine_threadsafe(self.close_position(pos_id, reason), event_loop)
                    else:
                        asyncio.run(self.close_position(pos_id, reason))
                except Exception:
                    pass

    def get_config(self) -> BrokerConfig:
        return BrokerConfig(
            broker_id=self.broker_id,
            name=self.name,
            mode=ExecutionMode.PAPER,
            is_active=True,
            is_connected=self._is_connected,
            api_key_masked="SIMULATED",
            environment="paper",
            latency_ms=1.2,
        )


mock_broker = MockBroker()
