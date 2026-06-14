# Logic Base Die Modeling Notes

Date: 2026-06-15

## Key Interpretation

HBM4 logic base die modeling should be treated as a **memory-subsystem
architecture problem**, not just a DRAM timing problem.

Public sources point to a broader base-die role:

- distributed independent channel interfaces;
- 2048-bit class aggregate stack interface;
- controller-in-base-die options for custom HBM;
- TSV PHY and host-facing D2D PHY boundaries;
- DFI-like controller/PHY split in standard IP flows;
- refresh management and row-hammer mitigation;
- ECC/parity/CRC and retry/reporting features;
- lane repair, MBIST, loopback, and training;
- PDN, thermal, and power-density constraints.

## Model Layers

### Layer 0: Public Configuration Layer

Purpose: hold standard/vendor parameters without committing to one product.

Examples:

- JEDEC baseline speed class;
- vendor over-speed bins;
- number of channels and pseudo-channels;
- stack height and die density;
- voltage and power points;
- supported RAS/ECC/CRC features;
- bump-map and physical-lane metadata.

### Layer 1: Transaction And Workload Layer

Purpose: generate traffic that stresses the base die.

Examples:

- sequential streaming;
- row-local tensor-tile traffic;
- random gather/scatter;
- mixed read/write inference traffic;
- refresh/thermal stress traces;
- multi-tenant QoS traffic.

### Layer 2: Logic Base Die Controller Layer

Purpose: answer controller placement and scheduling questions.

Examples:

- controller clusters;
- per-channel schedulers;
- pseudo-channel arbiters;
- request/command/response queues;
- read/write turnaround;
- refresh management;
- QoS and fairness;
- register/firmware-visible state.

### Layer 3: PHY, TSV, And Repair Layer

Purpose: estimate non-DRAM-array overhead.

Examples:

- TSV PHY state and latency;
- host-facing D2D PHY state and latency;
- training and retraining events;
- lane repair and remap;
- MBIST and loopback states;
- frequency change and low-power transitions.

### Layer 4: Power, Thermal, And Package Layer

Purpose: expose design constraints that can invalidate peak-bandwidth results.

Examples:

- command energy;
- PHY energy;
- ECC/RAS logic energy;
- clocking energy;
- controller-cluster power;
- thermal resistance proxy;
- throttling policy;
- PDN/voltage operating point.

## Early Architecture Decisions To Explore

- Full controller in HBM logic base die vs split controller/PHY partition.
- One controller cluster per channel group vs finer per-channel scheduling.
- Fixed pseudo-channel mapping vs workload-aware address interleaving.
- Central RAS/ECC block vs distributed per-channel RAS/ECC.
- Global throttling vs per-channel/per-slice throttling.
- Training/repair handled as rare events vs modeled as service interruptions.

## Risks And Unknowns

- Public sources do not provide enough timing detail for a cycle-accurate
  compliant model.
- Vendor speed bins can exceed JEDEC baseline and may require product-specific
  timing/power values.
- HBM4E and custom HBM may change base-die responsibilities.
- Bump-map and floorplan effects can dominate real implementation constraints.
- Thermal and PDN behavior need package/team data for calibration.
- Commercial IP feature lists reveal likely responsibilities but not exact
  microarchitecture.

## Recommended Next Research Step

Before coding, answer one architecture-scope question:

Should the first model assume the HBM4 logic base die contains the **full memory
controller**, or should it assume a **split architecture** where the host die owns
most scheduling and the HBM logic base die owns PHY, TSV, test, repair, RAS, and
maintenance support?

That choice changes nearly every model boundary.

