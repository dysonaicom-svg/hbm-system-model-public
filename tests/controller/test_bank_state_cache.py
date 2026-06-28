"""Tests for BankStateCache with LRU eviction."""

import pytest
from model.controller.bank_state_cache import BankStateCache, fast_check_bank_state


class TestBankStateCache:
    """Test BankStateCache functionality."""

    def test_cache_basic_operations(self):
        """Test basic get/set operations."""
        cache = BankStateCache(max_size=100)

        # Initially empty
        assert cache.get(0, 0, 0) is None
        assert cache.hits == 0
        assert cache.misses == 1

        # Set and get
        cache.set(0, 0, 0, "ACTIVE", 100)
        result = cache.get(0, 0, 0)
        assert result == ("ACTIVE", 100)
        assert cache.hits == 1

    def test_cache_hit_rate(self):
        """Test hit rate calculation."""
        cache = BankStateCache(max_size=100)

        # Miss
        cache.get(0, 0, 0)
        assert cache.hit_rate == 0.0

        # Hit
        cache.set(0, 0, 0, "IDLE", 100)
        cache.get(0, 0, 0)
        assert cache.hit_rate == 0.5

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = BankStateCache(max_size=2)

        # Fill cache
        cache.set(0, 0, 0, "ACTIVE", 100)
        cache.set(0, 0, 1, "IDLE", 101)

        # Third entry triggers eviction of oldest (0,0,0)
        cache.set(0, 0, 2, "BUSY", 102)

        assert cache.get(0, 0, 0) is None  # Evicted
        assert cache.get(0, 0, 1) == ("IDLE", 101)
        assert cache.get(0, 0, 2) == ("BUSY", 102)

    def test_lru_access_order(self):
        """Test that access updates LRU order."""
        cache = BankStateCache(max_size=3)

        cache.set(0, 0, 0, "A", 0)
        cache.set(0, 0, 1, "B", 1)
        cache.set(0, 0, 2, "C", 2)

        # Access 0 to make it most recently used
        cache.get(0, 0, 0)

        # New entry should evict 1 (oldest)
        cache.set(0, 0, 3, "D", 3)

        assert cache.get(0, 0, 0) == ("A", 0)  # Still there
        assert cache.get(0, 0, 1) is None  # Evicted
        assert cache.get(0, 0, 2) == ("C", 2)

    def test_invalidate(self):
        """Test cache invalidation."""
        cache = BankStateCache()

        cache.set(0, 0, 0, "ACTIVE", 100)
        assert cache.get(0, 0, 0) == ("ACTIVE", 100)

        cache.invalidate(0, 0, 0)
        assert cache.get(0, 0, 0) is None

    def test_clear(self):
        """Test cache clearing."""
        cache = BankStateCache()

        cache.set(0, 0, 0, "ACTIVE", 100)
        cache.set(0, 0, 1, "IDLE", 101)

        cache.clear()

        assert cache.size == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_reset_stats(self):
        """Test resetting stats without clearing cache."""
        cache = BankStateCache()

        cache.set(0, 0, 0, "ACTIVE", 100)
        cache.get(0, 0, 0)
        cache.get(0, 0, 1)  # Miss

        cache.reset_stats()

        assert cache.hits == 0
        assert cache.misses == 0
        assert cache.size == 1  # Cache still has entry

    def test_update_existing(self):
        """Test updating existing cache entry."""
        cache = BankStateCache()

        cache.set(0, 0, 0, "ACTIVE", 100)
        cache.set(0, 0, 0, "IDLE", 200)  # Update

        assert cache.get(0, 0, 0) == ("IDLE", 200)
        assert cache.size == 1  # No size increase

    def test_different_channels(self):
        """Test entries across different channels."""
        cache = BankStateCache(max_size=4)

        cache.set(0, 0, 0, "A", 0)
        cache.set(1, 0, 0, "B", 1)
        cache.set(0, 1, 0, "C", 2)
        cache.set(0, 0, 1, "D", 3)

        assert cache.get(0, 0, 0) == ("A", 0)
        assert cache.get(1, 0, 0) == ("B", 1)
        assert cache.get(0, 1, 0) == ("C", 2)
        assert cache.get(0, 0, 1) == ("D", 3)

    def test_get_stats(self):
        """Test get_stats method."""
        cache = BankStateCache(max_size=100)

        cache.set(0, 0, 0, "ACTIVE", 100)
        cache.get(0, 0, 0)  # Hit
        cache.get(0, 0, 1)  # Miss

        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5
        assert stats['size'] == 1
        assert stats['max_size'] == 100


class TestFastCheckBankState:
    """Test fast_check_bank_state helper function."""

    def test_fast_check_hit_idle(self):
        """Test fast check returns True for IDLE."""
        cache = BankStateCache()
        cache.set(0, 0, 0, "IDLE", 100)

        result = fast_check_bank_state(cache, 0, 0, 0)
        assert result is True

    def test_fast_check_hit_active(self):
        """Test fast check returns False for ACTIVE."""
        cache = BankStateCache()
        cache.set(0, 0, 0, "ACTIVE", 100)

        result = fast_check_bank_state(cache, 0, 0, 0)
        assert result is False

    def test_fast_check_miss(self):
        """Test fast check returns None on miss."""
        cache = BankStateCache()

        result = fast_check_bank_state(cache, 0, 0, 0)
        assert result is None


class TestBankStateCacheIntegration:
    """Integration tests for scheduler integration."""

    def test_cache_size_limits(self):
        """Test cache respects max_size limit."""
        cache = BankStateCache(max_size=10)

        # Add more than max_size entries
        for i in range(20):
            cache.set(i, 0, 0, "STATE", i)

        assert cache.size == 10

    def test_concurrent_access_pattern(self):
        """Test typical scheduler access pattern (hot banks)."""
        cache = BankStateCache(max_size=4)

        # Simulate pattern: banks 0, 1 are hot, accessed frequently
        for _ in range(5):
            cache.get(0, 0, 0)
            cache.set(0, 0, 0, "ACTIVE", 0)
            cache.get(1, 0, 1)
            cache.set(1, 0, 1, "IDLE", 0)

        # Add some cold banks
        cache.set(2, 0, 2, "IDLE", 0)
        cache.set(3, 0, 3, "IDLE", 0)

        # Hot banks should still be in cache
        assert cache.get(0, 0, 0) is not None
        assert cache.get(1, 0, 1) is not None

        # Hit rate should be reasonable
        total = cache.hits + cache.misses
        assert cache.hit_rate > 0.6  # >60% hit rate target
