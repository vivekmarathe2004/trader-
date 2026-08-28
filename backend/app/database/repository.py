"""
Data access repository layer with database persistence.
"""
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import (
    CandleModel, OrderModel, PositionModel, TradeModel, SignalModel, AuditLogModel, StrategyModel, BrokerCredentialModel
)
from app.core.security import compute_audit_hash, encrypt_secret, decrypt_secret
from app.core.logging import format_ist_timestamp


class Repository:
    def __init__(self, db: Session):
        self.db = db

    # --- Broker Credentials ---
    def save_or_update_broker_credentials(
        self,
        broker_id: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        account_id: Optional[str] = None,
        environment: Optional[str] = "paper",
        extra_params: Optional[dict] = None,
    ) -> BrokerCredentialModel:
        broker_id = broker_id.upper()
        cred = self.db.query(BrokerCredentialModel).filter(BrokerCredentialModel.broker_id == broker_id).first()
        
        enc_key = encrypt_secret(api_key) if api_key else (cred.api_key_encrypted if cred else None)
        enc_secret = encrypt_secret(api_secret) if api_secret else (cred.api_secret_encrypted if cred else None)
        enc_account = encrypt_secret(account_id) if account_id else (cred.account_id_encrypted if cred else None)
        extra_json = json.dumps(extra_params) if extra_params else (cred.extra_params_json if cred else None)

        if cred:
            if api_key is not None:
                cred.api_key_encrypted = enc_key
            if api_secret is not None:
                cred.api_secret_encrypted = enc_secret
            if account_id is not None:
                cred.account_id_encrypted = enc_account
            if environment is not None:
                cred.environment = environment
            if extra_params is not None:
                cred.extra_params_json = extra_json
            cred.updated_at = datetime.utcnow()
        else:
            cred = BrokerCredentialModel(
                broker_id=broker_id,
                api_key_encrypted=enc_key,
                api_secret_encrypted=enc_secret,
                account_id_encrypted=enc_account,
                environment=environment or "paper",
                extra_params_json=extra_json,
            )
            self.db.add(cred)

        self.db.commit()
        self.db.refresh(cred)
        return cred

    def get_broker_credentials(self, broker_id: str) -> Optional[Dict[str, Any]]:
        broker_id = broker_id.upper()
        cred = self.db.query(BrokerCredentialModel).filter(BrokerCredentialModel.broker_id == broker_id).first()
        if not cred:
            return None
        return {
            "broker_id": cred.broker_id,
            "api_key": decrypt_secret(cred.api_key_encrypted),
            "api_secret": decrypt_secret(cred.api_secret_encrypted),
            "account_id": decrypt_secret(cred.account_id_encrypted),
            "environment": cred.environment,
            "extra_params": json.loads(cred.extra_params_json) if cred.extra_params_json else {},
            "updated_at": cred.updated_at,
        }

    def get_all_broker_credentials(self) -> List[Dict[str, Any]]:
        creds = self.db.query(BrokerCredentialModel).all()
        res = []
        for c in creds:
            res.append({
                "broker_id": c.broker_id,
                "api_key": decrypt_secret(c.api_key_encrypted),
                "api_secret": decrypt_secret(c.api_secret_encrypted),
                "account_id": decrypt_secret(c.account_id_encrypted),
                "environment": c.environment,
                "extra_params": json.loads(c.extra_params_json) if c.extra_params_json else {},
                "updated_at": c.updated_at,
            })
        return res

    # --- Orders ---
    def create_order(self, order_data: dict) -> OrderModel:
        order = OrderModel(**order_data)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def update_order_state(self, order_id: str, new_state: str, error_message: Optional[str] = None) -> Optional[OrderModel]:
        order = self.db.query(OrderModel).filter(OrderModel.order_id == order_id).first()
        if order:
            order.state = new_state
            if error_message:
                order.error_message = error_message
            order.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(order)
        return order

    def get_orders(self, limit: int = 100, symbol: Optional[str] = None) -> List[OrderModel]:
        query = self.db.query(OrderModel)
        if symbol:
            query = query.filter(OrderModel.symbol == symbol.upper())
        return query.order_by(OrderModel.created_at.desc()).limit(limit).all()

    # --- Positions ---
    def create_position(self, pos_data: dict) -> PositionModel:
        pos = PositionModel(**pos_data)
        self.db.add(pos)
        self.db.commit()
        self.db.refresh(pos)
        return pos

    def get_open_positions(self, broker: Optional[str] = None) -> List[PositionModel]:
        query = self.db.query(PositionModel).filter(PositionModel.status == "OPEN")
        if broker:
            query = query.filter(PositionModel.broker == broker)
        return query.all()

    def get_position(self, position_id: str) -> Optional[PositionModel]:
        return self.db.query(PositionModel).filter(PositionModel.position_id == position_id).first()

    def update_position(self, position_id: str, updates: dict) -> Optional[PositionModel]:
        pos = self.get_position(position_id)
        if pos:
            for k, v in updates.items():
                setattr(pos, k, v)
            self.db.commit()
            self.db.refresh(pos)
        return pos

    # --- Trades ---
    def record_trade(self, trade_data: dict) -> TradeModel:
        trade = TradeModel(**trade_data)
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def get_trades(self, limit: int = 100, symbol: Optional[str] = None) -> List[TradeModel]:
        query = self.db.query(TradeModel)
        if symbol:
            query = query.filter(TradeModel.symbol == symbol.upper())
        return query.order_by(TradeModel.closed_at.desc()).limit(limit).all()

    def get_performance_statistics(self) -> Dict[str, Any]:
        trades = self.db.query(TradeModel).all()
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate_pct": 0.0,
                "daily_pnl": 0.0,
                "peak_drawdown_pct": 0.0,
                "total_realized_pnl": 0.0,
                "profit_factor": 0.0,
                "has_real_history": False,
            }

        total_trades = len(trades)
        wins = [t for t in trades if (t.pnl or 0) > 0]
        losses = [t for t in trades if (t.pnl or 0) <= 0]
        win_rate = (len(wins) / total_trades) * 100.0 if total_trades > 0 else 0.0

        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        daily_pnl = sum((t.pnl or 0) for t in trades if t.closed_at and str(t.closed_at).startswith(today_str))
        total_pnl = sum((t.pnl or 0) for t in trades)

        gross_profit = sum((t.pnl or 0) for t in wins)
        gross_loss = abs(sum((t.pnl or 0) for t in losses))
        pf = (gross_profit / gross_loss) if gross_loss > 0 else (1.0 if gross_profit > 0 else 0.0)

        # Calculate real drawdown from trade equity path
        running_equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            running_equity += (t.pnl or 0)
            if running_equity > peak:
                peak = running_equity
            dd = (peak - running_equity) / (1000.0 + peak) * 100.0 if (1000.0 + peak) > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        return {
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate_pct": round(win_rate, 1),
            "daily_pnl": round(daily_pnl, 2),
            "peak_drawdown_pct": round(max_dd, 1),
            "total_realized_pnl": round(total_pnl, 2),
            "profit_factor": round(pf, 2),
            "has_real_history": True,
        }

    # --- Signals & Provenance ---
    def record_signal(self, sig_data: dict) -> SignalModel:
        signal = SignalModel(**sig_data)
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def get_signals(self, limit: int = 100, symbol: Optional[str] = None, decision: Optional[str] = None) -> List[SignalModel]:
        query = self.db.query(SignalModel)
        if symbol:
            query = query.filter(SignalModel.symbol == symbol.upper())
        if decision:
            query = query.filter(SignalModel.decision == decision.upper())
        return query.order_by(SignalModel.created_at.desc()).limit(limit).all()

    # --- Audit Trail ---
    def record_audit_log(self, event_type: str, payload: dict) -> AuditLogModel:
        last_log = self.db.query(AuditLogModel).order_by(AuditLogModel.id.desc()).first()
        prev_hash = last_log.hash if last_log else "GENESIS_HASH_0000000000000000000000"
        timestamp = format_ist_timestamp()
        
        record_content = {
            "timestamp": timestamp,
            "event_type": event_type,
            "payload": payload,
        }
        current_hash = compute_audit_hash(record_content, prev_hash)
        
        log_entry = AuditLogModel(
            timestamp_ist=timestamp,
            event_type=event_type,
            payload_json=json.dumps(payload),
            previous_hash=prev_hash,
            hash=current_hash,
        )
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry

    def get_audit_logs(self, limit: int = 100) -> List[AuditLogModel]:
        return self.db.query(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(limit).all()

    # --- Strategies ---
    def save_or_update_strategy(self, strat_data: dict) -> StrategyModel:
        strat = self.db.query(StrategyModel).filter(
            StrategyModel.strategy_id == strat_data["strategy_id"],
            StrategyModel.version == strat_data["version"]
        ).first()
        if strat:
            for k, v in strat_data.items():
                setattr(strat, k, v)
        else:
            strat = StrategyModel(**strat_data)
            self.db.add(strat)
        self.db.commit()
        self.db.refresh(strat)
        return strat

    def get_strategies(self) -> List[StrategyModel]:
        return self.db.query(StrategyModel).all()
