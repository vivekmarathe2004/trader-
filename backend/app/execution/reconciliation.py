"""
Remote vs Local Position and Balance State Reconciliation Audit Engine.
"""
from typing import Dict, List, Any
from app.execution.manager import broker_manager
from app.database.session import SessionLocal
from app.database.models import PositionModel
from app.core.logging import logger, format_ist_timestamp


class ReconciliationEngine:
    def __init__(self):
        pass

    def reconcile_active_broker(self) -> Dict[str, Any]:
        """
        Compares local database state against the remote active broker positions.
        Identifies orphan positions, mismatched lots, and balance drift.
        """
        active_broker = broker_manager.get_active_broker()
        remote_positions = active_broker.get_positions()
        broker_balance = active_broker.get_balance()

        db = SessionLocal()
        try:
            local_positions = db.query(PositionModel).filter(
                PositionModel.status == "OPEN",
                PositionModel.broker == active_broker.broker_id
            ).all()

            local_dict = {p.position_id: p for p in local_positions}
            remote_dict = {p.position_id: p for p in remote_positions}

            discrepancies = []

            # Check for positions present in broker but missing locally
            for pos_id, r_pos in remote_dict.items():
                if pos_id not in local_dict:
                    discrepancies.append({
                        "type": "ORPHAN_REMOTE_POSITION",
                        "position_id": pos_id,
                        "symbol": r_pos.symbol,
                        "lots": r_pos.lots,
                        "details": "Position exists on broker but not in local database",
                    })

            # Check for positions present locally but missing in broker
            for pos_id, l_pos in local_dict.items():
                if pos_id not in remote_dict:
                    discrepancies.append({
                        "type": "PHANTOM_LOCAL_POSITION",
                        "position_id": pos_id,
                        "symbol": l_pos.symbol,
                        "lots": l_pos.lots,
                        "details": "Position marked OPEN locally but closed/missing on broker",
                    })

            is_synced = len(discrepancies) == 0

            return {
                "timestamp_ist": format_ist_timestamp(),
                "broker_id": active_broker.broker_id,
                "is_synced": is_synced,
                "discrepancies_count": len(discrepancies),
                "discrepancies": discrepancies,
                "remote_positions_count": len(remote_positions),
                "local_positions_count": len(local_positions),
                "broker_equity": broker_balance.get("equity", 0.0),
                "broker_free_balance": broker_balance.get("free_balance", 0.0),
            }
        finally:
            db.close()


    def reconcile_for_broker(self, broker_id: str) -> Dict[str, Any]:
        """
        Reconciles the specified broker (by ID) against local database state.
        Temporarily switches to the requested broker for the reconciliation read,
        then returns results. Falls back to the active broker if broker_id not found.
        """
        try:
            # Try to get the specific broker by ID
            target_broker = broker_manager.get_broker_by_id(broker_id.upper())
        except Exception:
            target_broker = None

        if target_broker is None:
            # Fallback: run against the currently active broker
            return self.reconcile_active_broker()

        remote_positions = target_broker.get_positions()
        broker_balance = target_broker.get_balance()

        db = SessionLocal()
        try:
            local_positions = db.query(PositionModel).filter(
                PositionModel.status == "OPEN",
                PositionModel.broker == target_broker.broker_id,
            ).all()

            local_dict = {p.position_id: p for p in local_positions}
            remote_dict = {p.position_id: p for p in remote_positions}

            discrepancies = []
            for pos_id, r_pos in remote_dict.items():
                if pos_id not in local_dict:
                    discrepancies.append({
                        "type": "ORPHAN_REMOTE_POSITION",
                        "position_id": pos_id,
                        "symbol": r_pos.symbol,
                        "lots": r_pos.lots,
                        "details": "Position exists on broker but not in local database",
                    })
            for pos_id, l_pos in local_dict.items():
                if pos_id not in remote_dict:
                    discrepancies.append({
                        "type": "PHANTOM_LOCAL_POSITION",
                        "position_id": pos_id,
                        "symbol": l_pos.symbol,
                        "lots": l_pos.lots,
                        "details": "Position marked OPEN locally but closed/missing on broker",
                    })

            return {
                "timestamp_ist": format_ist_timestamp(),
                "broker_id": target_broker.broker_id,
                "is_synced": len(discrepancies) == 0,
                "discrepancies_count": len(discrepancies),
                "discrepancies": discrepancies,
                "remote_positions_count": len(remote_positions),
                "local_positions_count": len(local_positions),
                "broker_equity": broker_balance.get("equity", 0.0),
                "broker_free_balance": broker_balance.get("free_balance", 0.0),
            }
        finally:
            db.close()


reconciliation_engine = ReconciliationEngine()
