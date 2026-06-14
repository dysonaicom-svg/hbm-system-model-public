# HBM Modeling Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible HBM system-modeling baseline that first runs trace-driven HBM timing experiments in Ramulator2, then leaves a clean path to integrate gem5 or DRAMSys.

**Architecture:** Start with the existing local Ramulator2 checkout as the cycle-accurate DRAM timing engine. Keep local project-owned configs, traces, scripts, and results outside the upstream checkout so experiments are reproducible and easy to compare. Use Ramulator2 HBM3 as the initial timing baseline; add HBM4-style parameters only after the HBM3 flow is validated.

**Tech Stack:** Ramulator2, C++20 compiler, CMake, Python 3, YAML, optional gem5 HBM2Stack/HBMCtrl, optional DRAMSys SystemC/TLM-2.0.

---

## Current Workspace Facts

- Existing Ramulator2 checkout: `research/ramulator2/ramulator2`
- Ramulator2 README says supported compilers include `g++-12` and `clang++-15`.
- Current machine has `cmake 3.16.3`, `g++ 9.4.0`, and `/usr/bin/clang++-18` 18.1.8.
- `g++-12`, `clang++-15`, and `clang++` are not currently found in `PATH`.
- `/usr/bin/clang++-18` compiles, links, and runs a C++20 probe using `<concepts>` and `<ranges>`.
- `/usr/bin/g++` 9.4.0 does not compile the same C++20 probe; with `-std=c++2a`, it fails because `<concepts>` is unavailable.
- The workspace root at `/home/ic/JXTF/HBM` is not a valid git repository even though an empty `.git` directory exists.

## File Structure

- Create: `research/hbm-modeling/README.md`
  - Explains the local experiment layout and the first HBM modeling flow.
- Create: `research/hbm-modeling/configs/`
  - Stores project-owned Ramulator2 YAML configs.
- Create: `research/hbm-modeling/traces/`
  - Stores synthetic memory traces for sequential, stride, random, and mixed read/write tests.
- Create: `research/hbm-modeling/scripts/`
  - Stores trace generation and experiment runner scripts.
- Create: `research/hbm-modeling/results/`
  - Stores run outputs and summarized metrics.
- Do not modify: `research/ramulator2/ramulator2/src/**` during the first baseline stage.

### Task 1: Toolchain Readiness

**Files:**
- Create: `research/hbm-modeling/README.md`

- [ ] **Step 1: Confirm the compiler state**

Run:

```bash
cmake --version
g++ --version
which g++-12
which clang++-15
ls -1 /usr/bin/clang++*
```

Expected on the current machine:

```text
cmake version 3.16.3
g++ (Ubuntu 9.4.0-1ubuntu1~20.04.2) 9.4.0
which g++-12 exits nonzero
which clang++-15 exits nonzero
/usr/bin/clang++-18 exists
```

- [ ] **Step 2: Decide how to provide a C++20 compiler**

Preferred options:

```text
Option A: Use the existing /usr/bin/clang++-18.
Option B: Install g++-12 or clang++-15 on the host.
Option C: Use a container image with g++-12 or clang++-15.
Option D: Build on another machine and copy only result artifacts back.
```

Expected decision for this workspace:

```text
Use Option A first. Install another compiler only if Ramulator2 fails with clang++-18.
```

- [ ] **Step 3: Write the local README skeleton**

Create `research/hbm-modeling/README.md` with:

```markdown
# HBM Modeling Baseline

This directory contains local HBM modeling experiments built around the existing Ramulator2 checkout at `../ramulator2/ramulator2`.

## First Goal

Run trace-driven HBM3 timing experiments in Ramulator2 and collect bandwidth, latency, row-buffer behavior, queue pressure, and address-mapping effects.

## Directory Layout

- `configs/`: project-owned Ramulator2 YAML configs
- `traces/`: synthetic memory traces
- `scripts/`: trace generators and run scripts
- `results/`: run output and summaries

## Toolchain

Ramulator2 requires a C++20-capable compiler. The upstream README lists `g++-12` and `clang++-15` as tested compilers.
```

- [ ] **Step 4: Verify README exists**

Run:

```bash
sed -n '1,120p' research/hbm-modeling/README.md
```

Expected: the README text from Step 3 is printed.

### Task 2: Build Ramulator2 Sanity Baseline

**Files:**
- Use: `research/ramulator2/ramulator2/README.md`
- Use: `research/ramulator2/ramulator2/example_config.yaml`

- [ ] **Step 1: Configure Ramulator2 with an explicit C++20 compiler**

Run one of these after the compiler decision in Task 1:

```bash
cd research/ramulator2/ramulator2
cmake -S . -B build -DCMAKE_CXX_COMPILER=g++-12
```

or:

```bash
cd research/ramulator2/ramulator2
cmake -S . -B build -DCMAKE_CXX_COMPILER=/usr/bin/clang++-18
```

Expected:

```text
Build files have been written to: /home/ic/JXTF/HBM/research/ramulator2/ramulator2/build
```

- [ ] **Step 2: Build the executable**

Run:

```bash
cd research/ramulator2/ramulator2
cmake --build build -j
```

Expected:

```text
ramulator2 executable is created under build/
libramulator.so is created under build/ or copied according to the CMake target layout
```

- [ ] **Step 3: Run the upstream DDR4 example**

Run:

```bash
cd research/ramulator2/ramulator2
./build/ramulator2 -f ./example_config.yaml
```

If the binary is created at the repository root by the build instructions, run:

```bash
cd research/ramulator2/ramulator2
./ramulator2 -f ./example_config.yaml
```

Expected:

```text
Simulation completes without a crash.
Ramulator2 prints or writes statistics for the DDR4 example configuration.
```

### Task 3: Create Project-Owned HBM3 Trace Experiments

**Files:**
- Create: `research/hbm-modeling/scripts/gen_trace.py`
- Create: `research/hbm-modeling/traces/seq_rd.trace`
- Create: `research/hbm-modeling/traces/stride_rd.trace`
- Create: `research/hbm-modeling/traces/random_rdwr.trace`

- [ ] **Step 1: Create local experiment directories**

Run:

```bash
mkdir -p research/hbm-modeling/configs research/hbm-modeling/traces research/hbm-modeling/scripts research/hbm-modeling/results
```

Expected: all four directories exist.

- [ ] **Step 2: Add the trace generator**

Create `research/hbm-modeling/scripts/gen_trace.py` with:

```python
#!/usr/bin/env python3
import argparse
import random


def write_trace(path, pattern, count, base, span, stride, write_ratio):
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

            op = "W" if rng.random() < write_ratio else "R"
            f.write(f"{addr:#x} {op}\n")


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
```

- [ ] **Step 3: Generate three baseline traces**

Run:

```bash
python3 research/hbm-modeling/scripts/gen_trace.py --out research/hbm-modeling/traces/seq_rd.trace --pattern seq --count 100000 --write-ratio 0.0
python3 research/hbm-modeling/scripts/gen_trace.py --out research/hbm-modeling/traces/stride_rd.trace --pattern stride --count 100000 --stride 4096 --write-ratio 0.0
python3 research/hbm-modeling/scripts/gen_trace.py --out research/hbm-modeling/traces/random_rdwr.trace --pattern random --count 100000 --write-ratio 0.3
```

Expected:

```text
seq_rd.trace, stride_rd.trace, and random_rdwr.trace exist under research/hbm-modeling/traces/
Each file contains 100000 address/op lines.
```

- [ ] **Step 4: Verify trace format**

Run:

```bash
sed -n '1,5p' research/hbm-modeling/traces/seq_rd.trace
sed -n '1,5p' research/hbm-modeling/traces/random_rdwr.trace
```

Expected:

```text
Each line contains one aligned hex address and one operation token, either R or W.
```

### Task 4: Add HBM3 Ramulator2 Configs

**Files:**
- Create: `research/hbm-modeling/configs/hbm3_seq.yaml`
- Create: `research/hbm-modeling/configs/hbm3_stride.yaml`
- Create: `research/hbm-modeling/configs/hbm3_random_rdwr.yaml`
- Use: `research/ramulator2/ramulator2/src/dram/impl/HBM3.cpp`

- [ ] **Step 1: Inspect HBM3 presets supported by the local checkout**

Run:

```bash
sed -n '1,240p' research/ramulator2/ramulator2/src/dram/impl/HBM3.cpp
```

Expected:

```text
The file lists HBM3 organization and timing preset names used by Ramulator2 configs.
```

- [ ] **Step 2: Copy the upstream example as the first editable config**

Run:

```bash
cp research/ramulator2/ramulator2/example_config.yaml research/hbm-modeling/configs/hbm3_seq.yaml
cp research/ramulator2/ramulator2/example_config.yaml research/hbm-modeling/configs/hbm3_stride.yaml
cp research/ramulator2/ramulator2/example_config.yaml research/hbm-modeling/configs/hbm3_random_rdwr.yaml
```

Expected: all three config files exist.

- [ ] **Step 3: Edit the three configs to use HBM3 and local traces**

In each config, set:

```yaml
MemorySystem:
  DRAM:
    impl: HBM3
```

Set each frontend trace path to the matching file:

```yaml
Frontend:
  traces:
    - ../../hbm-modeling/traces/seq_rd.trace
```

For `hbm3_stride.yaml`, use:

```yaml
Frontend:
  traces:
    - ../../hbm-modeling/traces/stride_rd.trace
```

For `hbm3_random_rdwr.yaml`, use:

```yaml
Frontend:
  traces:
    - ../../hbm-modeling/traces/random_rdwr.trace
```

Expected: each config uses `HBM3` and points to a local project-owned trace.

### Task 5: Run HBM3 Experiments and Capture Results

**Files:**
- Create: `research/hbm-modeling/scripts/run_baseline.sh`
- Create results under: `research/hbm-modeling/results/`

- [ ] **Step 1: Add the baseline runner**

Create `research/hbm-modeling/scripts/run_baseline.sh` with:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ic/JXTF/HBM"
RAMULATOR="$ROOT/research/ramulator2/ramulator2/build/ramulator2"
RESULTS="$ROOT/research/hbm-modeling/results"

mkdir -p "$RESULTS"

"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_seq.yaml" > "$RESULTS/hbm3_seq.log" 2>&1
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_stride.yaml" > "$RESULTS/hbm3_stride.log" 2>&1
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_random_rdwr.yaml" > "$RESULTS/hbm3_random_rdwr.log" 2>&1
```

- [ ] **Step 2: Make the runner executable**

Run:

```bash
chmod +x research/hbm-modeling/scripts/run_baseline.sh
```

Expected: the script is executable.

- [ ] **Step 3: Run the baseline experiments**

Run:

```bash
research/hbm-modeling/scripts/run_baseline.sh
```

Expected:

```text
research/hbm-modeling/results/hbm3_seq.log exists
research/hbm-modeling/results/hbm3_stride.log exists
research/hbm-modeling/results/hbm3_random_rdwr.log exists
```

- [ ] **Step 4: Summarize basic results**

Run:

```bash
grep -R "bandwidth\|latency\|row\|queue\|read\|write" research/hbm-modeling/results
```

Expected:

```text
The output identifies which metric names Ramulator2 emits in this build.
Use those names to create a focused parser in the next task.
```

### Task 6: Choose the System Integration Path

**Files:**
- Modify: `research/hbm-modeling/README.md`

- [ ] **Step 1: Record the decision criteria**

Append this section to `research/hbm-modeling/README.md`:

```markdown
## Next Integration Choice

Use `gem5` if the next question is CPU/SoC behavior, cache hierarchy, full-system software, or workload-level performance.

Use `DRAMSys` if the next question is SystemC/TLM virtual-platform integration, transaction-level SoC modeling, or faster DRAM-centric design-space exploration.

Use `Shuhai` or `DRAM-Bender` only when an HBM FPGA board is available and the goal is hardware calibration or reliability characterization.
```

- [ ] **Step 2: Pick one next path after the Ramulator2 baseline passes**

Recommended default:

```text
Pick gem5 when modeling a chip-level CPU/NPU/GPU subsystem with caches and traffic generators.
Pick DRAMSys when building a SystemC/TLM platform around an existing SoC virtual prototype.
```

Expected:

```text
One integration path is chosen before adding more tools.
```

## Self-Review

- Spec coverage: The plan covers the requested path from open-source HBM resources to an executable modeling workflow.
- Placeholder scan: No `TBD`, `TODO`, or undefined implementation steps remain.
- Type consistency: Paths consistently use `/home/ic/JXTF/HBM`, `research/ramulator2/ramulator2`, and `research/hbm-modeling`.
