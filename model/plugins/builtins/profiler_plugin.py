"""Profiler Plugin

Performance profiling plugin for HBM4 simulation.
"""

import time
import cProfile
import pstats
from io import StringIO
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from model.plugins.base import PluginInterface, PluginMetadata


@dataclass
class ProfileSample:
    """A profiling sample"""
    name: str
    calls: int
    total_time: float
    cumulative_time: float
    per_call: float


@dataclass
class ProfileStats:
    """Profiling statistics"""
    samples: List[ProfileSample] = field(default_factory=list)
    total_time: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0


class ProfilerPlugin(PluginInterface):
    """Performance profiling plugin"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="profiler",
            version="1.0.0",
            description="Performance profiling for HBM4 simulation",
            author="HBM4 Team",
            dependencies=["logger"],
        )

    def _do_initialize(self, config: Dict[str, Any]) -> None:
        """Initialize profiler"""
        self._enabled = config.get("enabled", True)
        self._output_file = config.get("output", "profile_stats.txt")
        self._sort_by = config.get("sort_by", "cumulative")  # cumulative, time, calls

        self._profiler = cProfile.Profile()
        self._stats: Optional[ProfileStats] = None
        self._profile_count = 0

    def _do_start(self) -> None:
        """Start profiling"""
        if self._enabled:
            self._profiler.enable()
            logging.info("ProfilerPlugin started - profiling enabled")

    def _do_stop(self) -> None:
        """Stop profiling"""
        if self._enabled:
            self._profiler.disable()
            self._collect_stats()
            self._save_stats()
            logging.info("ProfilerPlugin stopped - profiling disabled")

    def _collect_stats(self) -> None:
        """Collect profiling statistics"""
        stream = StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats(self._sort_by)

        # Parse stats
        self._profile_count += 1
        lines = stream.getvalue().split('\n')

        samples = []
        for line in lines:
            if '(' in line or 'ncalls' in line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                try:
                    sample = ProfileSample(
                        name=' '.join(parts[3:]),
                        calls=int(parts[0]),
                        total_time=float(parts[1]),
                        cumulative_time=float(parts[2]),
                        per_call=float(parts[1]) / int(parts[0]) if int(parts[0]) > 0 else 0,
                    )
                    samples.append(sample)
                except (ValueError, IndexError):
                    pass

        self._stats = ProfileStats(
            samples=samples[:50],  # Top 50
            total_time=sum(s.total_time for s in samples),
        )

    def _save_stats(self) -> None:
        """Save profiling statistics to file"""
        if self._stats is None:
            return

        with open(self._output_file, 'a') as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"Profile #{self._profile_count}\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"Total time: {self._stats.total_time:.4f}s\n")
            f.write(f"\nTop functions:\n")
            f.write(f"{'Calls':<10} {'Total':<10} {'Cumulative':<12} {'Per Call':<10} Function\n")
            f.write("-" * 80 + "\n")

            for sample in self._stats.samples[:20]:
                f.write(f"{sample.calls:<10} {sample.total_time:<10.4f} "
                       f"{sample.cumulative_time:<12.4f} {sample.per_call:<10.6f} "
                       f"{sample.name[:40]}\n")

    def get_top_functions(self, n: int = 10) -> List[ProfileSample]:
        """Get top N functions by total time

        Args:
            n: Number of functions to return

        Returns:
            List of top functions
        """
        if self._stats is None:
            return []

        return sorted(self._stats.samples, key=lambda s: s.total_time, reverse=True)[:n]

    def get_stats(self) -> Dict[str, Any]:
        """Get profiling statistics"""
        result = super().get_stats()

        if self._stats:
            result.update({
                "total_time": self._stats.total_time,
                "profile_count": self._profile_count,
                "output_file": self._output_file,
            })

        return result


# Import logging at module level
import logging
