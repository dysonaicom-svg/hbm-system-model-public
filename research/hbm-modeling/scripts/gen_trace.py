#!/usr/bin/env python3
"""Generate memory traces for Ramulator2 SimpleO3 frontend.

Format: bubble_count load_address [store_address]
- bubble_count: cycles between this instruction and next
- load_address: decimal address for load operation
- store_address: optional decimal address for store operation
"""
import argparse
import random


def write_trace(path, pattern, count, base, span, stride, write_ratio, max_bubble=10):
    rng = random.Random(42)  # Fixed seed for reproducibility
    with open(path, "w", encoding="ascii") as f:
        for i in range(count):
            # Generate bubble count (0-10 cycles between instructions)
            bubble = rng.randint(0, max_bubble)

            if pattern == "seq":
                addr = base + i * 64
            elif pattern == "stride":
                addr = base + i * stride
            elif pattern == "random":
                addr = base + rng.randrange(0, span // 64) * 64
            else:
                raise ValueError(f"unsupported pattern: {pattern}")

            # Write line: bubble_count load_address
            f.write(f"{bubble} {addr}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output trace file path")
    parser.add_argument("--pattern", choices=["seq", "stride", "random"], required=True)
    parser.add_argument("--count", type=int, default=100000, help="Number of memory operations")
    parser.add_argument("--base", type=lambda x: int(x, 0), default=0, help="Base address")
    parser.add_argument("--span", type=lambda x: int(x, 0), default=0x40000000, help="Address span")
    parser.add_argument("--stride", type=int, default=4096, help="Stride for stride pattern")
    parser.add_argument("--write-ratio", type=float, default=0.0, help="Write ratio (not used in SimpleO3 format)")
    parser.add_argument("--max-bubble", type=int, default=10, help="Maximum bubble count between instructions")
    args = parser.parse_args()
    write_trace(args.out, args.pattern, args.count, args.base, args.span, args.stride, args.write_ratio, args.max_bubble)


if __name__ == "__main__":
    main()