"""
Bank State Cache with LRU Eviction

Provides caching for bank state lookups to improve scheduler performance.
Based on P7.1 profiling, this helps reduce repeated bank state queries.

NOTE: P7.1 profiling showed main bottleneck is simulator init, not scheduler.
This cache helps when scheduler makes many repeated lookups for the same banks.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, Any
from collections import OrderedDict


@dataclass
class BankStateCache:
    """Bank state LRU cache for efficient scheduler lookups.

    Caches (channel, pseudo_channel, bank) -> (state, timestamp) mappings
    with LRU eviction when max_size is reached.

    Attributes:
        max_size: Maximum number of entries before LRU eviction
        hits: Number of cache hits
        misses: Number of cache misses
    """
    max_size: int = 1024
    hits: int = 0
    misses: int = 0
    _cache: OrderedDict = field(default_factory=OrderedDict)

    def get(self, channel: int, pseudo_channel: int, bank: int) -> Optional[Tuple[str, int]]:
        """Get cached bank state.

        Args:
            channel: Channel ID (0-31)
            pseudo_channel: Pseudo-channel ID (0-1)
            bank: Bank ID (0-15)

        Returns:
            Tuple of (state, timestamp) or None if not cached
        """
        key = (channel, pseudo_channel, bank)
        result = self._cache.get(key)
        if result is not None:
            self.hits += 1
            # Move to end (most recently used)
            self._cache.move_to_end(key)
        else:
            self.misses += 1
        return result

    def set(self, channel: int, pseudo_channel: int, bank: int, state: str, timestamp: int):
        """Set cached bank state.

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bank: Bank ID
            state: Bank state string ("IDLE", "ACTIVE", "BUSY", etc.)
            timestamp: Current simulation cycle
        """
        key = (channel, pseudo_channel, bank)
        # If key exists, update and move to end
        if key in self._cache:
            self._cache.move_to_end(key)
        # Evict LRU if at capacity
        elif len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        self._cache[key] = (state, timestamp)

    def invalidate(self, channel: int, pseudo_channel: int, bank: int):
        """Invalidate a specific cache entry.

        Args:
            channel: Channel ID
            pseudo_channel: Pseudo-channel ID
            bank: Bank ID
        """
        key = (channel, pseudo_channel, bank)
        self._cache.pop(key, None)

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def reset_stats(self):
        """Reset hit/miss counters without clearing cache."""
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            Hit rate as a float between 0.0 and 1.0
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, size
        """
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hit_rate,
            'size': self.size,
            'max_size': self.max_size,
        }


def fast_check_bank_state(cache: BankStateCache, channel: int,
                          pseudo_channel: int, bank: int) -> Optional[bool]:
    """Fast check if bank is IDLE using cache.

    Args:
        cache: BankStateCache instance
        channel: Channel ID
        pseudo_channel: Pseudo-channel ID
        bank: Bank ID

    Returns:
        True if IDLE, False if not IDLE, None if not cached
    """
    result = cache.get(channel, pseudo_channel, bank)
    if result is None:
        return None
    return result[0] == "IDLE"
