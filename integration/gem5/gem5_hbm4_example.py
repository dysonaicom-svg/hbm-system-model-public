#!/usr/bin/env python3
"""
gem5 HBM4 Example Simulation Script
Demonstrates how to configure and run HBM4 memory simulations with gem5

Usage:
    python gem5_hbm4_example.py --cpu-type=AtomicSimpleCPU --num-cpus=4
    python gem5_hbm4_example.py --cpu-type=TimingSimpleCPU --num-cpus=8
    python gem5_hbm4_example.py --hbm-config=hbm4_32ch --duration=100000
"""

import argparse
import sys
import os

# Check for gem5
try:
    # Add gem5 to path
    addToPath('/opt/gem5')

    from m5.objects import *
    from m5.util import addToPath
    import m5
    GEM5_AVAILABLE = True
except ImportError:
    GEM5_AVAILABLE = False
    print("WARNING: gem5 not available. This script requires gem5 to be installed.")
    print("  Install from: https://github.com/gem5/gem5")
    sys.exit(1)

# Import HBM4 configuration
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hbm4_config import (
    HBM4Timing, HBM4Config, HBM4Presets, get_config_by_name, HBM4AddrMap
)


def create_system(args):
    """Create gem5 system with HBM4 memory

    Args:
        args: Command line arguments

    Returns:
        Root system object
    """
    # Create system
    system = System()

    # Set clock domain
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = '4GHz'
    system.clk_domain.voltage_domain = VoltageDomain()

    # Set memory mode based on CPU type
    if args.cpu_type == 'AtomicSimpleCPU':
        system.mem_mode = 'atomic'
    else:
        system.mem_mode = 'timing'

    # Create CPU
    if args.num_cpus > 1:
        system.cpu = [eval(f'{args.cpu_type}()') for _ in range(args.num_cpus)]
    else:
        system.cpu = eval(f'{args.cpu_type}()')

    # Set CPU clock
    for cpu in system.cpu if isinstance(system.cpu, list) else [system.cpu]:
        cpu.clk_domain = system.clk_domain

    # Create memory controller based on HBM config
    hbm_config = get_config_by_name(args.hbm_config)

    # Create HBM4 memory controller
    mem_ctrl = HBM4MemoryController()
    mem_ctrl.channels = hbm_config['channels_per_stack']
    mem_ctrl.pseudo_channels = hbm_config['pseudo_channels']
    mem_ctrl.timing = HBM4Timing

    # Create memory
    memory = HBM4()
    memory.data_rate = hbm_config['data_rate'] / 1e9  # Convert to GT/s
    memory.width = 64

    # Set memory size
    mem_size = args.mem_size
    system.mem_ranges = [AddrRange(start=0, end=mem_size)]

    # Connect memory controller to system
    mem_ctrl.port = system.membus.cpu_side_ports
    system.mem_ctrls = [mem_ctrl]
    system.memory = memory

    # Set memory channel count
    system.mem_ctrls[0].nbr_channels = hbm_config['channels_per_stack']

    # Create cache hierarchy
    if args.no_cache:
        # Direct connect (no cache)
        for cpu in system.cpu if isinstance(system.cpu, list) else [system.cpu]:
            cpu.port = system.membus.cpu_side_ports
    else:
        # Create L1 caches
        for cpu in system.cpu if isinstance(system.cpu, list) else [system.cpu]:
            # L1 instruction cache
            cpu.icache = L1_ICache(args.cache_size)
            cpu.icache.connectCpuSidePort(cpu.icache_port)
            cpu.icache.connectMemSidePort(system.membus.cpu_side_ports)

            # L1 data cache
            cpu.dcache = L1_DCache(args.cache_size)
            cpu.dcache.connectCpuSidePort(cpu.dcache_port)
            cpu.dcache.connectMemSidePort(system.membus.cpu_side_ports)

            # Connect CPU to caches
            cpu.connectAllPorts(system.membus)

    # Setup process
    system.workload = SEWorkload.init_compatible(binary=args.binary)

    # Create process
    process = Process()
    process.executable = args.binary
    process.cmd = [args.binary] + args.options.split() if args.options else [args.binary]

    # Assign to CPU
    for cpu in system.cpu if isinstance(system.cpu, list) else [system.cpu]:
        cpu.workload = process

    return system


def run_simulation(args):
    """Run gem5 simulation

    Args:
        args: Command line arguments
    """
    # Create system
    print(f"Creating gem5 system with {args.hbm_config}...")
    root = Root(full_system=False)
    root.system = create_system(args)

    # Instantiate
    m5.instantiate()

    # Print configuration
    print(f"\nConfiguration:")
    print(f"  CPU type: {args.cpu_type}")
    print(f"  Number of CPUs: {args.num_cpus}")
    print(f"  HBM config: {args.hbm_config}")
    print(f"  Memory size: {args.mem_size / (1024**3):.2f} GB")
    print(f"  Binary: {args.binary}")
    print(f"  Duration: {args.duration} ticks")

    # Run simulation
    print(f"\nStarting simulation...")
    exit_event = m5.simulate(args.duration)

    # Print statistics
    print(f"\nSimulation ended at tick {m5.curTick()}")
    print(f"  Reason: {exit_event.getCause()}")

    # Output statistics
    m5.stats.dump()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='gem5 HBM4 Example')

    # CPU configuration
    parser.add_argument('--cpu-type', type=str, default='AtomicSimpleCPU',
                       choices=['AtomicSimpleCPU', 'TimingSimpleCPU', 'DerivO3CPU'],
                       help='CPU type')
    parser.add_argument('--num-cpus', type=int, default=1,
                       help='Number of CPUs')

    # Memory configuration
    parser.add_argument('--hbm-config', type=str, default='hbm4_8ch',
                       choices=['hbm4_32ch', 'hbm4_16ch', 'hbm4_8ch', 'hbm3_8ch'],
                       help='HBM configuration preset')
    parser.add_argument('--mem-size', type=str, default='1GB',
                       help='Memory size')

    # Cache configuration
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable caches (direct connect)')
    parser.add_argument('--cache-size', type=str, default='32kB',
                       help='L1 cache size')

    # Simulation configuration
    parser.add_argument('--binary', type=str, default='/tmp/test_binary',
                       help='Binary to run')
    parser.add_argument('--options', type=str, default='',
                       help='Command line options for binary')
    parser.add_argument('--duration', type=int, default=100000000,
                       help='Simulation duration in ticks')

    args = parser.parse_args()

    # Parse memory size
    mem_size = args.mem_size
    if mem_size.endswith('GB'):
        args.mem_size = int(mem_size[:-2]) * 1024**3
    elif mem_size.endswith('MB'):
        args.mem_size = int(mem_size[:-2]) * 1024**2
    elif mem_size.endswith('KB'):
        args.mem_size = int(mem_size[:-2]) * 1024
    else:
        args.mem_size = int(mem_size)

    # Run
    run_simulation(args)


if __name__ == '__main__':
    main()