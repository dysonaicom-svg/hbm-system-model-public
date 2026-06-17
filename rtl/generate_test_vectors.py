#!/usr/bin/env python3
"""
HBM Functional Testbench Test Vector Generator

Generates test vectors for the HBM controller functional testbench.
Supports various access patterns: sequential, random, bank conflict, etc.
"""

import argparse
import random
import sys
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class AccessPattern(Enum):
    """Test access patterns"""
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    STRIDE = "stride"
    BANK_CONFLICT = "bank_conflict"
    ROW_HIT = "row_hit"
    ROW_MISS = "row_miss"
    MIXED = "mixed"


class RequestType(Enum):
    """Request type"""
    READ = 1
    WRITE = 0


@dataclass
class HBMAddress:
    """HBM address structure (36-bit)"""
    stack: int = 0       # 2 bits
    channel: int = 0     # 5 bits (32 channels)
    pseudo_ch: int = 0   # 1 bit
    bank_group: int = 0  # 3 bits (8 groups)
    bank: int = 0         # 4 bits (16 banks)
    row: int = 0          # 16 bits
    col: int = 0          # 6 bits

    def to_uint(self) -> int:
        """Convert to 36-bit unsigned integer"""
        addr = 0
        addr |= (self.stack & 0x3) << 34
        addr |= (self.channel & 0x1F) << 29
        addr |= (self.pseudo_ch & 0x1) << 28
        addr |= (self.bank_group & 0x7) << 25
        addr |= (self.bank & 0xF) << 21
        addr |= (self.row & 0xFFFF) << 6
        addr |= (self.col & 0x3F)
        return addr

    @classmethod
    def from_uint(cls, addr: int) -> 'HBMAddress':
        """Create from 36-bit unsigned integer"""
        h = cls()
        h.stack = (addr >> 34) & 0x3
        h.channel = (addr >> 29) & 0x1F
        h.pseudo_ch = (addr >> 28) & 0x1
        h.bank_group = (addr >> 25) & 0x7
        h.bank = (addr >> 21) & 0xF
        h.row = (addr >> 6) & 0xFFFF
        h.col = addr & 0x3F
        return h

    def __str__(self) -> str:
        return (f"HBMAddress(ch={self.channel:2d}, bg={self.bank_group}, "
                f"bk={self.bank:2d}, row=0x{self.row:04X}, col={self.col:2d})")


@dataclass
class TestRequest:
    """Test request structure"""
    request_id: int
    request_type: RequestType
    address: HBMAddress
    priority: int = 3
    length: int = 64

    def to_sv_format(self) -> str:
        """Convert to SystemVerilog task call format"""
        req_type = "READ" if self.request_type == RequestType.READ else "WRITE"
        addr_hex = f"36'h{self.address.to_uint():09X}"
        return (f'        submit_request({req_type == "READ"}, {addr_hex}, '
                f'3\'d{self.priority}, {self.length});  // req #{self.request_id}')

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export"""
        return {
            'id': self.request_id,
            'type': 'READ' if self.request_type == RequestType.READ else 'WRITE',
            'address': self.address.to_uint(),
            'priority': self.priority,
            'length': self.length,
            'addr_struct': {
                'stack': self.address.stack,
                'channel': self.address.channel,
                'pseudo_ch': self.address.pseudo_ch,
                'bank_group': self.address.bank_group,
                'bank': self.address.bank,
                'row': self.address.row,
                'col': self.address.col,
            }
        }


class TestVectorGenerator:
    """Generates test vectors for HBM controller"""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.request_id = 0

    def reset_id(self):
        """Reset request ID counter"""
        self.request_id = 0

    def next_id(self) -> int:
        """Get next request ID"""
        curr = self.request_id
        self.request_id += 1
        return curr

    def create_address(self, channel: int = 0, bg: int = 0, bank: int = 0,
                       row: int = 0, col: int = 0, stack: int = 0,
                       pch: int = 0) -> HBMAddress:
        """Create HBM address with specified fields"""
        addr = HBMAddress()
        addr.stack = stack
        addr.channel = channel
        addr.pseudo_ch = pch
        addr.bank_group = bg
        addr.bank = bank
        addr.row = row
        addr.col = col
        return addr

    def generate_sequential(self, num_requests: int,
                           channel: int = 0,
                           start_row: int = 0,
                           start_col: int = 0,
                           read_ratio: float = 0.5) -> List[TestRequest]:
        """Generate sequential access pattern"""
        requests = []
        row = start_row
        col = start_col

        for i in range(num_requests):
            req_type = (RequestType.READ if self.rng.random() < read_ratio
                        else RequestType.WRITE)
            addr = self.create_address(channel=channel, row=row, col=col)
            priority = self.rng.randint(0, 7)

            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=req_type,
                address=addr,
                priority=priority
            ))

            # Increment column, wrap to next row
            col += 1
            if col >= 64:
                col = 0
                row += 1

        return requests

    def generate_random(self, num_requests: int,
                       read_ratio: float = 0.5) -> List[TestRequest]:
        """Generate random access pattern"""
        requests = []

        for _ in range(num_requests):
            req_type = (RequestType.READ if self.rng.random() < read_ratio
                        else RequestType.WRITE)

            # Generate random address fields
            channel = self.rng.randint(0, 31)
            bg = self.rng.randint(0, 7)
            bank = self.rng.randint(0, 15)
            row = self.rng.randint(0, 65535)
            col = self.rng.randint(0, 63)
            priority = self.rng.randint(0, 7)

            addr = self.create_address(
                channel=channel, bg=bg, bank=bank,
                row=row, col=col
            )

            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=req_type,
                address=addr,
                priority=priority
            ))

        return requests

    def generate_stride(self, num_requests: int,
                        stride: int = 4096,
                        channel: int = 0,
                        read_ratio: float = 0.5) -> List[TestRequest]:
        """Generate stride access pattern"""
        requests = []
        base_addr = 0

        for i in range(num_requests):
            req_type = (RequestType.READ if self.rng.random() < read_ratio
                        else RequestType.WRITE)

            # Stride through address space
            addr_int = (base_addr + i * stride) % (1 << 36)
            addr = HBMAddress.from_uint(addr_int)

            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=req_type,
                address=addr,
                priority=3
            ))

        return requests

    def generate_bank_conflict(self, num_requests: int,
                               pattern: str = "same_bank_diff_row"
                               ) -> List[TestRequest]:
        """Generate bank conflict test pattern

        Patterns:
        - same_bank_same_row: Row hits (fast)
        - same_bank_diff_row: Row conflicts (slow)
        - diff_bank: Parallelizable
        - diff_channel: Fully parallel
        """
        requests = []

        if pattern == "same_bank_same_row":
            # All requests to same bank/row = row hits
            addr = self.create_address(channel=0, bg=0, bank=0, row=0)
            for i in range(num_requests):
                req_type = (RequestType.READ if i % 2 == 0 else RequestType.WRITE)
                requests.append(TestRequest(
                    request_id=self.next_id(),
                    request_type=req_type,
                    address=addr,
                    priority=7
                ))

        elif pattern == "same_bank_diff_row":
            # Same bank, different rows = row misses
            addr = self.create_address(channel=0, bg=0, bank=0, row=0)
            for i in range(num_requests):
                req_type = (RequestType.READ if i % 2 == 0 else RequestType.WRITE)
                addr.row = i % 256  # Different row each time
                requests.append(TestRequest(
                    request_id=self.next_id(),
                    request_type=req_type,
                    address=addr.copy() if hasattr(addr, 'copy') else self.create_address(
                        channel=0, bg=0, bank=0, row=i % 256
                    ),
                    priority=7
                ))

        elif pattern == "diff_bank":
            # Different banks = can be pipelined
            for i in range(num_requests):
                req_type = (RequestType.READ if i % 2 == 0 else RequestType.WRITE)
                addr = self.create_address(
                    channel=0, bg=0, bank=i % 16, row=0
                )
                requests.append(TestRequest(
                    request_id=self.next_id(),
                    request_type=req_type,
                    address=addr,
                    priority=5
                ))

        elif pattern == "diff_channel":
            # Different channels = fully parallel
            for i in range(num_requests):
                req_type = (RequestType.READ if i % 2 == 0 else RequestType.WRITE)
                addr = self.create_address(
                    channel=i % 32, row=0
                )
                requests.append(TestRequest(
                    request_id=self.next_id(),
                    request_type=req_type,
                    address=addr,
                    priority=5
                ))

        return requests

    def generate_priority_test(self, num_requests: int = 24
                               ) -> List[TestRequest]:
        """Generate QoS priority test pattern

        Mix of low/medium/high priority requests to verify
        scheduler correctly prioritizes high-priority traffic.
        """
        requests = []

        # Low priority first
        for i in range(num_requests // 4):
            addr = self.create_address(channel=0, row=i)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=0
            ))

        # Medium priority
        for i in range(num_requests // 4):
            addr = self.create_address(channel=1, row=i + 64)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=3
            ))

        # High priority
        for i in range(num_requests // 2):
            addr = self.create_address(channel=2, row=i + 128)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=7
            ))

        return requests

    def generate_boundary_test(self) -> List[TestRequest]:
        """Generate boundary condition test

        Tests edge cases for all address fields.
        """
        requests = []

        # Channel boundaries
        for ch in [0, 31]:
            addr = self.create_address(channel=ch)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=5
            ))

        # Bank group boundaries
        for bg in [0, 7]:
            addr = self.create_address(bank_group=bg)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=5
            ))

        # Bank boundaries
        for bk in [0, 15]:
            addr = self.create_address(bank=bk)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=5
            ))

        # Row boundaries
        addr = self.create_address(row=0)
        requests.append(TestRequest(
            request_id=self.next_id(),
            request_type=RequestType.READ,
            address=addr,
            priority=5
        ))
        addr = self.create_address(row=65535)
        requests.append(TestRequest(
            request_id=self.next_id(),
            request_type=RequestType.READ,
            address=addr,
            priority=5
        ))

        # Column boundaries
        for col in [0, 63]:
            addr = self.create_address(col=col)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=5
            ))

        # Stack boundaries
        for stack in [0, 3]:
            addr = self.create_address(stack=stack)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=5
            ))

        # Pseudo-channel boundaries
        for pch in [0, 1]:
            addr = self.create_address(pseudo_ch=pch)
            requests.append(TestRequest(
                request_id=self.next_id(),
                request_type=RequestType.READ,
                address=addr,
                priority=5
            ))

        return requests

    def generate_mixed(self, num_requests: int = 100) -> List[TestRequest]:
        """Generate mixed access pattern with all patterns"""
        requests = []

        # 20% sequential
        requests.extend(self.generate_sequential(
            num_requests=int(num_requests * 0.2),
            read_ratio=0.6
        ))

        # 30% random
        requests.extend(self.generate_random(
            num_requests=int(num_requests * 0.3),
            read_ratio=0.5
        ))

        # 20% bank conflict (row hits)
        requests.extend(self.generate_bank_conflict(
            num_requests=int(num_requests * 0.2),
            pattern="same_bank_same_row"
        ))

        # 30% priority test
        requests.extend(self.generate_priority_test(
            num_requests=int(num_requests * 0.3)
        ))

        return requests


def generate_sv_testbench(requests: List[TestRequest],
                          test_name: str = "Generated Test"
                          ) -> str:
    """Generate SystemVerilog test code from requests"""
    lines = []
    lines.append(f"    // {test_name}")
    lines.append(f"    // Generated {len(requests)} requests")
    lines.append(f"    init_test(TEST_BASIC_READ_WRITE, \"{test_name}\", {len(requests)});")
    lines.append("")

    for req in requests:
        lines.append(req.to_sv_format())

    lines.append("")
    lines.append("    wait_complete(5000);")
    lines.append("    verify_test();")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="HBM Functional Testbench Test Vector Generator"
    )
    parser.add_argument("-o", "--output", default="-",
                        help="Output file (default: stdout)")
    parser.add_argument("-n", "--num-requests", type=int, default=100,
                        help="Number of requests to generate")
    parser.add_argument("-p", "--pattern", type=AccessPattern,
                        default=AccessPattern.SEQUENTIAL,
                        choices=list(AccessPattern),
                        help="Access pattern")
    parser.add_argument("-s", "--seed", type=int, default=42,
                        help="Random seed")
    parser.add_argument("--format", choices=["sv", "json", "csv"],
                        default="sv",
                        help="Output format")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # Create generator
    gen = TestVectorGenerator(seed=args.seed)

    # Generate requests based on pattern
    if args.pattern == AccessPattern.SEQUENTIAL:
        requests = gen.generate_sequential(args.num_requests)
    elif args.pattern == AccessPattern.RANDOM:
        requests = gen.generate_random(args.num_requests)
    elif args.pattern == AccessPattern.STRIDE:
        requests = gen.generate_stride(args.num_requests)
    elif args.pattern == AccessPattern.BANK_CONFLICT:
        requests = gen.generate_bank_conflict(args.num_requests)
    elif args.pattern == AccessPattern.ROW_HIT:
        requests = gen.generate_bank_conflict(
            args.num_requests, "same_bank_same_row"
        )
    elif args.pattern == AccessPattern.ROW_MISS:
        requests = gen.generate_bank_conflict(
            args.num_requests, "same_bank_diff_row"
        )
    elif args.pattern == AccessPattern.MIXED:
        requests = gen.generate_mixed(args.num_requests)
    else:
        requests = gen.generate_sequential(args.num_requests)

    # Generate output
    output = []
    if args.format == "sv":
        output.append(generate_sv_testbench(requests, f"{args.pattern.value} Test"))
    elif args.format == "json":
        import json
        output.append(json.dumps([r.to_dict() for r in requests], indent=2))
    elif args.format == "csv":
        output.append("id,type,address_hex,priority,length,channel,bank_group,bank,row,col")
        for req in requests:
            addr = req.address
            output.append(
                f"{req.request_id},"
                f"{'READ' if req.request_type == RequestType.READ else 'WRITE'},"
                f"0x{addr.to_uint():09X},"
                f"{req.priority},"
                f"{req.length},"
                f"{addr.channel},"
                f"{addr.bank_group},"
                f"{addr.bank},"
                f"0x{addr.row:04X},"
                f"{addr.col}"
            )

    # Write output
    if args.output == "-":
        print("\n".join(output))
    else:
        with open(args.output, "w") as f:
            f.write("\n".join(output))
        if args.verbose:
            print(f"Wrote {len(requests)} requests to {args.output}")

    if args.verbose:
        print(f"Generated {len(requests)} requests with pattern: {args.pattern.value}")
        print(f"Seed: {args.seed}")


if __name__ == "__main__":
    main()
