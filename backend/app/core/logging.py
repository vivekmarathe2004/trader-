"""
Structured JSON logging with IST timestamping and in-memory ring buffer for audit logs.
"""
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from collections import deque

IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_now() -> datetime:
    return datetime.now(IST)


def format_ist_timestamp(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = get_ist_now()
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc).astimezone(IST)
    return dt.strftime("%Y-%m-%d %H:%M:%S IST")


class LogBuffer:
    def __init__(self, maxlen: int = 1000):
        self.buffer: deque = deque(maxlen=maxlen)

    def add(self, record: Dict[str, Any]):
        self.buffer.append(record)

    def get_logs(self, limit: int = 100, level: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        logs = list(self.buffer)
        if level:
            level_upper = level.upper()
            logs = [l for l in logs if l.get("level") == level_upper]
        if search:
            search_lower = search.lower()
            logs = [l for l in logs if search_lower in json.dumps(l).lower()]
        return logs[-limit:][::-1]

    def clear(self):
        self.buffer.clear()


log_buffer = LogBuffer()


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ist_time = format_ist_timestamp()
        log_obj = {
            "timestamp": ist_time,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj.update(record.extra_data)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        log_buffer.add(log_obj)
        return json.dumps(log_obj)


def setup_logger(name: str = "quant_platform", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger


logger = setup_logger()
