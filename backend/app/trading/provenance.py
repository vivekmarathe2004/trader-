"""
Immutable Rule Provenance Snapshot Engine.
Creates tamper-proof audit records for every signal evaluation.
"""
import uuid
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.logging import format_ist_timestamp
from app.core.security import compute_audit_hash


def build_provenance_snapshot(
    symbol: str,
    timeframe: str,
    strategy_id: str,
    strategy_version: str,
    market_regime: str,
    indicator_snapshot: Dict[str, Any],
    rule_evaluation_matrix: list,
    decision: str,
    veto_reasons: list,
    execution_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Constructs a complete provenance snapshot with a unique ID and SHA-256 hash.
    """
    timestamp = format_ist_timestamp()
    prov_id = f"SIG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{symbol}-{uuid.uuid4().hex[:6].upper()}"
    
    snapshot = {
        "provenance_id": prov_id,
        "timestamp_ist": timestamp,
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "market_regime": market_regime,
        "indicator_snapshot": indicator_snapshot,
        "rule_evaluation_matrix": rule_evaluation_matrix,
        "decision": decision,
        "veto_reasons": veto_reasons,
        "execution_payload": execution_payload or {},
    }
    
    # Generate cryptographic hash for record integrity
    snapshot_str = json.dumps(snapshot, sort_keys=True)
    snapshot["record_hash"] = hashlib.sha256(snapshot_str.encode("utf-8")).hexdigest()
    
    return snapshot
