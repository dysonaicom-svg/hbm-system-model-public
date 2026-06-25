# Component Interaction Diagrams

## Controller-Channel Interaction

```
HBM4Controller                          HBM4Channel
     |                                      |
     |  submit_request(addr)                |
     |------------------------------------->|
     |                                      |
     |  [Address Decoder]                    |
     |  + channel = addr[31:27]              |
     |  + pseudo_ch = addr[26]               |
     |  + bank_group = addr[25:23]           |
     |  + row = addr[20:05]                  |
     |                                      |
     |  issue_command(ACT, ...)             |
     |------------------------------------->|
     |                                      |
     |  [Bank State Machine]                 |
     |  + check can_activate()               |
     |  + update state to OPEN               |
     |                                      |
     |<------------------------------------ |
     |  return (success)                     |
     |                                      |
     |  issue_command(RD, ...)              |
     |------------------------------------->|
     |                                      |
     |  [Row Hit Check]                      |
     |  + check open_row == request_row      |
     |                                      |
     |<------------------------------------ |
     |  return (success, row_hit)            |
     |                                      |
     |  tick()                               |
     |------------------------------------->|
     |  [Update State Machines]               |
     |                                      |
```

## DFI Interface Interaction

```
Controller                          DFI5Interface                      PHY
    |                                    |                              |
    |  encode_command(ACT, ...)          |                              |
    |----------------------------------->|                              |
    |                                    |                              |
    |  [Validate Command]                |                              |
    |                                    |                              |
    |  queue_request(request)            |                              |
    |----------------------------------->|                              |
    |                                    |                              |
    |                                    |  tick()                      |
    |                                    |----------------------------->|
    |                                    |                              |
    |                                    |  [Process Command]           |
    |                                    |                              |
    |<-----------------------------------|                              |
    |  get_next_request()                |                              |
    |                                    |                              |
    |                                    |  <-- ctrlupd_ack             |
    |                                    |<-----------------------------|
    |                                    |                              |
    |                                    |  <-- rddata_en               |
    |                                    |<-----------------------------|
```

## Logic Base Die Interactions

```
Controller                      HBM4LogicBaseDie                PAM3Encoder
    |                                  |                              |
    |  process_command(...)            |                              |
    |--------------------------------->|                              |
    |                                  |                              |
    |  [Channel Routing]               |                              |
    |                                  |                              |
    |                                  |  encode_data(data)           |
    |                                  |----------------------------->|
    |                                  |                              |
    |                                  |  [PAM3 Encoding]             |
    |                                  |  + 2 bits -> 3 levels        |
    |                                  |                              |
    |                                  |<-----------------------------|
    |                                  |  return symbols[]            |
    |                                  |                              |
    |                                  |  [Lane Repair Check]         |
    |                                  |                              |
    |                                  |  [ECC Calculation]           |
    |                                  |                              |
    |<---------------------------------|                              |
    |  return result                   |                              |
```

## Channel Array Interaction

```
HBM4ChannelArray                    HBM4Channel[0..31]
       |                                    |
       |  tick()                           |
       |---------------------------------->|
       |                                    |
       |  [Parallel Processing]             |
       |                                    |
       |  Channel 0: ACT pending            |
       |  Channel 1: RD in progress         |
       |  ...                               |
       |  Channel 31: WR queued             |
       |                                    |
       |<----------------------------------|
       |  return states[]                  |
       |                                    |
       |  validate_all_timing()             |
       |---------------------------------->|
       |                                    |
       |  [Violation Check]                 |
       |                                    |
       |<----------------------------------|
       |  return violations[]               |
```

## RTL Co-Simulation Interaction

```
Python Model                       RTLInterface                       RTL Sim
     |                                  |                               |
     |  send_request(...)                |                               |
     |--------------------------------->|                               |
     |                                  |                               |
     |                                  |  convert_to_rtl(request)      |
     |                                  |------------------------------>|
     |                                  |                               |
     |                                  |  [Verilator Simulation]       |
     |                                  |                               |
     |                                  |<------------------------------|
     |                                  |  return rtl_response         |
     |                                  |                               |
     |<---------------------------------|                               |
     |  return result                   |                               |
     |                                  |                               |
     |  compare_results(model, rtl)     |                               |
     |--------------------------------->|                               |
     |                                  |                               |
```

## QoS Scheduler Interaction

```
HBM4Controller                      HBM4QoSScheduler                 RequestQueue
     |                                  |                               |
     |  submit_request(..., qos=10)    |                               |
     |--------------------------------->|                               |
     |                                  |                               |
     |                                  |  [Priority Queue Insert]      |
     |                                  |                               |
     |                                  |  enqueue(request)             |
     |                                  |----------------------------->|
     |                                  |                               |
     |                                  |  [Queue State]                |
     |                                  |  + depth: 512                |
     |                                  |  + oldest: qos=2              |
     |                                  |  + newest: qos=10            |
     |                                  |                               |
     |<---------------------------------|                               |
     |  return request_id               |                               |
     |                                  |                               |
     |  get_next_request()              |                               |
     |--------------------------------->|                               |
     |                                  |                               |
     |                                  |  [Highest Priority]          |
     |                                  |  return qos=10 request        |
     |                                  |<------------------------------|
```

## Refresh Scheduler Interaction

```
HBM4Controller                      HBM4RefreshScheduler              HBM4Channel
     |                                  |                               |
     |  tick()                          |                               |
     |--------------------------------->|                               |
     |                                  |                               |
     |                                  |  [Refresh Counter]            |
     |                                  |  + tREFI: 7800 cycles         |
     |                                  |  + count: 7654               |
     |                                  |                               |
     |                                  |  if count >= tREFI:          |
     |                                  |    issue REFRESH             |
     |                                  |----------------------------->|
     |                                  |                               |
     |                                  |  [Bank State: IDLE Required] |
     |                                  |------------------------------>|
     |                                  |                               |
```

## Training Sequence Interaction

```
Controller                          DFIPhyIF                      PHY
    |                                  |                              |
    |  start_training()                |                              |
    |--------------------------------->|                              |
    |                                  |                              |
    |                                  |  [Training Phases]           |
    |                                  |  + DRAM_RESET                |
    |                                  |  + WRITE_LEVELING            |
    |                                  |  + READ_GATE_TRAINING        |
    |                                  |  + READ DQ TRAINING          |
    |                                  |  + WRITE DQ TRAINING         |
    |                                  |  + VREF_CALIBRATION         |
    |                                  |                              |
    |                                  |  [Write Leveling]            |
    |  issue_command(WRLVL, ...)       |----------------------------->|
    |--------------------------------->|                              |
    |                                  |                              |
    |                                  |<------------------------------|
    |                                  |  return training_data        |
    |                                  |                              |
    |  [Adjust Delays]                 |                              |
    |                                  |                              |
    |  complete_training()             |                              |
    |--------------------------------->|                              |
    |                                  |                              |
```

## Error Handling Flow

```
Normal Operation                    Error Detected                    Recovery
     |                                    |                               |
     |  process_command(WR)              |                               |
     |  +------------------------------>|                               |
     |                                    |                               |
     |                                    |  [ECC Check]                 |
     |                                    |  + bit_error_detected        |
     |                                    |                               |
     |  <-------------------------------+|                               |
     |  return (success)                 |                               |
     |                                    |                               |
     |                                    |  correct_error(data)         |
     |                                    |  +------------------------->|
     |                                    |  |                          |
     |                                    |  |  [Hamming ECC]           |
     |                                    |  |  + detect 2-bit errors   |
     |                                    |  |  + correct 1-bit errors  |
     |                                    |  |                          |
     |                                    |  <-------------------------+|
     |                                    |  return corrected_data      |
     |                                    |                               |
     |                                    |  log_error(event)            |
     |                                    |  +------------------------->|
     |                                    |  |                          |
     |                                    |  |  [Error Record]          |
     |                                    |  |  + type: ECC_CORRECTED   |
     |                                    |  |  + cycle: 12345           |
     |                                    |  |  + channel: 7             |
```

## Power State Flow

```
Normal Operation                    Power Down                        Low Power
     |                                    |                               |
     |  tick()                           |                               |
     |                                    |                               |
     |  [Active Power]                   |                               |
     |  + dynamic: ~150 mW/channel       |                               |
     |  + leakage: ~50 mW/channel        |                               |
     |                                    |                               |
     |                                    |  enter_low_power_state()     |
     |                                    |----------------------------->|
     |                                    |                              |
     |                                    |  [Clock Gating]              |
     |                                    |                              |
     |                                    |  [Power Reduction]           |
     |                                    |  + ~70% reduction           |
     |                                    |                              |
     |                                    |<-----------------------------|
     |                                    |  return success             |
     |                                    |                               |
```
