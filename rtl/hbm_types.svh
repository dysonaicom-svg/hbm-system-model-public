// =============================================================================
// HBM Type Definitions
// =============================================================================
// Type definitions for High Bandwidth Memory (HBM) SystemVerilog model
// Supports HBM2, HBM3, and HBM4 specifications
// =============================================================================

`ifndef HBM_TYPES_SVH
`define HBM_TYPES_SVH

// verilator lint_off SYMRSVDWORD

// =============================================================================
// HBM4 Command Encoding (4-bit, aligned with Python hbm4_channel_model.py)
// =============================================================================
typedef enum logic [3:0] {
    CMD_NOP    = 4'd0,   // No operation
    CMD_ACT    = 4'd1,   // Activate command
    CMD_READ   = 4'd2,   // Read command
    CMD_WRITE  = 4'd3,   // Write command
    CMD_PRE    = 4'd4,   // Precharge single bank
    CMD_PREA   = 4'd5,   // Precharge all banks
    CMD_REF    = 4'd6,   // Refresh (all banks)
    CMD_RFM    = 4'd7,   // Row flash memory (refresh)
    CMD_MRS    = 4'd8    // Mode register set
} hbm_cmd_t;

// -----------------------------------------------------------------------------
// Address Structure - HBM4 RBC (Row-Bank-Channel) Mapping
// -----------------------------------------------------------------------------
// HBM4 address breakdown (42-bit effective):
// Bit positions from MSB (matching Python hbm4_address_decoder.py RBC mapping):
// - stack:       bits [47:46] (2 bits, 4 stacks)
// - channel:     bits [45:41] (5 bits, 32 channels per stack)
// - pseudo_ch:   bit  [40]    (1 bit, 2 pseudo-channels per channel)
// - bank_group:  bits [39:37] (3 bits, 8 bank groups per pseudo-channel)
// - bank:        bits [36:33] (4 bits, 16 banks per bank group)
// - row:         bits [32:17] (16 bits, 64K rows per bank)
// - col:         bits [16:11] (6 bits, 64 columns per row)
// - burst:       bits [10:9]  (2 bits, 4-beat burst alignment)
// - offset:      bits [8:6]   (3 bits, 8-byte offset within burst)
//
// Note: Fields are declared in MSB-first order for packed struct.
// Total: 2+5+1+3+4+16+6+2+3 = 42 bits

typedef struct packed {
    logic [1:0]   stack;           // Stack identifier (2 bits = 4 stacks)
    logic [4:0]   channel;         // Channel address (5 bits = 32 channels)
    logic         pseudo_ch;       // Pseudo-channel (1 bit = 2 per channel)
    logic [2:0]   bank_group;      // Bank group address (3 bits = 8 groups)
    logic [3:0]   bank;            // Bank address (4 bits = 16 banks)
    logic [15:0]  row;             // Row address (16 bits = 64K rows)
    logic [5:0]   col;             // Column address (6 bits = 64 columns)
    logic [1:0]   burst;           // Burst beat (2 bits = 4-beat alignment)
    logic [2:0]   offset;          // Byte offset within burst (3 bits = 8 bytes)
} hbm_addr_t;

// -----------------------------------------------------------------------------
// Request Type Enumeration
// -----------------------------------------------------------------------------
typedef enum logic [2:0] {
    REQ_NOP    = 3'b000,  // No operation / idle
    REQ_READ   = 3'b001,  // Read request
    REQ_WRITE  = 3'b010,  // Write request
    REQ_ACT    = 3'b011,  // Activate bank
    REQ_PRE    = 3'b100,  // Precharge bank
    REQ_REF    = 3'b101   // Refresh operation
} hbm_req_type_t;

// -----------------------------------------------------------------------------
// Request State Enumeration
// -----------------------------------------------------------------------------
typedef enum logic [2:0] {
    REQ_IDLE       = 3'b000,  // Request is idle / not active
    REQ_PENDING    = 3'b001,  // Request pending in queue
    REQ_IN_FLIGHT  = 3'b010,  // Request currently being processed
    REQ_COMPLETE   = 3'b011   // Request completed successfully
} hbm_req_state_t;

// -----------------------------------------------------------------------------
// Bank State Enumeration
// -----------------------------------------------------------------------------
typedef enum logic [2:0] {
    BANK_IDLE       = 3'b000,  // Bank is idle and available
    BANK_ACTIVE     = 3'b001,  // Bank has open row
    BANK_BUSY       = 3'b010,  // Bank is busy with operation
    BANK_REFRESH    = 3'b011,  // Bank in refresh mode
    BANK_POWER_DOWN = 3'b100   // Bank in power-down mode
} hbm_bank_state_t;

// -----------------------------------------------------------------------------
// Timing Parameters Structure - HBM4 JEDEC Values
// -----------------------------------------------------------------------------
// All timing values in clock cycles (@clk_i)
// HBM4 timing at 8 GT/s DDR (tCK = 125 ps) per JEDEC JESD270-4A
//
// Standard timing parameters:
// - tRCD:  RAS to CAS delay (activate to read/write)
// - tRP:   Row precharge time (close row)
// - tRAS:  Row active time (minimum row open time)
// - tRC:   Row cycle time (activate to activate same bank)
// - tCCD:  CAS-to-CAS delay (read/write burst spacing)
// - tRRD:  Row-to-row delay (different bank activation)
// - tFAW:  Four Bank Activation Window
// - tRFC:  Refresh cycle time
// - tREFI: Refresh interval
// - tCL:   CAS latency (read data valid after read command)
// - tCWL:  CAS write latency (write data valid after write command)

typedef struct packed {
    logic [7:0] tRCD;    // RAS to CAS delay (default: 8 cycles)
    logic [7:0] tRP;     // Row precharge time (default: 8 cycles)
    logic [7:0] tRAS;    // Row active time (default: 20 cycles)
    logic [7:0] tRC;     // Row cycle time (default: 22 cycles)
    logic [7:0] tCCD;    // CAS-to-CAS delay (default: 4 cycles)
    logic [7:0] tRRD;    // Row-to-row delay (default: 4 cycles)
    logic [7:0] tFAW;    // Four Bank Activation Window (default: 16 cycles)
    logic [7:0] tRFC;    // Refresh cycle time (default: 180 cycles)
    logic [15:0] tREFI;  // Refresh interval (default: 3900 cycles)
    logic [7:0] tCL;     // CAS latency (default: 8 cycles)
    logic [7:0] tCWL;    // CAS write latency (default: 3 cycles)
} hbm_timing_t;

// -----------------------------------------------------------------------------
// Request Structure
// -----------------------------------------------------------------------------
typedef struct packed {
    logic        valid;          // Request validity
    logic [7:0]  req_id;         // Unique request identifier
    hbm_addr_t   addr;           // Request address
    hbm_req_type_t req_type;    // Type of request
    logic [7:0]  length;         // Burst length (in beats)
    logic        req_priority;    // Request priority (1=high, 0=normal)
    hbm_req_state_t state;      // Current request state
    logic [15:0] cycle_submitted; // Cycle when request was submitted
    logic [15:0] cycle_complete;  // Cycle when request completed
} hbm_req_t;

// -----------------------------------------------------------------------------
// System Configuration Constants - HBM4 Specification
// -----------------------------------------------------------------------------
// Number of HBM4 stacks (per JEDEC JESD270-4A)
`define NUM_STACKS      4
// Number of channels per stack (HBM4: 32 channels)
`define NUM_CHANNELS    32
// Number of pseudo-channels per channel (2 for HBM4)
`define NUM_PSEUDO_CH   2
// Number of bank groups per pseudo-channel (8 for HBM4)
`define NUM_BANK_GROUPS 8
// Number of banks per bank group (16 for HBM4)
`define NUM_BANKS       16

// -----------------------------------------------------------------------------
// Default Timing Parameters - HBM4 JEDEC Values
// -----------------------------------------------------------------------------
// HBM4 timing at 8 GT/s DDR (tCK = 125 ps)
// All values in clock cycles @ clk_i
// Reference: JEDEC JESD270-4A HBM4 specification
//
// Timing parameter naming:
// - t-prefix: Traditional JEDEC naming (tRCD, tRP, tRAS)
// - n-prefix: HBM4-specific naming (nRCD, nRP, nRAS) - same values

`define HBM4_TIMING_DEFAULT  8,8,20,22,4,4,16,180,3900
// tRCD, tRP, tRAS, tRC, tCCD, tRRD, tFAW, tRFC, tREFI

// HBM2 timing for legacy compatibility (800 MHz, tCK = 1250 ps)
`define HBM2_TIMING_DEFAULT  14,14,34,48,4,4,20,160,7800

// HBM3 timing for reference (1.28 GHz, tCK = 781 ps)
`define HBM3_TIMING_DEFAULT  17,17,42,59,5,5,26,295,5000

`endif // HBM_TYPES_SVH
// verilator lint_on SYMRSVDWORD


