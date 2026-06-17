"""
Unit Tests for HBM Trace Replay and Benchmark Framework

Tests trace replay functionality:
- Multiple trace format support (DDR4, HBM2, HBM3, HBM4)
- CSV, binary, and memory dump format support
- Timing annotation support
- Performance metrics collection
- Row hit rate tracking
- Channel utilization analysis

Usage:
    pytest tests/sim/test_trace_replay.py -v
"""

import os
import sys
import tempfile
import pytest
import json
import csv

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from sim.trace.replay import (
    TraceReplay,
    ReplayConfig,
    ReplayStats,
    ReplayRequest,
    ChannelUtilization,
    TraceFormat,
    HBMVersion,
    replay_trace,
    create_sample_trace,
)
from sim.trace.benchmark import (
    TraceBenchmark,
    BenchmarkConfig,
    BenchmarkResult,
    PerformanceMetrics,
    BenchmarkSource,
    BenchmarkPattern,
    PatternGenerator,
    run_benchmark_suite,
)


class TestTraceReplay:
    """Test TraceReplay functionality"""

    @pytest.fixture
    def temp_trace_file(self):
        """Create a temporary trace file"""
        fd, path = tempfile.mkstemp(suffix='.trace')
        with os.fdopen(fd, 'w') as f:
            # Write some test requests
            for i in range(100):
                op = 'R' if i % 5 != 0 else 'W'
                addr = i * 64
                f.write(f"{op} 0x{addr:x}\n")
        yield path
        os.unlink(path)

    @pytest.fixture
    def csv_trace_file(self):
        """Create a temporary CSV trace file"""
        fd, path = tempfile.mkstemp(suffix='.csv')
        with os.fdopen(fd, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'address', 'op', 'length'])
            writer.writeheader()
            for i in range(50):
                writer.writerow({
                    'timestamp': i,
                    'address': f"0x{i * 64:x}",
                    'op': 'R' if i % 5 != 0 else 'W',
                    'length': 64,
                })
        yield path
        os.unlink(path)

    def test_load_ramulator_format(self, temp_trace_file):
        """Test loading Ramulator format trace"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
        )
        replay = TraceReplay(config)
        count = replay.load_trace()

        assert count == 100
        assert len(replay.requests) == 100

    def test_load_csv_format(self, csv_trace_file):
        """Test loading CSV format trace"""
        config = ReplayConfig(
            trace_file=csv_trace_file,
            format=TraceFormat.CSV,
            hbm_version=HBMVersion.HBM3,
        )
        replay = TraceReplay(config)
        count = replay.load_trace()

        assert count == 50
        assert len(replay.requests) == 50

    def test_address_decoding(self):
        """Test address decoding"""
        config = ReplayConfig(
            trace_file="dummy.trace",
            hbm_version=HBMVersion.HBM3,
        )
        replay = TraceReplay(config)

        # Test address decoding
        decoded = replay._decode_address(0x1000)
        assert 'channel' in decoded
        assert 'bank' in decoded
        assert 'row' in decoded

    def test_row_hit_detection(self):
        """Test row hit detection"""
        config = ReplayConfig(
            trace_file="dummy.trace",
            hbm_version=HBMVersion.HBM3,
        )
        replay = TraceReplay(config)

        # First access should be miss
        hit1 = replay._detect_row_hit(0, 0, 100)
        assert not hit1

        # Same row access should be hit
        replay._bank_states[(0, 0)] = 100
        hit2 = replay._detect_row_hit(0, 0, 100)
        assert hit2

        # Different row should be conflict (not hit)
        hit3 = replay._detect_row_hit(0, 0, 200)
        assert not hit3

    def test_filter_reads(self, temp_trace_file):
        """Test filtering read requests"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
            filter_reads=True,
        )
        replay = TraceReplay(config)
        count = replay.load_trace()

        # Only writes should be loaded
        assert count == 20  # 20% writes
        for req in replay.requests:
            assert req.op_type == 'W'

    def test_filter_writes(self, temp_trace_file):
        """Test filtering write requests"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
            filter_writes=True,
        )
        replay = TraceReplay(config)
        count = replay.load_trace()

        # Only reads should be loaded
        assert count == 80  # 80% reads
        for req in replay.requests:
            assert req.op_type == 'R'

    def test_run_replay(self, temp_trace_file):
        """Test running trace replay"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
            warmup_cycles=10,
            cooldown_cycles=5,
        )
        replay = TraceReplay(config)
        stats = replay.run()

        assert stats.total_requests == 100
        assert stats.read_requests == 80
        assert stats.write_requests == 20
        assert stats.total_cycles > 0
        assert stats.bandwidth_gbps > 0

    def test_channel_utilization(self, temp_trace_file):
        """Test channel utilization tracking"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
            track_channel_util=True,
        )
        replay = TraceReplay(config)
        stats = replay.run()

        assert len(stats.channel_utilization) > 0
        for ch_util in stats.channel_utilization.values():
            assert isinstance(ch_util, ChannelUtilization)

    def test_hbm_version_configs(self):
        """Test HBM version configurations"""
        for version in [HBMVersion.DDR4, HBMVersion.HBM2, HBMVersion.HBM3, HBMVersion.HBM4]:
            config = ReplayConfig(
                trace_file="dummy.trace",
                hbm_version=version,
            )
            replay = TraceReplay(config)

            # Verify configuration
            assert replay.cycle_time_ps > 0
            assert replay.channels > 0

    def test_stats_to_dict(self, temp_trace_file):
        """Test statistics dictionary conversion"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
        )
        replay = TraceReplay(config)
        stats = replay.run()

        stats_dict = stats.to_dict()
        assert isinstance(stats_dict, dict)
        assert 'total_requests' in stats_dict
        assert 'row_hit_rate' in stats_dict
        assert 'bandwidth_gbps' in stats_dict

    def test_print_summary(self, temp_trace_file):
        """Test summary printing"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
        )
        replay = TraceReplay(config)
        replay.run()

        # Should not raise
        replay.print_summary()

    def test_replay_stats_properties(self, temp_trace_file):
        """Test ReplayStats computed properties"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
        )
        replay = TraceReplay(config)
        stats = replay.run()

        # Test computed properties
        assert stats.avg_latency >= 0
        assert 0 <= stats.row_hit_rate <= 1

    def test_max_requests_limit(self, temp_trace_file):
        """Test maximum requests limit"""
        config = ReplayConfig(
            trace_file=temp_trace_file,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
            max_requests=10,
        )
        replay = TraceReplay(config)
        count = replay.load_trace()

        assert count == 10
        assert len(replay.requests) == 10


class TestPatternGenerator:
    """Test PatternGenerator functionality"""

    @pytest.fixture
    def generator(self):
        """Create a pattern generator"""
        return PatternGenerator(HBMVersion.HBM4)

    @pytest.fixture
    def temp_output(self):
        """Create temporary output file"""
        fd, path = tempfile.mkstemp(suffix='.trace')
        os.close(fd)
        os.unlink(path)  # Remove so generator can create it
        yield path
        if os.path.exists(path):
            os.unlink(path)

    def test_generate_sequential(self, generator, temp_output):
        """Test sequential pattern generation"""
        count = generator.generate_trace_file(
            BenchmarkPattern.SYNTH_READ,
            temp_output,
            num_requests=1000,
        )
        assert count == 1000
        assert os.path.exists(temp_output)

        # Read and verify
        with open(temp_output) as f:
            lines = f.readlines()
            assert len(lines) == 1000

    def test_generate_random(self, generator, temp_output):
        """Test random pattern generation"""
        count = generator.generate_trace_file(
            BenchmarkPattern.RAND_READ,
            temp_output,
            num_requests=500,
        )
        assert count == 500

    def test_generate_stride(self, generator, temp_output):
        """Test stride pattern generation"""
        count = generator.generate_trace_file(
            BenchmarkPattern.STRIDE,
            temp_output,
            num_requests=500,
        )
        assert count == 500

    def test_generate_transpose(self, generator, temp_output):
        """Test transpose pattern generation"""
        count = generator.generate_trace_file(
            BenchmarkPattern.TRANSPOSE,
            temp_output,
            num_requests=500,
        )
        assert count == 500

    def test_generate_hotspot(self, generator, temp_output):
        """Test hotspot pattern generation"""
        count = generator.generate_trace_file(
            BenchmarkPattern.HOTSPOT,
            temp_output,
            num_requests=500,
        )
        assert count == 500

    def test_all_patterns(self, generator, temp_output):
        """Test all pattern types"""
        patterns = [
            BenchmarkPattern.SYNTH_READ,
            BenchmarkPattern.SYNTH_WRITE,
            BenchmarkPattern.RAND_READ,
            BenchmarkPattern.RAND_WRITE,
            BenchmarkPattern.STRIDE,
            BenchmarkPattern.TRANSPOSE,
            BenchmarkPattern.HOTSPOT,
        ]

        for pattern in patterns:
            path = temp_output.replace('.trace', f'_{pattern.value}.trace')
            count = generator.generate_trace_file(
                pattern,
                path,
                num_requests=100,
            )
            assert count == 100
            assert os.path.exists(path)
            os.unlink(path)


class TestTraceBenchmark:
    """Test TraceBenchmark functionality"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        path = tempfile.mkdtemp()
        yield path
        # Cleanup
        import shutil
        shutil.rmtree(path, ignore_errors=True)

    @pytest.fixture
    def benchmark_config(self, temp_output_dir):
        """Create benchmark configuration"""
        return BenchmarkConfig(
            source=BenchmarkSource.PATTERNS,
            pattern=BenchmarkPattern.SYNTH_READ,
            hbm_version=HBMVersion.HBM4,
            pattern_size=100,
            output_dir=temp_output_dir,
            verbose=False,
        )

    def test_run_pattern_benchmark(self, benchmark_config):
        """Test running pattern benchmark"""
        bench = TraceBenchmark(benchmark_config)
        result = bench.run()

        assert isinstance(result, BenchmarkResult)
        assert result.name == "synth_read"
        assert result.config.pattern == BenchmarkPattern.SYNTH_READ

    def test_metrics_collection(self, benchmark_config):
        """Test metrics collection"""
        bench = TraceBenchmark(benchmark_config)
        result = bench.run()
        metrics = result.metrics

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_requests == 100
        assert metrics.bandwidth_gbps >= 0
        assert 0 <= metrics.efficiency <= 1

    def test_passing_criteria(self, benchmark_config):
        """Test passing criteria"""
        bench = TraceBenchmark(benchmark_config)
        result = bench.run()

        # Result should have passed or failed flag
        assert isinstance(result.passed, bool)

    def test_save_results_json(self, benchmark_config):
        """Test saving results to JSON"""
        bench = TraceBenchmark(benchmark_config)
        bench.run()

        output_file = os.path.join(benchmark_config.output_dir, "test_results.json")
        bench.save_results(output_file)

        assert os.path.exists(output_file)

        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
            assert 'timestamp' in data
            assert 'results' in data

    def test_save_results_csv(self, benchmark_config):
        """Test saving results to CSV"""
        bench = TraceBenchmark(benchmark_config)
        bench.run()

        output_file = os.path.join(benchmark_config.output_dir, "test_results.csv")
        bench.save_csv(output_file)

        assert os.path.exists(output_file)

        # Verify CSV content
        with open(output_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1

    def test_multiple_patterns(self, temp_output_dir):
        """Test running multiple patterns"""
        results = []
        patterns = [BenchmarkPattern.SYNTH_READ, BenchmarkPattern.RAND_READ]

        for pattern in patterns:
            config = BenchmarkConfig(
                source=BenchmarkSource.PATTERNS,
                pattern=pattern,
                hbm_version=HBMVersion.HBM4,
                pattern_size=50,
                output_dir=temp_output_dir,
                verbose=False,
            )
            bench = TraceBenchmark(config)
            result = bench.run()
            results.append(result)

        assert len(results) == 2

    def test_convert_stats_to_metrics(self, temp_output_dir):
        """Test converting ReplayStats to PerformanceMetrics"""
        # First create a trace replay
        fd, path = tempfile.mkstemp(suffix='.trace')
        with os.fdopen(fd, 'w') as f:
            for i in range(100):
                f.write(f"R 0x{i * 64:x}\n")

        from sim.trace.replay import TraceReplay, ReplayConfig

        config = ReplayConfig(
            trace_file=path,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM4,
        )
        replay = TraceReplay(config)
        replay_stats = replay.run()

        # Now convert via benchmark
        bench_config = BenchmarkConfig(
            source=BenchmarkSource.PATTERNS,
            pattern=BenchmarkPattern.SYNTH_READ,
            hbm_version=HBMVersion.HBM4,
            pattern_size=100,
            output_dir=temp_output_dir,
        )
        bench = TraceBenchmark(bench_config)
        metrics = bench._convert_stats_to_metrics(replay_stats)

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_requests == replay_stats.total_requests

        os.unlink(path)

    def test_aggregate_metrics(self):
        """Test aggregating metrics from multiple runs"""
        bench_config = BenchmarkConfig(
            source=BenchmarkSource.PATTERNS,
            pattern=BenchmarkPattern.SYNTH_READ,
            hbm_version=HBMVersion.HBM4,
            pattern_size=50,
        )
        bench = TraceBenchmark(bench_config)

        # Create fake metrics
        metrics_list = [
            PerformanceMetrics(total_requests=50, bandwidth_gbps=100.0, efficiency=0.5),
            PerformanceMetrics(total_requests=50, bandwidth_gbps=200.0, efficiency=0.6),
            PerformanceMetrics(total_requests=50, bandwidth_gbps=150.0, efficiency=0.55),
        ]

        agg = bench._aggregate_metrics(metrics_list)

        assert agg.total_requests == 150
        assert agg.bandwidth_gbps == 150.0  # Mean
        assert agg.efficiency == pytest.approx(0.55, rel=0.01)

    def test_channel_balance_score(self):
        """Test channel balance score calculation"""
        bench_config = BenchmarkConfig(
            source=BenchmarkSource.PATTERNS,
            pattern=BenchmarkPattern.SYNTH_READ,
            hbm_version=HBMVersion.HBM4,
            num_channels=32,
        )
        bench = TraceBenchmark(bench_config)

        # Perfect balance
        counts = [100] * 32
        score = bench._calculate_balance_score(counts)
        assert score == 1.0

        # Slightly unbalanced (2 channels with different loads)
        counts = [200] + [100] * 31
        score = bench._calculate_balance_score(counts)
        assert score < 1.0  # Some imbalance

    def test_variance_percent(self):
        """Test variance percentage calculation"""
        bench_config = BenchmarkConfig(
            source=BenchmarkSource.PATTERNS,
            pattern=BenchmarkPattern.SYNTH_READ,
            hbm_version=HBMVersion.HBM4,
        )
        bench = TraceBenchmark(bench_config)

        # Perfect balance
        counts = [100] * 32
        variance = bench._calculate_variance_percent(counts)
        assert variance == 0.0

    def test_replay_from_trace_file(self, temp_output_dir):
        """Test replay from actual trace file"""
        # Create a test trace file
        fd, trace_path = tempfile.mkstemp(suffix='.trace')
        with os.fdopen(fd, 'w') as f:
            for i in range(100):
                f.write(f"R 0x{i * 64:x}\n")

        config = BenchmarkConfig(
            source=BenchmarkSource.TRACE,
            trace_file=trace_path,
            format=TraceFormat.RAMULATOR,
            hbm_version=HBMVersion.HBM3,
            pattern_size=50,
            output_dir=temp_output_dir,
            verbose=False,
        )

        bench = TraceBenchmark(config)
        result = bench.run()

        assert result.metrics.total_requests == 50
        assert result.metrics.bandwidth_gbps > 0

        os.unlink(trace_path)


class TestReplayConvenienceFunctions:
    """Test convenience functions"""

    def test_replay_trace_function(self):
        """Test replay_trace convenience function"""
        # Create temp trace
        fd, path = tempfile.mkstemp(suffix='.trace')
        with os.fdopen(fd, 'w') as f:
            for i in range(50):
                f.write(f"R 0x{i * 64:x}\n")

        try:
            stats = replay_trace(
                trace_file=path,
                format=TraceFormat.RAMULATOR,
                hbm_version=HBMVersion.HBM3,
                max_requests=25,
                verbose=False,
            )

            assert stats.total_requests == 25
        finally:
            os.unlink(path)

    def test_create_sample_trace(self):
        """Test create_sample_trace function"""
        fd, path = tempfile.mkstemp(suffix='.trace')
        os.close(fd)
        os.unlink(path)

        try:
            patterns = ['sequential', 'random', 'stride', 'transpose']

            for pattern in patterns:
                p = path.replace('.trace', f'_{pattern}.trace')
                create_sample_trace(p, pattern=pattern, num_requests=100)

                assert os.path.exists(p)
                with open(p) as f:
                    lines = f.readlines()
                    assert len(lines) == 100

                os.unlink(p)
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestHBMVersionCompatibility:
    """Test HBM version compatibility"""

    def test_hbm4_address_decoding(self):
        """Test HBM4 address decoding"""
        config = ReplayConfig(
            trace_file="dummy.trace",
            hbm_version=HBMVersion.HBM4,
        )
        replay = TraceReplay(config)

        # Test with various addresses
        for addr in [0x1000, 0x10000, 0x100000, 0x10000000]:
            decoded = replay._decode_address(addr)
            assert decoded['channel'] < 32  # HBM4 has 32 channels

    def test_hbm3_address_decoding(self):
        """Test HBM3 address decoding"""
        config = ReplayConfig(
            trace_file="dummy.trace",
            hbm_version=HBMVersion.HBM3,
        )
        replay = TraceReplay(config)

        decoded = replay._decode_address(0x1000)
        assert decoded['channel'] < 8  # HBM3 has 8 channels

    def test_ddr4_address_decoding(self):
        """Test DDR4 address decoding"""
        config = ReplayConfig(
            trace_file="dummy.trace",
            hbm_version=HBMVersion.DDR4,
        )
        replay = TraceReplay(config)

        decoded = replay._decode_address(0x1000)
        assert decoded['channel'] == 0  # DDR4 has 1 channel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
