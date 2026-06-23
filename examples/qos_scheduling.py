"""
Example: HBM4 QoS Scheduling

This example demonstrates QoS scheduling features:
- 16-level priority scheduling
- Anti-starvation guarantees
- Bandwidth guarantees and caps
- FR-FCFS selection within same priority

HBM4 QoS Priority Levels:
- CRITICAL (15): Real-time/critical traffic
- HIGH (12): High priority
- NORMAL (8): Normal traffic
- LOW (4): Background/batch
- IDLE (0): Idle/probe

Run: python examples/qos_scheduling.py
"""

from model.controller.HBM4_qos_scheduler import HBM4QoSScheduler, QoSLevel
from model.dram.HBM4_spec import HBM4Spec
import time


def main():
    print("=" * 60)
    print("HBM4 QoS Scheduling Example")
    print("=" * 60)

    # Create scheduler
    print("\n1. Creating HBM4QoSScheduler...")
    scheduler = HBM4QoSScheduler()
    print(f"   - Priority levels: {scheduler.priority_levels}")
    print(f"   - QoS levels defined:")
    print(f"     CRITICAL: {scheduler.QOS_CRITICAL}")
    print(f"     HIGH: {scheduler.QOS_HIGH}")
    print(f"     NORMAL: {scheduler.QOS_NORMAL}")
    print(f"     LOW: {scheduler.QOS_LOW}")
    print(f"     IDLE: {scheduler.QOS_IDLE}")

    # Show bandwidth guarantees and caps
    print("\n2. Bandwidth Configuration:")
    print("   QoS Level | Guarantee (GB/s) | Cap (GB/s)")
    print("   " + "-" * 40)
    for qos in [scheduler.QOS_CRITICAL, scheduler.QOS_HIGH,
                scheduler.QOS_NORMAL, scheduler.QOS_LOW]:
        guarantee = scheduler.bw_guarantee.get(qos, 0)
        cap = scheduler.bw_cap.get(qos, 0)
        print(f"   {qos:10d} | {guarantee:14.1f} | {cap:10.1f}")

    # Submit requests with different priorities
    print("\n3. Submitting Requests with Different Priorities...")
    request_id = 1
    test_cases = [
        (QoSLevel.LOW, "Background traffic"),
        (QoSLevel.NORMAL, "Normal access"),
        (QoSLevel.HIGH, "High priority access"),
        (QoSLevel.CRITICAL, "Real-time critical"),
    ]

    for qos, description in test_cases:
        scheduler.submit_request(
            request_id=request_id,
            addr=0x1000 + request_id * 0x100,
            qos=qos,
            is_read=True,
            channel=request_id % 32,
            row_hit=(request_id % 3 == 0),  # Every 3rd request is row hit
        )
        print(f"   - Request {request_id}: {description} (QoS={qos})")
        request_id += 1

    # Check queue sizes
    print("\n4. Queue Status:")
    print(f"   - Total queued: {scheduler.get_total_queue_size()}")
    for qos in [QoSLevel.LOW, QoSLevel.NORMAL, QoSLevel.HIGH, QoSLevel.CRITICAL]:
        size = scheduler.get_queue_size(qos)
        if size > 0:
            print(f"   - QoS {qos:2d}: {size} request(s)")

    # Schedule requests (should select highest priority first)
    print("\n5. Scheduling Requests:")
    for i in range(6):
        scheduled = scheduler.schedule()
        if scheduled:
            print(f"   - Scheduled {i+1}: id={scheduled.request_id}, "
                  f"QoS={scheduled.qos}, row_hit={scheduled.row_hit}")
        else:
            print(f"   - No more requests to schedule")
            break

    # Demonstrate select_next with HBMRequest-like objects
    print("\n6. Using select_next with request list:")

    class MockRequest:
        def __init__(self, req_id, qos, arrival, row_hit=False):
            self.request_id = req_id
            self.qos = qos
            self.arrival_time = arrival
            self.row_hit = row_hit

    # Create scheduler for fresh selection
    scheduler2 = HBM4QoSScheduler()

    # Submit mixed requests
    base_time = time.time()
    mock_requests = [
        MockRequest(1, QoSLevel.LOW, base_time + 1, False),
        MockRequest(2, QoSLevel.HIGH, base_time + 2, False),
        MockRequest(3, QoSLevel.CRITICAL, base_time + 3, False),
        MockRequest(4, QoSLevel.NORMAL, base_time + 4, True),  # Row hit
        MockRequest(5, QoSLevel.HIGH, base_time + 5, True),  # Row hit
    ]

    for req in mock_requests:
        scheduler2.submit_request(
            request_id=req.request_id,
            qos=req.qos,
            is_read=True,
            row_hit=req.row_hit,
        )

    print("   Initial queue state:")
    for qos in [QoSLevel.LOW, QoSLevel.NORMAL, QoSLevel.HIGH, QoSLevel.CRITICAL]:
        size = scheduler2.get_queue_size(qos)
        if size > 0:
            print(f"   - QoS {qos:2d}: {size} request(s)")

    # FR-FCFS: CRITICAL first, then HIGH with row hit
    print("\n   FR-FCFS Selection (row hits first within QoS):")
    selected = scheduler2.select_next(mock_requests)
    if selected:
        print(f"   - First selected: id={selected.request_id}, "
              f"QoS={selected.qos}, row_hit={selected.row_hit}")

    # Select remaining by priority
    remaining = [r for r in mock_requests if r.request_id != selected.request_id]
    selected2 = scheduler2.select_next(remaining)
    if selected2:
        print(f"   - Second selected: id={selected2.request_id}, "
              f"QoS={selected2.qos}, row_hit={selected2.row_hit}")

    # Get statistics
    print("\n7. Scheduler Statistics:")
    stats = scheduler2.get_stats()
    print(f"   - Total scheduled: {stats['total_scheduled']}")
    print(f"   - Requests by QoS: {stats['by_qos']}")

    # Modify bandwidth settings
    print("\n8. Modifying Bandwidth Settings:")
    print(f"   Before: CRITICAL guarantee={scheduler.bw_guarantee[15]:.1f} GB/s")
    scheduler.set_bandwidth_guarantee(15, 400.0)
    print(f"   After: CRITICAL guarantee={scheduler.bw_guarantee[15]:.1f} GB/s")

    print("\n" + "=" * 60)
    print("QoS scheduling example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()