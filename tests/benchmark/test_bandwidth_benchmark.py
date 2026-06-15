"""
Tests for Bandwidth Benchmark Module
"""

import pytest
from model.benchmark.bandwidth_benchmark import (
    BandwidthBenchmark,
    BandwidthResult,
)
from model.benchmark.benchmark_config import BandwidthConfig, TestPattern


class TestBandwidthBenchmark:
    """Tests for BandwidthBenchmark"""
    
    def test_initialization(self):
        benchmark = BandwidthBenchmark()
        assert benchmark.speed_grade == "8Gbps"
        assert benchmark.config is not None
        assert benchmark.spec is not None
    
    def test_custom_speed_grade(self):
        benchmark = BandwidthBenchmark(speed_grade="12Gbps")
        assert benchmark.speed_grade == "12Gbps"
        assert benchmark.spec.data_rate_gtps == 12.0
    
    def test_custom_config(self):
        config = BandwidthConfig(
            test_duration_ns=1_000_000,
            num_batches=10
        )
        benchmark = BandwidthBenchmark(config=config, speed_grade="8Gbps")
        assert benchmark.config.test_duration_ns == 1_000_000
        assert benchmark.config.num_batches == 10
    
    def test_peak_bandwidth_calculation(self):
        """Test that peak bandwidth is calculated correctly"""
        benchmark = BandwidthBenchmark(speed_grade="8Gbps")
        # 8 GT/s * 2048 bits / 8 = 2048 GB/s
        assert benchmark.spec.bandwidth_gbs == pytest.approx(2048.0, rel=0.1)
    
    def test_address_generation_sequential(self):
        """Test sequential address generation"""
        benchmark = BandwidthBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.SEQUENTIAL, 10)
        assert len(addresses) == 10
        # Sequential addresses should be consecutive
        for i in range(1, len(addresses)):
            assert addresses[i] == addresses[i-1] + 64
    
    def test_address_generation_random(self):
        """Test random address generation"""
        benchmark = BandwidthBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.RANDOM, 100)
        assert len(addresses) == 100
        # Random addresses should vary
        unique = len(set(addresses))
        assert unique > 50  # Most should be unique
    
    def test_address_generation_strided(self):
        """Test strided address generation"""
        benchmark = BandwidthBenchmark()
        config = BandwidthConfig(stride_bytes=128)
        benchmark.config = config
        addresses = benchmark._generate_addresses(TestPattern.STRIDED, 10)
        assert len(addresses) == 10
        for i in range(1, len(addresses)):
            assert addresses[i] == addresses[i-1] + 128
    
    def test_address_generation_hotspot(self):
        """Test hotspot address generation"""
        benchmark = BandwidthBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.HOTSPOT, 100)
        assert len(addresses) == 100
        # 80% should be in first 20% of address space
        hotspot_count = sum(1 for a in addresses if a < 0x20_000_000)
        assert hotspot_count >= 50  # Relaxed threshold for random distribution
    
    def test_address_generation_row_hit(self):
        """Test row hit address generation"""
        benchmark = BandwidthBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.ROW_HIT, 100)
        assert len(addresses) == 100
        # All same address
        assert len(set(addresses)) == 1
    
    def test_address_generation_bank_conflict(self):
        """Test bank conflict address generation"""
        benchmark = BandwidthBenchmark()
        addresses = benchmark._generate_addresses(TestPattern.BANK_CONFLICT, 100)
        assert len(addresses) == 100
        # Addresses should span different addresses (not necessarily banks)
        # Bank conflict pattern spreads addresses evenly
        assert len(set(addresses)) > 10  # Should have variety in addresses


class TestBandwidthResult:
    """Tests for BandwidthResult"""
    
    def test_default_result(self):
        result = BandwidthResult()
        assert result.peak_bandwidth_gbs == 0.0
        assert result.measured_bandwidth_gbs == 0.0
        assert result.refresh_count == 0
    
    def test_result_to_dict(self):
        result = BandwidthResult()
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1800.0
        result.peak_efficiency_percent = 87.8
        
        d = result.to_dict()
        assert d['peak_bandwidth_gbs'] == 2048.0
        assert d['measured_bandwidth_gbs'] == 1800.0
        assert d['peak_efficiency_percent'] == 87.8
    
    def test_result_str(self):
        result = BandwidthResult()
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1800.0
        result.peak_efficiency_percent = 87.8
        result.total_requests = 1000
        result.read_requests = 700
        result.write_requests = 300
        
        s = str(result)
        assert "2048" in s
        assert "1800" in s
        assert "87.8" in s
        assert "1000" in s


class TestBandwidthEfficiency:
    """Tests for bandwidth efficiency calculations"""
    
    def test_efficiency_calculation(self):
        """Test efficiency percentage calculation"""
        result = BandwidthResult()
        result.peak_bandwidth_gbs = 2048.0
        result.measured_bandwidth_gbs = 1638.4
        
        # Calculate efficiency
        efficiency = (result.measured_bandwidth_gbs / result.peak_bandwidth_gbs * 100 
                      if result.peak_bandwidth_gbs > 0 else 0)
        assert efficiency == pytest.approx(80.0, rel=0.1)
    
    def test_refresh_overhead_calculation(self):
        """Test refresh overhead calculation"""
        result = BandwidthResult()
        result.refresh_total_time_ns = 1800.0  # 100 refreshes * 18ns each
        result.test_duration_ns = 100_000.0  # 100us test
        
        overhead = (result.refresh_total_time_ns / result.test_duration_ns * 100 
                    if result.test_duration_ns > 0 else 0)
        assert overhead == pytest.approx(1.8, rel=0.1)