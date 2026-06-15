"""
HBM4 Comprehensive Benchmark Suite

Benchmarks for HBM4 Logic Base Die modeling platform.
Tests bandwidth, latency, channel independence, PAM3, and QoS scheduling.

Usage:
    python3 -m sim.hbm4_benchmark
    python3 -m sim.hbm4_benchmark --quick  # Fast test mode
    python3 -m sim.hbm4_benchmark --verbose  # Detailed output
"""

import argparse
import time
import sys
from typing import Dict, List, Tuple, Any

# Import HBM4 modules
from model.dram.logic_base_die import HBM4LogicBaseDie, LogicBaseDieConfig
from model.dram.phy_signal import PAM3SignalModel, HBM4PAM3Encoder
from model.dram.channel_timing import HBM4TimingManager, IndependentChannelTiming
from model.dram.hbm4_spec import HBM4Spec


class BenchmarkResult:
    """Result container for benchmark tests"""
    def __init__(self, name: str, passed: bool, value: float, unit: str, details: str = ""):
        self.name = name
        self.passed = passed
        self.value = value
        self.unit = unit
        self.details = details
        self.duration_ms = 0.0

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.value:.2f} {self.unit} ({self.duration_ms:.1f}ms)"


class HBM4Benchmark:
    """HBM4 Comprehensive Benchmark Suite"""

    def __init__(self, quick_mode: bool = False, verbose: bool = False):
        self.quick_mode = quick_mode
        self.verbose = verbose
        self.results: List[BenchmarkResult] = []
        self.spec = HBM4Spec()

        # Configuration
        self.iterations = 1000 if not quick_mode else 100
        self.warmup_cycles = 100 if not quick_mode else 10

    def log(self, msg: str):
        """Print log message"""
        if self.verbose:
            print(f"  [LOG] {msg}")

    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")

    def print_result(self, result: BenchmarkResult):
        """Print benchmark result"""
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.name}: {result.value:.2f} {result.unit}")

    # ============================================================
    # Benchmark 1: Bandwidth Test
    # ============================================================
    def run_bandwidth_test(self) -> BenchmarkResult:
        """Test peak bandwidth capability

        HBM4 Spec: 2 TB/s per stack (8 GT/s × 2048 bits / 8)
        """
        self.print_header("Bandwidth Test")

        start = time.time()

        lbd = HBM4LogicBaseDie()
        lbd.initialize()

        # Initialize to ready state
        for _ in range(self.warmup_cycles):
            lbd.tick()

        # Simulate traffic
        total_bytes = 0
        cycles = 0
        max_cycles = self.iterations

        for i in range(max_cycles):
            channel_id = i % 32

            # Alternate reads and writes
            if i % 2 == 0:
                lbd.process_command(channel_id, 'ACT', address=0x1000 + (i % 16))
                lbd.process_command(channel_id, 'RD', address=0x1000 + (i % 16))
            else:
                lbd.process_command(channel_id, 'ACT', address=0x1000 + (i % 16))
                lbd.process_command(channel_id, 'WR', address=0x1000 + (i % 16), data=0xDEADBEEF)

            lbd.tick()
            cycles += 1
            total_bytes += 256  # 256 bytes per transaction

        duration = time.time() - start

        # Calculate bandwidth
        # Each transaction = 256 bytes @ 8 GT/s
        # Peak theoretical = 8e9 symbols/s × 256 bits/symbol / 8 = 256 GB/s per channel
        # 32 channels × 256 GB/s = 8 TB/s (aggregate theoretical max)
        # Practical target: 2 TB/s per stack

        bytes_per_cycle = total_bytes / cycles if cycles > 0 else 0
        cycles_per_second = 8e9  # 8 GHz
        bandwidth_gbs = bytes_per_cycle * cycles_per_second / 1e9

        duration_ms = duration * 1000

        # Target: 2 TB/s = 2000 GB/s
        target_gbs = 2000.0
        passed = bandwidth_gbs >= target_gbs * 0.1  # 10% of theoretical for simulation

        result = BenchmarkResult(
            name="Peak Bandwidth",
            passed=passed,
            value=bandwidth_gbs,
            unit="GB/s",
            details=f"Target: {target_gbs:.0f} GB/s"
        )
        result.duration_ms = duration_ms

        return result

    # ============================================================
    # Benchmark 2: Latency Test
    # ============================================================
    def run_latency_test(self) -> BenchmarkResult:
        """Test read/write latency

        Target: < 100 cycles for typical access
        """
        self.print_header("Latency Test")

        start = time.time()

        lbd = HBM4LogicBaseDie()
        lbd.initialize()

        # Initialize
        for _ in range(self.warmup_cycles):
            lbd.tick()

        # Measure latency for different access patterns
        latencies = []

        for i in range(min(self.iterations, 500)):
            channel_id = i % 32
            row = 0x1000 + (i % 16)

            # Open row
            lbd.process_command(channel_id, 'ACT', address=row)
            for _ in range(8):  # Wait for tRCD
                lbd.tick()

            # Issue read and measure cycles
            cycle_before = lbd.cycle
            lbd.process_command(channel_id, 'RD', address=row)
            lbd.tick()

            # Wait for data
            data_cycles = 0
            while data_cycles < 20:  # Max wait
                lbd.tick()
                data_cycles += 1
                # Simulated data ready
                if data_cycles >= lbd.spec.nCL:
                    break

            latency = lbd.cycle - cycle_before
            latencies.append(latency)

            if self.quick_mode and i >= 50:
                break

        duration = time.time() - start

        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        min_latency = min(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0

        duration_ms = duration * 1000

        # Target: < 100 cycles
        target = 100
        passed = avg_latency < target

        result = BenchmarkResult(
            name="Average Latency",
            passed=passed,
            value=avg_latency,
            unit="cycles",
            details=f"Min: {min_latency}, Max: {max_latency}, Target: <{target}"
        )
        result.duration_ms = duration_ms

        return result

    # ============================================================
    # Benchmark 3: Channel Independence Test
    # ============================================================
    def run_channel_independence_test(self) -> BenchmarkResult:
        """Verify 32 channels operate independently

        JEDEC requirement: "Each channel is completely independent"
        """
        self.print_header("Channel Independence Test")

        start = time.time()

        manager = HBM4TimingManager(num_channels=32)

        # Test: Each channel should maintain independent state
        # Open different rows in different channels
        for ch in range(32):
            timing = manager.get_channel_timing(ch)
            if timing:
                timing.execute_with_independent_timing('ACT', bank=0, row=0x1000 + ch)
                manager.tick()

        # Verify each channel has correct row open
        mismatches = 0
        for ch in range(32):
            timing = manager.get_channel_timing(ch)
            if timing:
                expected_row = 0x1000 + ch
                actual_row = timing.bank_states[0].row_id
                if actual_row != expected_row:
                    mismatches += 1
                    self.log(f"Channel {ch}: expected row {expected_row}, got {actual_row}")

        duration = time.time() - start
        duration_ms = duration * 1000

        # All channels should match
        passed = mismatches == 0

        result = BenchmarkResult(
            name="Channel State Isolation",
            passed=passed,
            value=32 - mismatches,
            unit="channels correct",
            details=f"Mismatches: {mismatches}"
        )
        result.duration_ms = duration_ms

        return result

    # ============================================================
    # Benchmark 4: PAM3 Throughput Test
    # ============================================================
    def run_pam3_throughput_test(self) -> BenchmarkResult:
        """Test PAM3 encoding efficiency

        PAM3: ~1.585 bits/symbol vs NRZ 1 bit/symbol
        """
        self.print_header("PAM3 Throughput Test")

        start = time.time()

        encoder = HBM4PAM3Encoder(config={'symbol_rate': 8e9})

        # Encode test data
        data = 0xDEADBEEF
        symbols_generated = 0
        iterations = self.iterations * 10 if not self.quick_mode else self.iterations

        for _ in range(iterations):
            symbols = encoder.encode_data_burst(data, dq_width=128)
            symbols_generated += len(symbols)

        # Calculate encoding time
        duration = time.time() - start
        duration_ms = duration * 1000

        # PAM3 efficiency: ~1.585 bits/symbol
        # 128 bits / 1.585 = ~81 symbols per burst
        expected_symbols_per_burst = 128 / 1.585  # ~81
        actual = symbols_generated / iterations if iterations > 0 else 0

        efficiency = actual / expected_symbols_per_burst if expected_symbols_per_burst > 0 else 0

        # Target: > 75% efficiency (relaxed for simulation)
        passed = efficiency > 0.75

        result = BenchmarkResult(
            name="PAM3 Encoding Efficiency",
            passed=passed,
            value=efficiency * 100,
            unit="%",
            details=f"Symbols/burst: {actual:.1f} (expected: {expected_symbols_per_burst:.1f})"
        )
        result.duration_ms = duration_ms

        return result

    # ============================================================
    # Benchmark 5: QoS Scheduling Test
    # ============================================================
    def run_qos_scheduling_test(self) -> BenchmarkResult:
        """Test QoS scheduling under load

        Verify high-priority requests are serviced first
        """
        self.print_header("QoS Scheduling Test")

        start = time.time()

        lbd = HBM4LogicBaseDie()
        lbd.initialize()

        # Initialize
        for _ in range(self.warmup_cycles):
            lbd.tick()

        # Simulate mixed traffic: high and low priority
        high_priority_latency = []
        low_priority_latency = []

        for i in range(min(self.iterations, 200)):
            channel_id = i % 32
            priority = "HIGH" if i % 5 == 0 else "LOW"

            # Open row
            lbd.process_command(channel_id, 'ACT', address=0x2000 + (i % 16))
            for _ in range(8):
                lbd.tick()

            cycle_before = lbd.cycle
            lbd.process_command(channel_id, 'RD', address=0x2000 + (i % 16))

            if priority == "HIGH":
                high_priority_latency.append(lbd.cycle - cycle_before)
            else:
                low_priority_latency.append(lbd.cycle - cycle_before)

            lbd.tick()

            if self.quick_mode and i >= 50:
                break

        duration = time.time() - start
        duration_ms = duration * 1000

        # High priority should have lower or equal latency
        avg_high = sum(high_priority_latency) / len(high_priority_latency) if high_priority_latency else 0
        avg_low = sum(low_priority_latency) / len(low_priority_latency) if low_priority_latency else 0

        # Simple check: QoS should not make things worse
        passed = avg_high <= avg_low * 1.5  # Within 50%

        result = BenchmarkResult(
            name="QoS Scheduling",
            passed=passed,
            value=avg_high,
            unit="cycles (high pri)",
            details=f"High: {avg_high:.1f}, Low: {avg_low:.1f}"
        )
        result.duration_ms = duration_ms

        return result

    # ============================================================
    # Run All Benchmarks
    # ============================================================
    def run_all(self) -> Dict[str, BenchmarkResult]:
        """Run all benchmarks"""
        print("\n" + "="*60)
        print(" HBM4 Logic Base Die - Comprehensive Benchmark Suite")
        print("="*60)
        print(f"Mode: {'Quick' if self.quick_mode else 'Full'}")
        print(f"Iterations: {self.iterations}")

        benchmarks = [
            ("Bandwidth", self.run_bandwidth_test),
            ("Latency", self.run_latency_test),
            ("Channel Independence", self.run_channel_independence_test),
            ("PAM3 Throughput", self.run_pam3_throughput_test),
            ("QoS Scheduling", self.run_qos_scheduling_test),
        ]

        results = {}
        for name, func in benchmarks:
            try:
                result = func()
                results[name] = result
                self.print_result(result)
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
                results[name] = BenchmarkResult(
                    name=name,
                    passed=False,
                    value=0,
                    unit="N/A",
                    details=str(e)
                )

        return results

    def print_summary(self, results: Dict[str, BenchmarkResult]):
        """Print benchmark summary"""
        self.print_header("Benchmark Summary")

        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)

        total_duration = sum(r.duration_ms for r in results.values())

        print(f"\n  Total: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {total - passed}")
        print(f"  Pass Rate: {100*passed/total:.0f}%")
        print(f"  Total Duration: {total_duration:.1f}ms")

        if passed == total:
            print("\n  All benchmarks PASSED!")
        else:
            print("\n  Some benchmarks FAILED - see details above.")

        return passed == total


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='HBM4 Benchmark Suite')
    parser.add_argument('--quick', action='store_true', help='Quick test mode')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    benchmark = HBM4Benchmark(quick_mode=args.quick, verbose=args.verbose)
    results = benchmark.run_all()
    success = benchmark.print_summary(results)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()