# HBM4 Reference Models Analysis

Date: 2026-06-15

## Executive Summary

After searching and cloning major open-source DRAM/HBM simulators, **no public HBM4 model is available**. 
All existing open-source solutions support HBM2/HBM3 at best. HBM4 support requires either:
1. Academic/commercial license (DRAMSys extended features)
2. Custom implementation based on HBM3 models

## Cloned Reference Models

### 1. Ramulator 2.0 (CMU-SAFARI)

**Repository**: https://github.com/CMU-SAFARI/ramulator2
**License**: MIT
**Language**: C++

#### HBM Support
| Version | Status | File |
|---------|--------|------|
| HBM | ✅ Basic | `src/dram/impl/HBM.cpp` |
| HBM2 | ✅ Basic | `src/dram/impl/HBM2.cpp` |
| HBM3 | ✅ Full | `src/dram/impl/HBM3.cpp` |
| HBM4 | ❌ **NOT AVAILABLE** | - |

#### Architecture Highlights

**Hierarchical Node Structure**:
```
Channel → PseudoChannel → BankGroup → Bank → Row → Column
```

**Key Design Patterns**:
1. **Template-based specification**: `ImplDef<N>` for compile-time level/command names
2. **Specification LUT**: `SpecLUT` for runtime lookup of timing/organization values
3. **Timing constraints**: Populated via `populate_timingcons()` with `TimingConsEntry`
4. **Lambda-based actions**: Actions, prerequisites, row-hit/open checks as lambda functions

**Organization Presets (HBM3)**:
```cpp
{"HBM3_2Gb",   {2<<10,  128,  {1, 2,  4,  4, 1<<13, 1<<6}}},
{"HBM3_4Gb",   {4<<10,  128,  {1, 2,  4,  4, 1<<14, 1<<6}}},
{"HBM3_8Gb",   {8<<10,  128,  {1, 2,  4,  4, 1<<15, 1<<6}}},
// Format: density(Mb), DQ, {channel, pseudochannel, bankgroup, bank, row, column}
```

**Timing Presets (HBM3)**:
```cpp
{"HBM3_2Gbps", {2000, 4, 7, 7, 7, 7, 17, 19, 8, 2, 3, 2, 1, 2, 2, 3, 3, 4, 3, 15, -1, 160, 3900, -1, 8, 1000}}
// rate(MT/s), nBL, nCL, nRCDRD, nRCDWR, nRP, nRAS, nRC, nWR, nRTPS, nRTPL, nCWL, 
// nCCDS, nCCDL, nRRDS, nRRDL, nWTRS, nWTRL, nRTW, nFAW, nRFC, nRFCSB, nREFI, nREFISB, nRREFD, tCK_ps
```

**Commands**:
```
ACT, PRE, PREA, RD, WR, RDA, WRA, REFab, REFsb, RFMab, RFMsb
```

**States**:
```
Opened, Closed, N/A, Refreshing
```

#### Lessons for HBM4 Implementation

1. **Extend m_levels**: Add necessary for HBM4 (32 channels instead of 8)
2. **Update timing presets**: Base on JESD270-4A spec
3. **Modify organization**: 32 channels × 64-bit = 2048-bit interface
4. **Timing constraints**: Reference HBM3 but scale for 8+ Gb/s operation

---

### 2. DRAMSys (RPTU/Fraunhofer)

**Repository**: https://github.com/tukl-msd/DRAMSys
**License**: BSD 3-Clause (public version)
**Language**: SystemC TLM-2.0

#### HBM Support
| Version | Status | License |
|---------|--------|---------|
| HBM1 | ✅ Public | BSD |
| HBM2 | ✅ Public | BSD |
| HBM3 | ✅ Academic/Commercial | Extended license |
| HBM4 | ✅ Academic/Commercial | Extended license |

**Public version supports only HBM1/HBM2.** HBM3/4 require academic or commercial license.

#### Architecture Highlights

**SystemC TLM-2.0 Based**:
- Cycle-accurate modeling with TLM-AT protocol
- Modular design with separate controller, bank machines, power models
- Configuration via JSON files

**Key Components**:
```
Controller → BankMachine → Command → Scheduler
           → Power/DRAMPower → Thermal Model
           → ECC Schemes
```

**HBM2 Configuration Example** (`configs/memspec/HBM2.json`):
```json
{
    "memspec": {
        "memarchitecturespec": {
            "burstLength": 4,
            "dataRate": 2,
            "nbrOfBankGroups": 8,
            "nbrOfBanks": 32,
            "nbrOfPseudoChannels": 2,
            "nbrOfRows": 32768,
            "width": 64
        },
        "memtimingspec": {
            "RL": 17, "WL": 7, "RAS": 28, "RC": 42,
            "RCDRD": 12, "RCDWR": 6, "RP": 14,
            "REFI": 3900, "RFC": 220,
            // ... full timing spec
        }
    }
}
```

**Address Mapping Example** (`configs/addressmapping/am_hbm2_16Gb-8H_pc_brc.json`):
```json
{
    "addressmapping": {
        "BURST_BIT": [0, 1, 2, 3, 4],
        "PSEUDOCHANNEL_BIT": [5],
        "BANKGROUP_BIT": [6, 7],
        "BANK_BIT": [8, 9],
        "STACK_BIT": [10],
        "COLUMN_BIT": [11, 12, 13, 14, 15],
        "ROW_BIT": [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    }
}
```

#### Lessons for HBM4 Implementation

1. **JSON configuration**: Easy to extend for HBM4 parameters
2. **Bit-granular address mapping**: Important for HBM4's 32-channel configuration
3. **DRAMPower integration**: Good power modeling reference
4. **Trace Analyzer**: Useful for debugging (full version requires license)

---

### 3. Original Ramulator

**Repository**: https://github.com/CMU-SAFARI/ramulator
**License**: MIT
**Language**: C++

#### HBM Support
| Version | Status | Notes |
|---------|--------|-------|
| HBM | ✅ Full | Original implementation |

**Configuration**: `configs/HBM-config.cfg`
```
standard = HBM
channels = 8
speed = HBM_1Gbps
org = HBM_4Gb
```

#### Reference Config Values
- 8 channels
- 1 rank
- HBM_1Gbps speed
- HBM_4Gb organization

---

## Comparison of Reference Models

| Aspect | Ramulator 2.0 | DRAMSys | Original Ramulator |
|--------|---------------|---------|-------------------|
| **Language** | C++17 | SystemC TLM-2.0 | C++11 |
| **Accuracy** | Cycle-accurate | Cycle-accurate (TLM-AT) | Cycle-accurate |
| **Speed** | Fast | Medium | Fast |
| **Config Format** | YAML | JSON | Config file |
| **Power Model** | Basic | DRAMPower integration | None |
| **ECC Support** | Plugin architecture | Built-in schemes | None |
| **HBM2 Support** | ✅ | ✅ | ✅ |
| **HBM3 Support** | ✅ | ✅ (license) | ❌ |
| **HBM4 Support** | ❌ | ✅ (license) | ❌ |
| **Maintainability** | Active (CMU) | Active (Fraunhofer) | Historical |

---

## Recommended Approach for HBM4

Based on the analysis, the recommended approach is:

### Option 1: Extend Ramulator 2.0 (Recommended)
1. Create `HBM4.cpp` based on `HBM3.cpp`
2. Update organization for 32 channels
3. Add HBM4 timing presets based on JESD270-4A
4. Extend address mapper for HBM4 addressing

**Advantages**:
- Modern, modular architecture
- Active maintenance by CMU
- Easy to extend with YAML configs
- Good for integration with gem5

### Option 2: Extend DRAMSys (If SystemC Required)
1. Request academic license from DRAMSys team
2. Or implement HBM4 from HBM2 spec
3. Extend JSON configuration

**Advantages**:
- TLM-2.0 standard interface
- Commercial-grade architecture
- Built-in power/thermal models

### Option 3: Build Custom (Your Current Approach)
1. Use existing JXTF/HBM Python models
2. Extend based on research findings
3. Add HBM4-specific features

**Advantages**:
- Full control over architecture
- Matches your existing codebase
- No external dependencies

---

## Key Technical Insights from Reference Models

### HBM Addressing (From DRAMSys HBM2)
```
Bit 0-4:   BURST_BIT (burst alignment)
Bit 5:     PSEUDOCHANNEL_BIT
Bit 6-7:   BANKGROUP_BIT
Bit 8-9:   BANK_BIT
Bit 10:    STACK_BIT
Bit 11-15: COLUMN_BIT
Bit 16-30: ROW_BIT
```

### HBM4 Expected Addressing (Extended)
```
Bit 0-4:   BURST_BIT (4 beats × 64-bit = 256-bit FLINE)
Bit 5:     PSEUDOCHANNEL_BIT (2 per channel)
Bit 6-8:   BANKGROUP_BIT (8 groups for HBM4)
Bit 9-13:  BANK_BIT (16 banks per group = 128 banks)
Bit 14-18: CHANNEL_BIT (32 channels)
Bit 19:    STACK_BIT
Bit 20-35: ROW_BIT (16K-256K rows)
Bit 36-41: COLUMN_BIT
```

### HBM3 Timing Reference (From Ramulator 2.0)
```cpp
// HBM3_2Gbps preset
{2000,  // rate (MT/s)
 4,     // nBL (burst length)
 7,     // nCL (CAS latency)
 7,     // nRCDRD
 7,     // nRCDWR
 7,     // nRP
 17,    // nRAS
 19,    // nRC
 8,     // nWR
 2,     // nRTPS
 3,     // nRTPL
 2,     // nCWL
 1,     // nCCDS
 2,     // nCCDL
 2,     // nRRDS
 3,     // nRRDL
 3,     // nWTRS
 4,     // nWTRL
 3,     // nRTW
 15,    // nFAW
 160,   // nRFC
 3900,  // nREFI
 8,     // nRREFD
 1000}  // tCK_ps
```

### HBM4 Expected Timing (Estimated for 8 GT/s)
```cpp
// HBM4_8Gbps estimated
{4000,  // rate (MT/s) - double from HBM3
 4,     // nBL
 8,     // nCL (may increase for higher rate)
 8,     // nRCDRD
 8,     // nRCDWR
 8,     // nRP
 20,    // nRAS
 22,    // nRC
 8,     // nWR
 2,     // nRTPS
 3,     // nRTPL
 3,     // nCWL
 2,     // nCCDS
 3,     // nCCDL
 3,     // nRRDS
 4,     // nRRDL
 4,     // nWTRS
 5,     // nWTRL
 4,     // nRTW
 16,    // nFAW
 180,   // nRFC (may increase with higher density)
 3900,  // nREFI
 8,     // nRREFD
 625}   // tCK_ps (1250ps / 2 for DDR)
```

---

## Next Steps

1. **Confirm HBM4 timing parameters** from JESD270-4A (requires access)
2. **Decide on base implementation**: Ramulator 2.0 vs custom Python
3. **Define HBM4 organization**: 32 channels, pseudo-channels, bank groups
4. **Create HBM4 configuration template**: Based on HBM3 config extensions
5. **Implement HBM4 model**: Based on chosen approach

---

## Contact for Extended DRAMSys

If academic collaboration is feasible:
- Email: DRAMSys@iese.fraunhofer.de
- Website: https://dramsys.de