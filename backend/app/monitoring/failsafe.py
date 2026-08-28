"""
Failsafe background monitor and emergency circuit breaker.
"""
import time
import asyncio
from typing import Dict, Optional, Any
from app.core.logging import logger, format_ist_timestamp
from app.risk.engine import risk_engine


class FailsafeMonitor:
    def __init__(self):
        self.is_monitoring: bool = False
        self._task: Optional[asyncio.Task] = None
        self._last_heartbeat: float = time.time()
        self._failure_counts: Dict[str, int] = {}

    def start(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("Failsafe heartbeat monitor active.")

    def stop(self):
        self.is_monitoring = False
        if self._task and not self._task.done():
            self._task.cancel()

    async def _monitor_loop(self):
        while self.is_monitoring:
            try:
                self._last_heartbeat = time.time()
                # Check broker connectivity
                from app.execution.manager import broker_manager
                active_broker = broker_manager.get_active_broker()
                is_connected = await active_broker.connect()
                if not is_connected and active_broker.broker_id != "MOCK_BROKER":
                    logger.critical(f"Active broker {active_broker.broker_id} disconnected! Triggering failsafe.")
                    risk_engine.trigger_emergency_kill_switch(f"Broker {active_broker.broker_id} disconnect detected")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in failsafe monitor loop: {e}")
            await asyncio.sleep(10)


failsafe_monitor = FailsafeMonitor()
