"""
HBM4 QoS Priority Scheduling Example

Demonstrates QoS-based request scheduling:
- 16 priority levels (0-15)
- Critical, high, normal, low, idle levels
- Anti-starvation guarantees
- FR-FCFS within same priority
- Bandwidth guarantees and caps

Reference: Synopsys DesignWare HBM4/4E Controller IP

Run: python examples/qos_priority.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel
from model.controller.hbm4_controller import HBM4Controller


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def example_qos_levels():
    """Show available QoS levels."""
    print_section("Example 1: QoS Priority Levels")

    print("\nAvailable QoS Levels:")
    print("  " + "-" * 50)
    print(f"  {'Level':<10} {'Name':<12} {'Value':<8} Description")
    print("  " + "-" * 50)

    levels = [
        (QoSLevel.CRITICAL, "Real-time/critical traffic"),
        (QoSLevel.HIGH, "High priority traffic"),
        (QoSLevel.NORMAL, "Normal/default traffic"),
        (QoSLevel.LOW, "Background/batch processing"),
        (QoSLevel.IDLE, "Idle/probe traffic"),
    ]

    for level, desc in levels:
        print(f"  {level.value:<10} {level.name:<12} {level:<8} {desc}")

    # Show all 16 levels
    print("\nAll 16 Priority Levels (0-15):")
    print("  Higher value = higher priority")
    print("  Level 15: CRITICAL (real-time)")
    print("  Level 12: HIGH")
    print("  Level 8:  NORMAL (default)")
    print("  Level 4:  LOW")
    print("  Level 0:  IDLE")


def example_scheduler_basics():
    """Basic QoS scheduler usage."""
    print_section("Example 2: QoS Scheduler Basics")

    scheduler = HBM4QoSScheduler()

    print("\nSubmitting requests with different priorities...")
    print("  " + "-" * 50)

    # Submit requests with different priorities
    test_requests = [
        (1, 0x1000, QoSLevel.LOW, True),
        (2, 0x2000, QoSLevel.NORMAL, True),
        (3, 0x3000, QoSLevel.HIGH, True),
        (4, 0x4000, QoSLevel.CRITICAL, True),
        (5, 0x5000, QoSLevel.LOW, False),
    ]

    for req_id, addr, qos, is_read in test_requests:
        scheduler.submit_request(
            request_id=req_id,
            addr=addr,
            qos=qos,
            is_read=is_read,
        )
        print(f"  Request {req_id}: QoS={qos.value} ({qos.name})")

    # Check queue sizes
    print("\nQueue Status:")
    for level in [15, 12, 8, 4, 0]:
        size = scheduler.get_queue_size(level)
        print(f"  QoS {level:2d}: {size} request(s)")

    print(f"\n  Total queued: {scheduler.get_total_queue_size()}")

    # Schedule requests (should be in priority order)
    print("\nScheduling Order (highest priority first):")
    print("  " + "-" * 50)

    for i in range(5):
        req = scheduler.schedule()
        if req:
            print(f"  {i+1}. Request {req.request_id}, QoS={req.qos} ({QoSLevel(req.qos).name})")


def example_anti_starvation():
    """Demonstrate anti-starvation mechanism."""
    print_section("Example 3: Anti-Starvation Mechanism")

    scheduler = HBM4QoSScheduler()

    print("\nAnti-Starvation Configuration:")
    print("  " + "-" * 50)

    # Show default bandwidth guarantees
    print("\n  Bandwidth Guarantees (GB/s):")
    for qos in [15, 12, 8, 4, 0]:
        guarantee = scheduler.bw_guarantee.get(qos, 0)
        print(f"    QoS {qos:2d}: {guarantee:.0f} GB/s")

    # Show bandwidth caps
    print("\n  Bandwidth Caps (GB/s):")
    for qos in [15, 12, 8, 4, 0]:
        cap = scheduler.bw_cap.get(qos, float('inf'))
        cap_str = f"{cap:.0f}" if cap < float('inf') else "unlimited"
        print(f"    QoS {qos:2d}: {cap_str} GB/s")

    # Simulate high-priority traffic consuming bandwidth
    print("\nSimulating High-Priority Traffic:")
    for i in range(50):
        scheduler.submit_request(
            request_id=i,
            addr=0x1000 + i,
            qos=QoSLevel.CRITICAL,
            is_read=True,
            length=64
        )

    # Schedule all critical requests
    print("  Submitted 50 CRITICAL requests")

    while scheduler.get_total_queue_size() > 0:
        scheduler.schedule()

    stats = scheduler.get_stats()
    print(f"  Scheduled {stats['total_scheduled']} requests")
    print(f"  By QoS: {stats['by_qos']}")


def example_fr_fcfs():
    """Demonstrate FR-FCFS within same priority."""
    print_section("Example 4: FR-FCFS Within Same Priority")

    scheduler = HBM4QoSScheduler()

    print("\nFirst-Ready FCFS Scheduling:")
    print("  " + "-" * 50)
    print("  Within the same QoS level:")
    print("  1. Row hit requests first")
    print("  2. Oldest request (FCFS)")

    # Submit all at same priority but with different row_hit flags
    import time
    time.sleep(0.01)  # Ensure different arrival times

    # Row miss requests (submitted first)
    for i in range(3):
        scheduler.submit_request(
            request_id=100 + i,
            addr=0x1000 + i * 0x1000,
            qos=QoSLevel.NORMAL,
            is_read=True,
            row_hit=False,
        )

    time.sleep(0.01)

    # Row hit request (submitted later but should be prioritized)
    scheduler.submit_request(
        request_id=200,
        addr=0x5000,
        qos=QoSLevel.NORMAL,
        is_read=True,
        row_hit=True,  # This should be scheduled first
    )

    print("\n  Submitted 4 requests at QoS 8 (NORMAL):")
    print("    Requests 100-102: row_hit=False (submitted first)")
    print("    Request 200:      row_hit=True (submitted later)")

    print("\n  Scheduling Order:")
    scheduled = []
    for i in range(4):
        req = scheduler.schedule()
        if req:
            scheduled.append(req)
            hit_status = "ROW HIT" if req.row_hit else "row miss"
            print(f"    {i+1}. Request {req.request_id} ({hit_status})")

    # Verify row hit was scheduled first
    if scheduled[0].row_hit:
        print("\n  Verified: Row hit request scheduled first!")


def example_controller_integration():
    """Show QoS integration with HBM4Controller."""
    print_section("Example 5: QoS Integration with Controller")

    controller = HBM4Controller(enable_qos=True)

    print("\nController Configuration:")
    print("  " + "-" * 50)
    stats = controller.get_stats()
    print(f"  QoS Enabled: {stats['qos']['enabled']}")
    print(f"  Priority Levels: {stats['qos']['priority_levels']}")

    # Submit requests with different priorities
    print("\nSubmitting requests with different priorities:")
    print("  (Low priority submitted first)")

    priority_map = [
        (QoSLevel.LOW, 5),
        (QoSLevel.NORMAL, 5),
        (QoSLevel.HIGH, 5),
        (QoSLevel.CRITICAL, 5),
    ]

    for qos, count in priority_map:
        for i in range(count):
            addr = ((qos & 0xF) << 44) | ((i & 0xF) << 36) | 0x8
            controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=qos
            )
        print(f"  QoS {qos.value} ({qos.name}): {count} requests")

    # Track completion order
    print("\nRunning simulation...")
    completion_order = []

    cycles = 0
    while len(controller._pending_requests) > 0 and cycles < 500:
        cycles += 1
        resp_list = controller.tick()
        for resp in resp_list:
            # Estimate QoS from request_id pattern
            completion_order.append(resp.request_id)

    print(f"\n  Simulation completed in {cycles} cycles")
    print(f"  Completed {len(completion_order)} requests")

    # Get final stats
    stats = controller.get_stats()
    scheduler_stats = controller.qos_scheduler.get_stats()
    print(f"\n  QoS Statistics:")
    print(f"    Total scheduled: {scheduler_stats['total_scheduled']}")
    print(f"    By QoS level: {scheduler_stats['by_qos']}")


def example_bandwidth_guarantees():
    """Configure bandwidth guarantees."""
    print_section("Example 6: Bandwidth Guarantees Configuration")

    scheduler = HBM4QoSScheduler()

    print("\nDefault Configuration:")
    print("  " + "-" * 50)
    print("  Bandwidth Guarantees:")
    for qos in [15, 12, 8, 4, 0]:
        print(f"    QoS {qos:2d}: {scheduler.bw_guarantee.get(qos, 0):.0f} GB/s")

    # Customize for specific use case
    print("\nCustom Configuration (real-time workload):")
    scheduler.set_bandwidth_guarantee(QoSLevel.CRITICAL, 500.0)  # 500 GB/s for critical
    scheduler.set_bandwidth_cap(QoSLevel.HIGH, 400.0)  # Cap high at 400 GB/s

    print("  Bandwidth Guarantees (customized):")
    for qos in [15, 12, 8, 4, 0]:
        guarantee = scheduler.bw_guarantee.get(qos, 0)
        cap = scheduler.bw_cap.get(qos, float('inf'))
        cap_str = f"{cap:.0f}" if cap < float('inf') else "unlimited"
        print(f"    QoS {qos:2d}: guarantee={guarantee:.0f} GB/s, cap={cap_str} GB/s")


def example_qos_with_controller():
    """Real-world QoS example with controller."""
    print_section("Example 7: Real-World QoS Scenario")

    controller = HBM4Controller(enable_qos=True)

    print("\nScenario: Mixed Workload")
    print("  " + "-" * 50)
    print("  - Real-time video frame processing (QoS 15)")
    print("  - GPU compute results (QoS 12)")
    print("  - Normal application data (QoS 8)")
    print("  - Background prefetch (QoS 4)")

    # Simulate workload
    workloads = [
        (QoSLevel.CRITICAL, 10, "Video frames"),
        (QoSLevel.HIGH, 20, "GPU results"),
        (QoSLevel.NORMAL, 30, "Application data"),
        (QoSLevel.LOW, 40, "Prefetch"),
    ]

    for qos, count, name in workloads:
        for i in range(count):
            addr = ((qos & 0xF) << 48) | ((i & 0xFFF) << 6) | 0x8
            controller.submit_request(
                addr=addr,
                is_read=True,
                qos_level=qos
            )
        print(f"\n  Submitted {count} {name} requests (QoS {qos.value})")

    # Run simulation
    print("\nRunning simulation...")
    cycles = 0
    while len(controller._pending_requests) > 0 and cycles < 1000:
        cycles += 1
        controller.tick()

    # Get stats
    stats = controller.get_stats()
    scheduler_stats = controller.qos_scheduler.get_stats()

    print(f"\n  Completed in {cycles} cycles")
    print(f"  Average latency: {stats['controller']['average_latency_ns']:.1f} ns")
    print(f"\n  Requests by QoS (scheduled):")
    for qos in [15, 12, 8, 4]:
        count = scheduler_stats['by_qos'].get(qos, 0)
        print(f"    QoS {qos:2d}: {count} requests")


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("#  HBM4 QoS Priority Scheduling Examples")
    print("#" * 60)

    example_qos_levels()
    example_scheduler_basics()
    example_anti_starvation()
    example_fr_fcfs()
    example_controller_integration()
    example_bandwidth_guarantees()
    example_qos_with_controller()

    print("\n" + "#" * 60)
    print("#  All Examples Completed Successfully!")
    print("#" * 60)


if __name__ == "__main__":
    main()