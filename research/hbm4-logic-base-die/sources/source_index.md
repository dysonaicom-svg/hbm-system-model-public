# HBM4 Source Index

Date captured: 2026-06-15

This index tracks public sources only. JEDEC standards may require login or
registration, and vendor product pages can change over time. Treat the entries
below as inputs for requirements capture, not as final design signoff data.

## Source Classes

- **Standard**: JEDEC pages and document listings.
- **IP vendor**: Controller, PHY, VIP, and memory-subsystem IP pages.
- **Memory vendor**: HBM4 product, sampling, production, packaging, base-die,
  thermal, or power information.
- **Derived assumption**: Engineering inference made from public material.

## Standards And Protocol Sources

| Source | Type | Captured facts | Logic-base-die relevance | Confidence |
| --- | --- | --- | --- | --- |
| [JEDEC JESD270-4A HBM4 DRAM](https://www.jedec.org/standards-documents/docs/jesd270-4a) | Standard | HBM4 is distributed across independent channels; channels need not be synchronous; each channel maintains a 64-bit DDR data bus. Page links to JESD271-4 bump matrix spreadsheet. | Defines the channel-level partitioning that the logic base die must expose and schedule. Independent/non-synchronous channels imply per-channel clocking/state modeling rather than one global synchronous model. | High for page-level facts; detailed timings require standard download. |
| [JEDEC JC-42.2 HBM committee](https://www.jedec.org/committees/jc-422) | Standard | Lists recent documents: JESD270-4A HBM4 DRAM, JESD271-4 HBM4 bump map spreadsheet, JESD330-4 SPHBM4. | Confirms that bump mapping and SPHBM4 should be tracked separately from baseline HBM4. | High. |
| [JEDEC HBM4 press release, 2025-04-16](https://www.jedec.org/news/pressreleases/jedec%C2%AE-and-industry-leaders-collaborate-release-jesd270-4-hbm4-standard-advancing) | Standard / ecosystem | Announces JESD270-4 HBM4 publication for AI/HPC/graphics/server use cases, emphasizing bandwidth, power efficiency, and capacity improvements over HBM3. | Establishes the intended workload class and top-level optimization goals. | High for announcement-level facts. |

## IP Vendor Sources

| Source | Type | Captured facts | Logic-base-die relevance | Confidence |
| --- | --- | --- | --- | --- |
| [Synopsys HBM4/4E Controller IP](https://www.synopsys.com/designware-ip/interface-ip/hbm/hbm4-controller.html) | IP vendor | Standard controller connects to HBM4 PHY through extended DFI 5.1. Custom HBM4/4E variant shifts the memory controller into the base die and integrates with a TSV PHY. Public feature list includes APB registers, command scheduler, QoS, refresh management, low-power modes, DQ/CA parity, SECDED ECC, CRC, PHY management, DRAM maintenance, and pseudo-channel support. | Strongest public clue for a logic-base-die model boundary: controller-in-base-die, TSV PHY, register model, RAS, power, and training/maintenance must be modeled. | High for public feature list. |
| [Synopsys HBM IP Solution](https://www.synopsys.com/designware-ip/interface-ip/hbm.html) | IP vendor | Describes complete HBM IP solution with controller, PHY, and verification IP for multi-die AI/HPC designs; HBM4/4E pin bandwidth advertised up to 12 Gbps and over 3 TB/s interface bandwidth. | Indicates model should separate standard JEDEC operation from vendor over-speed bins and IP integration choices. | Medium-high. |
| [Synopsys HBM4 test-chip blog](https://www.synopsys.com/blogs/chip-design/worlds-first-hbm4-ip-test-chip-ai-hpc-validation.html) | IP vendor | Emphasizes validation across controller, PHY, package, interposer, and memory devices; real-memory link-up validates signaling and compatibility. | Reinforces that base-die architecture simulation must not stop at DRAM timing; package/interposer/PHY effects need at least abstract hooks. | Medium-high. |
| [Rambus HBM4 Controller IP](https://www.rambus.com/interface-ip/hbm/hbm4-controller) | IP vendor | HBM4 controller can be standalone or integrated with a chosen HBM4 PHY; page lists HBM4 protocol compatibility up to 10 Gbps for AI/HPC/graphics. | Useful for decoupling controller and PHY in the model; do not assume one fixed PHY implementation. | Medium-high. |
| [Rambus HBM overview](https://www.rambus.com/blogs/hbm3-everything-you-need-to-know/) | IP vendor / background | Public overview compares HBM generations; HBM4 uses 2048-bit interface and around 2 TB/s per device at 8 Gb/s. | Useful sanity check for peak-bandwidth formulas and model configuration defaults. | Medium. |
| [Cadence HBM4E PHY and controller](https://www.cadence.com/en_US/home/tools/silicon-solutions/design-ip/memory-interface-and-storage-ip/hbm-phy/hbm4e.html) | IP vendor | Public page describes 2048-bit total data width, 32 independent channels, 2.5D silicon-interposer routing, clocking architecture, DFI PHY Independent Mode, IEEE 1500, memory BIST, loopback, lane repair, and interposer/package support. | Adds concrete PHY/test/repair/interposer requirements that belong in a logic-base-die model interface. | High for public feature list. |
| [Cadence HBM4 AI training blog](https://community.cadence.com/cadence_blogs_8/b/ip/posts/hbm4-boosts-memory-performance-for-ai-training) | IP vendor / explainer | States 32 channels with two pseudo-channels per channel, 2048-bit interface, 8 Gb/s class standard speed, 2 TB/s class bandwidth, 16-high stack support, 24/32 Gb die densities, and DRFM for row-hammer mitigation. | Useful checklist for channel/pseudo-channel modeling, DRFM/RAS, and capacity parameterization. | Medium-high; blog should be cross-checked against JEDEC standard. |

## Memory Vendor Sources

| Source | Type | Captured facts | Logic-base-die relevance | Confidence |
| --- | --- | --- | --- | --- |
| [Micron HBM product page](https://www.micron.com/products/memory/hbm) | Memory vendor | Current public page advertises HBM4 36 GB 12H, over 11 Gb/s pin speed, greater than 2.8 TB/s bandwidth, and power-efficiency improvement versus HBM3E. | Vendor speed bins exceed JEDEC baseline; model needs speed-bin parameterization and should separate standard mode from vendor/product mode. | Medium-high; product claims may change. |
| [Micron HBM4 press release](https://investors.micron.com/news-releases/news-release-details/micron-ships-hbm4-key-customers-power-next-gen-ai-platforms) | Memory vendor | Describes 2048-bit interface, greater than 2 TB/s per stack, and 2026 ramp alignment with next-generation AI platforms. | Supports public assumption that HBM4 base die must handle 2 TB/s-class stack bandwidth and AI inference/training traffic. | Medium-high. |
| [Micron Q4 2025 prepared remarks PDF](https://investors.micron.com/static-files/5ea95475-639b-4cfc-91fd-b9b4a2bb5e63) | Memory vendor / investor | Mentions advanced CMOS base die for HBM4 and HBM4E option for customized base logic die with TSMC manufacturing. | Important for requirement capture: future custom HBM likely shifts more controller/optimization logic into base die. | Medium; investor material, not protocol spec. |
| [SK hynix HBM4 development press release](https://news.skhynix.com/sk-hynix-completes-worlds-first-hbm4-development-and-readies-mass-production) | Memory vendor | Publicly states 2048 I/O terminals, over 10 Gb/s operation, and more than 40% power-efficiency improvement versus prior generation. | Reinforces need for parameterized speed bins and power model. | Medium-high. |
| [SK hynix 12-layer HBM4 sample release](https://news.skhynix.com/sk-hynix-ships-world-first-12-layer-hbm4-samples-to-customers) | Memory vendor | Reports 12-layer HBM4 sample shipment to customers. | Stack height and capacity should be model parameters, not constants. | Medium. |
| [SK hynix iHBM thermal solution](https://news.skhynix.com/ihbm-solution) | Memory vendor / thermal | Discusses power density and D2D PHY between HBM base die and AI accelerator as a thermal competitiveness factor. | Thermal and D2D PHY power-density modeling should be included even in early architecture simulation. | Medium. |
| [Samsung HBM4 product page](https://semiconductor.samsung.com/dram/hbm/hbm4) | Memory vendor | Public page states 2048 I/O, low-voltage TSV I/O design, PDN optimization, energy-efficiency and thermal improvements, and increasing importance of the base die through memory + logic + packaging integration. | Strong input for base-die scope: PDN, TSV I/O, thermal, and packaging integration are part of the modeling problem. | Medium-high. |
| [Samsung HBM4 commercial shipment press release](https://news.samsung.com/global/samsung-ships-industry-first-commercial-hbm4-with-ultimate-performance-for-ai-computing) | Memory vendor | Describes 1c DRAM, 4 nm logic process for HBM4, 2048 I/O, 24-36 GB 12-layer products, future 16-layer direction, low-power TSV, PDN, and thermal improvements. | Shows logic base die is becoming advanced-node logic, not passive glue; model should account for area, power, clocking, and customer-specific feature tradeoffs. | Medium; vendor/product claim. |

## Derived Modeling Assumptions

| Assumption | Rationale | Validation needed |
| --- | --- | --- |
| The first model should be parameterized around JEDEC baseline plus vendor speed bins. | Public sources disagree by timing/version and vendors advertise faster-than-JEDEC products. | Download JESD270-4A and vendor datasheets under appropriate access terms. |
| Logic base die simulation needs more than DRAM timing. | Public IP pages expose controller, DFI/TSV PHY, RAS, power state, training/maintenance, test, and repair responsibilities. | Confirm actual partitioning for the intended product strategy. |
| Channel and pseudo-channel independence should be modeled explicitly. | JEDEC page states channels are independent and not necessarily synchronous; Cadence discusses 32 channels and pseudo-channels. | Confirm exact pseudo-channel behavior and command/address constraints in standard. |
| Thermal and PDN abstractions should be first-class requirements. | Samsung and SK hynix both emphasize thermal/power-density constraints; HBM4 doubles I/O width. | Calibrate with package/thermal team data. |

