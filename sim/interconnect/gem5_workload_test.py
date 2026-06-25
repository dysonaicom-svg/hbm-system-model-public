#!/usr/bin/env python3
"""
gem5 Workload Test for HBM4
Tests gem5 bridge integration with realistic memory workloads

Usage:
    python -m sim.interconnect.gem5_workload_test
    python -m sim.interconnect.gem5_workload_test --pattern sequential
    python -m sim.interconnect.gem5_workload_test --pattern random --num-requests 1000
"""

import argparse
import time
import sys
from typing import List, Dict, Any

from sim.interconnect.gem5_bridge import (
    Gem5Bridge,
    BridgeConfig,
    create_bridge,
    TrafficGeneratorInterface,
)


def run_sequential_test(bridge: Gem5Bridge, num_requests: int) -> Dict[str, Any]:
    """运行顺序访问测试"""
    print(f"\n=== Sequential Access Test ({num_requests} requests) ===")

    tg = bridge.create_traffic_generator("seq_tg", "sequential")
    tg.set_base_address(0x1000_0000)
    tg.set_access_size(64)

    start_time = time.time()

    # 发送请求
    for i in range(num_requests):
        req_id = tg.generate_request()
        if req_id is not None:
            bridge.sync(cycle=1)

    # 收集响应
    responses = 0
    for _ in range(num_requests):
        resp = bridge.recv_response(timeout_cycles=1000)
        if resp:
            responses += 1

    elapsed = time.time() - start_time

    stats = tg.get_stats()
    bridge_stats = bridge.get_stats()

    print(f"  Requests sent: {stats['requests_sent']}")
    print(f"  Responses received: {stats['responses_received']}")
    print(f"  Avg latency: {stats['average_latency']:.2f} cycles")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Throughput: {num_requests / elapsed:.0f} req/s")

    return {
        'pattern': 'sequential',
        'requests': stats['requests_sent'],
        'responses': stats['responses_received'],
        'avg_latency': stats['average_latency'],
        'elapsed': elapsed,
        'throughput': num_requests / elapsed,
    }


def run_random_test(bridge: Gem5Bridge, num_requests: int) -> Dict[str, Any]:
    """运行随机访问测试"""
    print(f"\n=== Random Access Test ({num_requests} requests) ===")

    tg = bridge.create_traffic_generator("rand_tg", "random")
    tg.set_base_address(0x1000_0000)
    tg.set_access_size(64)

    start_time = time.time()

    # 发送请求
    for i in range(num_requests):
        req_id = tg.generate_request()
        if req_id is not None:
            bridge.sync(cycle=1)

    # 收集响应
    responses = 0
    for _ in range(num_requests):
        resp = bridge.recv_response(timeout_cycles=1000)
        if resp:
            responses += 1

    elapsed = time.time() - start_time

    stats = tg.get_stats()
    bridge_stats = bridge.get_stats()

    print(f"  Requests sent: {stats['requests_sent']}")
    print(f"  Responses received: {stats['responses_received']}")
    print(f"  Avg latency: {stats['average_latency']:.2f} cycles")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Throughput: {num_requests / elapsed:.0f} req/s")

    return {
        'pattern': 'random',
        'requests': stats['requests_sent'],
        'responses': stats['responses_received'],
        'avg_latency': stats['average_latency'],
        'elapsed': elapsed,
        'throughput': num_requests / elapsed,
    }


def run_hotspot_test(bridge: Gem5Bridge, num_requests: int) -> Dict[str, Any]:
    """运行热点访问测试"""
    print(f"\n=== Hotspot Access Test ({num_requests} requests) ===")

    tg = bridge.create_traffic_generator("hotspot_tg", "hotspot")
    tg.set_base_address(0x1000_0000)
    tg.set_access_size(64)
    tg.hotspot_ratio = 0.8  # 80% 热点

    start_time = time.time()

    # 发送请求
    for i in range(num_requests):
        req_id = tg.generate_request()
        if req_id is not None:
            bridge.sync(cycle=1)

    # 收集响应
    responses = 0
    for _ in range(num_requests):
        resp = bridge.recv_response(timeout_cycles=1000)
        if resp:
            responses += 1

    elapsed = time.time() - start_time

    stats = tg.get_stats()
    bridge_stats = bridge.get_stats()

    print(f"  Requests sent: {stats['requests_sent']}")
    print(f"  Responses received: {stats['responses_received']}")
    print(f"  Avg latency: {stats['average_latency']:.2f} cycles")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Throughput: {num_requests / elapsed:.0f} req/s")

    return {
        'pattern': 'hotspot',
        'requests': stats['requests_sent'],
        'responses': stats['responses_received'],
        'avg_latency': stats['average_latency'],
        'elapsed': elapsed,
        'throughput': num_requests / elapsed,
    }


def run_stride_test(bridge: Gem5Bridge, num_requests: int) -> Dict[str, Any]:
    """运行 stride 访问测试"""
    print(f"\n=== Stride Access Test ({num_requests} requests) ===")

    tg = bridge.create_traffic_generator("stride_tg", "stride")
    tg.set_base_address(0x1000_0000)
    tg.set_access_size(64)
    tg.stride = 256  # 4KB stride

    start_time = time.time()

    # 发送请求
    for i in range(num_requests):
        req_id = tg.generate_request()
        if req_id is not None:
            bridge.sync(cycle=1)

    # 收集响应
    responses = 0
    for _ in range(num_requests):
        resp = bridge.recv_response(timeout_cycles=1000)
        if resp:
            responses += 1

    elapsed = time.time() - start_time

    stats = tg.get_stats()
    bridge_stats = bridge.get_stats()

    print(f"  Requests sent: {stats['requests_sent']}")
    print(f"  Responses received: {stats['responses_received']}")
    print(f"  Avg latency: {stats['average_latency']:.2f} cycles")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Throughput: {num_requests / elapsed:.0f} req/s")

    return {
        'pattern': 'stride',
        'requests': stats['requests_sent'],
        'responses': stats['responses_received'],
        'avg_latency': stats['average_latency'],
        'elapsed': elapsed,
        'throughput': num_requests / elapsed,
    }


def run_mixed_test(bridge: Gem5Bridge, num_requests: int) -> Dict[str, Any]:
    """运行混合读写测试"""
    print(f"\n=== Mixed Read/Write Test ({num_requests} requests) ===")

    start_time = time.time()
    reads = 0
    writes = 0

    for i in range(num_requests):
        if i % 4 == 0:
            # 写请求
            data = [i & 0xFFFFFFFF] * 8
            req_id = bridge.send_request(
                addr=0x1000_0000 + (i * 64),
                size=64,
                is_write=True,
                data=data,
            )
            if req_id is not None:
                writes += 1
        else:
            # 读请求
            req_id = bridge.send_request(
                addr=0x1000_0000 + (i * 64),
                size=64,
                is_write=False,
            )
            if req_id is not None:
                reads += 1

        bridge.sync(cycle=1)

    # 收集响应
    responses = 0
    for _ in range(num_requests):
        resp = bridge.recv_response(timeout_cycles=1000)
        if resp:
            responses += 1

    elapsed = time.time() - start_time

    stats = bridge.get_stats()

    print(f"  Reads: {reads}")
    print(f"  Writes: {writes}")
    print(f"  Responses: {responses}")
    print(f"  Avg latency: {stats.get('avg_latency', 0):.2f} cycles")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Throughput: {num_requests / elapsed:.0f} req/s")

    return {
        'pattern': 'mixed',
        'reads': reads,
        'writes': writes,
        'responses': responses,
        'elapsed': elapsed,
        'throughput': num_requests / elapsed,
    }


def run_burst_test(bridge: Gem5Bridge, num_bursts: int) -> Dict[str, Any]:
    """运行突发传输测试"""
    print(f"\n=== Burst Transfer Test ({num_bursts} bursts) ===")

    start_time = time.time()
    beats_per_burst = 4
    beat_size = 64

    responses = 0
    for i in range(num_bursts):
        # 突发读
        resp_list = bridge.burst_read(
            addr=0x1000_0000 + (i * beat_size * beats_per_burst),
            num_beats=beats_per_burst,
            beat_size=beat_size,
        )
        responses += len(resp_list)

        # 同步
        bridge.sync(cycle=50)

    elapsed = time.time() - start_time
    total_bytes = num_bursts * beats_per_burst * beat_size

    print(f"  Bursts: {num_bursts}")
    print(f"  Beats per burst: {beats_per_burst}")
    print(f"  Responses: {responses}")
    print(f"  Total bytes: {total_bytes / 1024:.1f} KB")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Bandwidth: {total_bytes / elapsed / 1e9:.2f} GB/s")

    return {
        'pattern': 'burst',
        'bursts': num_bursts,
        'beats': beats_per_burst,
        'responses': responses,
        'total_bytes': total_bytes,
        'elapsed': elapsed,
        'bandwidth': total_bytes / elapsed / 1e9,
    }


def main():
    parser = argparse.ArgumentParser(description='gem5 Workload Test for HBM4')
    parser.add_argument('--pattern', '-p', default='all',
                       choices=['all', 'sequential', 'random', 'hotspot', 'stride', 'mixed', 'burst'],
                       help='Test pattern to run')
    parser.add_argument('--num-requests', '-n', type=int, default=100,
                       help='Number of requests per pattern')
    parser.add_argument('--cache-line', type=int, default=64, choices=[64, 128],
                       help='Cache line size')
    parser.add_argument('--latency', type=int, default=10,
                       help='Default latency cycles')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    print("=" * 60)
    print("HBM4 gem5 Workload Test")
    print("=" * 60)

    # 创建桥接
    config = BridgeConfig(
        default_latency=args.latency,
        cache_line_size=args.cache_line,
        enable_cache_line_handling=True,
    )
    bridge = Gem5Bridge(config=config)
    bridge.connect_to_gem5()

    print(f"Configuration:")
    print(f"  Cache line: {args.cache_line} bytes")
    print(f"  Latency: {args.latency} cycles")
    print(f"  Requests: {args.num_requests}")

    results = []

    # 运行测试
    if args.pattern == 'all':
        results.append(run_sequential_test(bridge, args.num_requests))
        bridge.reset_stats()

        results.append(run_random_test(bridge, args.num_requests))
        bridge.reset_stats()

        results.append(run_hotspot_test(bridge, args.num_requests))
        bridge.reset_stats()

        results.append(run_stride_test(bridge, args.num_requests))
        bridge.reset_stats()

        results.append(run_mixed_test(bridge, args.num_requests))
        bridge.reset_stats()

        results.append(run_burst_test(bridge, args.num_requests // 10))
    else:
        if args.pattern == 'sequential':
            results.append(run_sequential_test(bridge, args.num_requests))
        elif args.pattern == 'random':
            results.append(run_random_test(bridge, args.num_requests))
        elif args.pattern == 'hotspot':
            results.append(run_hotspot_test(bridge, args.num_requests))
        elif args.pattern == 'stride':
            results.append(run_stride_test(bridge, args.num_requests))
        elif args.pattern == 'mixed':
            results.append(run_mixed_test(bridge, args.num_requests))
        elif args.pattern == 'burst':
            results.append(run_burst_test(bridge, args.num_requests // 10))

    # 清理
    bridge.disconnect()

    # 打印汇总
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for r in results:
        if 'throughput' in r:
            print(f"  {r['pattern']:12s}: {r['throughput']:8.0f} req/s, "
                  f"latency={r.get('avg_latency', 0):6.2f} cycles")
        elif 'bandwidth' in r:
            print(f"  {r['pattern']:12s}: {r['bandwidth']:8.2f} GB/s")

    print("\nTest completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
