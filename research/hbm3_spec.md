# HBM3 Specification Summary
## Based on JEDEC JESD238

### Key Parameters

| Parameter | HBM3 Value |
|-----------|-------------|
| Data Rate | 6.4 Gb/s/pin |
| Interface Width | 1024-bit |
| Peak Bandwidth | 819.2 GB/s |
| Max Stack Height | 16-Hi |
| Max Capacity | 64GB |
| Pseudo Channels | 8 per channel |
| Banks | 16 per pseudo channel |
| Row Size | 2KB (typical) |
| Burst Length | 32 (FLINE) |

### Timing Parameters

| Parameter | Typical Value |
|-----------|---------------|
| tCK | 781 ps |
| tRCD | 13.3 ns |
| tRP | 13.3 ns |
| tRAS | 33 ns |
| tRC | 46.3 ns |
| tCCD | 3.9 ns |
| tRRD | 3.9 ns |
| tFAW | 20 ns |
| tRFC | 230 ns (16Gb) |
| tREFI | 3.9 μs |

### Architecture

```
HBM Stack
├── 8 Channels
│   ├── 2 Pseudo Channels per Channel
│   │   ├── 16 Banks
│   │   │   └── 2 Bank Groups (HBM3)
│   │   └── Independent command/address bus
│   └── 128-bit per Pseudo Channel
└── 1024-bit aggregate I/O
```

### Reference
- JEDEC JESD238 (HBM3)
- Ramulator2: https://github.com/CMU-SAFARI/ramulator2
