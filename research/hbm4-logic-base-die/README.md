# HBM4 Logic Base Die Research

This directory is an isolated research area for HBM4 logic-base-die modeling.
It is intentionally separate from the existing HBM3/Ramulator2 baseline under
`research/hbm-modeling/`.

Current scope:

- collect public HBM4 standard, protocol, vendor, and IP information;
- capture early requirements for a model that can guide HBM4 logic base die
  architecture decisions;
- separate public facts, vendor claims, assumptions, and open questions;
- avoid implementation until requirements are reviewed.

Out of scope for this first pass:

- no Python/SystemVerilog model implementation;
- no Ramulator2 HBM4 integration;
- no NDA-only JEDEC timing-table reconstruction;
- no signoff-level SI/PI/thermal model.

Directory layout:

```text
research/hbm4-logic-base-die/
  README.md
  sources/
    source_index.md
  requirements/
    requirements_capture.md
  notes/
    logic_base_die_modeling_notes.md
```

Research status as of 2026-06-15:

- public JEDEC HBM4 pages and committee listings reviewed;
- public Cadence, Synopsys, Rambus, Micron, SK hynix, and Samsung HBM4 pages
  reviewed;
- first-pass requirements captured for logic base die modeling;
- detailed implementation plan intentionally not created yet.

