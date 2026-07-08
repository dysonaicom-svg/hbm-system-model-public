"""Logger Plugin

Advanced logging plugin for HBM4 simulation.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from model.plugins.base import PluginInterface, PluginMetadata


class LoggerPlugin(PluginInterface):
    """Advanced logging plugin"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="logger",
            version="1.0.0",
            description="Advanced logging for HBM4 simulation",
            author="HBM4 Team",
        )

    def _do_initialize(self, config: Dict[str, Any]) -> None:
        """Initialize logger"""
        self._log_level = config.get("level", "INFO")
        self._log_format = config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self._output = config.get("output", "console")  # console, file, both
        self._log_file = config.get("file", "hbm4_simulation.log")

        # Setup logging
        self._setup_logging()

        self._entries: List[Dict] = []
        self._start_time: Optional[float] = None

    def _do_start(self) -> None:
        """Start logging"""
        self._start_time = time.time()
        logging.info("LoggerPlugin started")

    def _do_stop(self) -> None:
        """Stop logging"""
        if self._start_time is not None:
            elapsed = time.time() - self._start_time
            logging.info(f"LoggerPlugin stopped. Total time: {elapsed:.2f}s")
            logging.info(f"Total log entries: {len(self._entries)}")

    def _setup_logging(self) -> None:
        """Setup Python logging"""
        logger = logging.getLogger("hbm4")
        logger.setLevel(getattr(logging, self._log_level.upper(), logging.INFO))

        # Console handler
        if self._output in ("console", "both"):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(self._log_format))
            logger.addHandler(console_handler)

        # File handler
        if self._output in ("file", "both"):
            file_handler = logging.FileHandler(self._log_file)
            file_handler.setFormatter(logging.Formatter(self._log_format))
            logger.addHandler(file_handler)

    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a simulation event

        Args:
            event_type: Type of event
            data: Event data
        """
        entry = {
            "timestamp": time.time(),
            "type": event_type,
            "data": data,
        }
        self._entries.append(entry)

        logging.debug(f"Event: {event_type} - {data}")

    def log_metric(self, metric_name: str, value: float, unit: str = "") -> None:
        """Log a performance metric

        Args:
            metric_name: Name of metric
            value: Metric value
            unit: Unit of measurement
        """
        entry = {
            "timestamp": time.time(),
            "type": "metric",
            "name": metric_name,
            "value": value,
            "unit": unit,
        }
        self._entries.append(entry)

        logging.info(f"Metric: {metric_name} = {value} {unit}")

    def get_entries(self, event_type: Optional[str] = None) -> List[Dict]:
        """Get logged entries

        Args:
            event_type: Filter by event type

        Returns:
            List of log entries
        """
        if event_type is None:
            return self._entries.copy()

        return [e for e in self._entries if e.get("type") == event_type]

    def clear(self) -> None:
        """Clear all log entries"""
        self._entries.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return {
            **super().get_stats(),
            "total_entries": len(self._entries),
            "log_level": self._log_level,
            "output": self._output,
        }
