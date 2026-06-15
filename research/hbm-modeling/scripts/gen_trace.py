#!/usr/bin/env python3
"""Generate memory traces for Ramulator2 LoadStoreTrace frontend."""
import argparse
import random


def write_trace(path, pattern, count, base, span, stride, write_ratio):
    """Write trace in Ramulator2 LoadStoreTrace format (LD/ST + addr)."""
    rng = random.Random(1)
    with open(path, "w", encoding="ascii") as f:
        for i in range(count):
            if pattern == "seq":
                addr = base + i * 64
            elif pattern == "stride":
                addr = base + i * stride
            elif pattern == "random":
                addr = base + rng.randrange(0, span // 64) * 64
            else:
                raise ValueError(f"unsupported pattern: {pattern}")

            op = "ST" if rng.random() < write_ratio else "LD"
            f.write(f"{op} {addr:#x}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--pattern", choices=["seq", "stride", "random"], required=True)
    parser.add_argument("--count", type=int, default=100000)
    parser.add_argument("--base", type=lambda x: int(x, 0), default=0)
    parser.add_argument("--span", type=lambda x: int(x, 0), default=0x40000000)
    parser.add_argument("--stride", type=int, default=4096)
    parser.add_argument("--write-ratio", type=float, default=0.0)
    args = parser.parse_args()
    write_trace(args.out, args.pattern, args.count, args.base, args.span, args.stride, args.write_ratio)


if __name__ == "__main__":
    main()