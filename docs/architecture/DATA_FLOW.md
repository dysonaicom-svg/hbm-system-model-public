# Data Flow Diagrams

## Request Processing Flow

```
+------------------+     +------------------+     +------------------+
|  AXI Request     |     |  Address Decoder |     |  QoS Scheduler   |
|  (addr, size,    | --> |  (channel,       | --> |  (priority,      |
|   is_read)       |     |   bg, bank,      |     |   age)           |
+------------------+     |   row, col)      |     +------------------+
                         +------------------+            |
                                                       v
+------------------+     +------------------+     +------------------+
|  DFI Request     |     |  DFI Encoder     |     |  Request Queue   |
|  (cmd, addr,     | <-- |  (DFI 5.0        | <-- |  (FIFO, priority|
|   bank)          |     |   encoding)      |     |   sorted)        |
+------------------+     +------------------+     +------------------+
                                                       |
                                                       v
+------------------+     +------------------+     +------------------+
|  DRAM Command    |     |  Timing Check   |     |  Scheduler       |
|  (ACT, RD, WR,   | <-- |  (tRCD, tCL,    | <-- |  (ready bank     |
|   PRE, REF)      |     |   tRP, etc.)    |     |   selection)     |
+------------------+     +------------------+     +------------------+
                                                       |
                                                       v
+------------------+     +------------------+     +------------------+
|  Bank State      |     |  Row Buffer      |     |  Command         |
|  Update          | --> |  Hit/Miss        | --> |  Execution       |
|  (OPEN/CLOSED)  |     |  Decision        |     |  (memory array)  |
+------------------+     +------------------+     +------------------+
                                                       |
                                                       v
                                               +------------------+
                                               |  Response        |
                                               |  (data, latency)|
                                               +------------------+
```

## ECC Flow

```
+------------------+     +------------------+     +------------------+
|  Write Data      |     |  ECC Calculation |     |  Lane Repair     |
|  (64 bytes)      | --> |  (Hamming code)  | --> |  Check          |
+------------------+     +------------------+     +------------------+
                                                               |
                                                               v
+------------------+     +------------------+     +------------------+
|  PAM3 Encode     |     |  Channel         |     |  Data + ECC      |
|  (2-bit -> 3-lev)| <-- |  Multiplexing    | <-- |  Stored         |
+------------------+     +------------------+     +------------------+


+------------------+     +------------------+     +------------------+
|  Read Data       |     |  Lane Repair     |     |  ECC Check       |
|  Retrieved       | --> |  Decode          | --> |  (detect/correct)|
+------------------+     +------------------+     +------------------+
                                                               |
                                                               v
+------------------+     +------------------+     +------------------+
|  PAM3 Decode     |     |  Error Status    |     |  Corrected Data  |
|  (3-lev -> 2-bit| <-- |  Reported        | <-- |  Returned       |
+------------------+     +------------------+     +------------------+
```

## Refresh Flow

```
+------------------+     +------------------+     +------------------+
|  Refresh Timer   |     |  Refresh         |     |  Bank State      |
|  (tREFI cycles)  | --> |  Scheduler       | --> |  Check           |
+------------------+     +------------------+     +------------------+
                                                               |
                                                               v (all banks idle)
+------------------+     +------------------+     +------------------+
|  REFab Command   |     |  All Banks       |     |  Internal       |
|  Issued          | --> |  Refreshed       | --> |  Refreshed      |
+------------------+     +------------------+     +------------------+
                                                               |
                                                               v (all banks ready)
+------------------+     +------------------+     +------------------+
|  Return to       |     |  Row Buffer      |     |  Normal          |
|  Normal Ops      | <-- |  Invalidated    | <-- |  Operation      |
+------------------+     +------------------+     +------------------+
```

## PAM3 Signal Flow (8+ GT/s)

```
NRZ Data (2 bits)          PAM3 Symbol (3 levels)
================          ====================

  00         -->            -1 (Low)
  01         -->             0 (Mid)
  10         -->             0 (Mid)
  11         -->            +1 (High)


+------------------+     +------------------+     +------------------+
|  Data Pattern     |     |  PAM3 Encoder    |     |  Channel          |
|  [7:0]           | --> |  (2-to-3 level)  | --> |  Transmission    |
|  2 bits/symbol   |     |  + preamble      |     |  (differential)  |
+------------------+     +------------------+     +------------------+
                                                               |
                                                               v
+------------------+     +------------------+     +------------------+
|  Memory Array    |     |  PAM3 Decoder    |     |  Channel          |
|  Storage         | <-- |  (3-to-2 level)  | <-- |  Reception       |
|  (3-level cell) |     |  + alignment      |     |  (sampling)      |
+------------------+     +------------------+     +------------------+
```

## Independent Channel Timing Flow

```
Channel 0                    Channel 1                    Channel N
==========                    ==========                    ==========

    |                            |                            |
    v                            v                            v
+-------+                    +-------+                    +-------+
|tCK=62.5|                   |tCK=62.5|                   |tCK=62.5|
|ps     |                    |ps      |                   |ps      |
+-------+                    +-------+                    +-------+
    |                            |                            |
    | ACT @ cycle X             |                            |
    v                            |                            |
+-------+                        |                            |
|tRCD=12 |                       |                            |
|cycles  |                       |                            |
+-------+                        |                            |
    |                            |                            |
    | RD @ cycle X+12            | ACT @ cycle Y              |
    v                            v                            |
+-------+                    +-------+                    +-------+
|tCL=16  |                   |tRCD=12 |                   |       |
|cycles  |                   |cycles  |                   |       |
+-------+                    +-------+                    +-------+
    |                            |                            |
    | DATA @ cycle X+28         | RD @ cycle Y+12           |
    |                            v                            |
    |                     +-------+                       |
    |                     |tCL=16  |                       |
    |                     |cycles  |                       |
    |                     +-------+                       |
    |                            |                            |
    v                            v                            v
(All channels operate independently with no cross-channel constraints)
```

## Power State Flow

```
+------------------+     +------------------+     +------------------+
|  Normal Operation|     |  Idle Detection  |     |  Auto LP Entry   |
|  (LP_IDLE)      | --> |  (idle_counter)  | --> |  (LP_CTRL)       |
+------------------+     +------------------+     +------------------+
        ^                                                |
        |                                                v
        |                                     +------------------+
        |                                     |  Clock Gating    |
        |                                     |  (PLL on)        |
        |                                     +------------------+
        |                                                |
        |  LP_REQ                              v
        +------------------------------- +------------------+
                                        |  Deep LP         |
                                        |  (LP_SREF)       |
                                        +------------------+
                                                |
        LP_WAKEUP                                v
        +------------------------------- +------------------+
                                        |  Exit LP         |
                                        |  (LP_IDLE)       |
                                        +------------------+
                                                |
                                                v
                                        (Resume Normal Ops)
```
