// =============================================================================
// HBM Type Definitions
// =============================================================================
// Type definitions for High Bandwidth Memory (HBM) SystemVerilog model
// =============================================================================

`ifndef HBM_TYPES_SVH
`define HBM_TYPES_SVH

// verilator lint_off SYMRSVDWORD

// -----------------------------------------------------------------------------
// Address Structure
// -----------------------------------------------------------------------------
// HBM address breakdown:
// - stack:      3 bits (8 stacks maximum)
// - channel:    3 bits (8 channels per stack)
// - bank_group: 3 bits (8 bank groups per channel)
// - bank:       4 bits (16 banks per bank group)
// - row:       16 bits (64K rows per bank)
// - col:       10 bits (1K columns per row, with sub-bank interleaving)

typedef struct packed {
    logic [15:0] row;        // Row address
    logic [9:0]  col;        // Column address
    logic [3:0]  bank;       // Bank address (4 bits = 16 banks)
    logic [2:0]  bank_group; // Bank group address
    logic [2:0]  channel;    // Channel address
    logic [2:0]  stack;      // Stack identifier
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
// DRAM Command Enumeration
// -----------------------------------------------------------------------------
typedef enum logic [2:0] {
    CMD_NOP    = 3'b000,  // No operation
    CMD_ACT    = 3'b001,  // Activate command
    CMD_READ   = 3'b010,  // Read command
    CMD_WRITE  = 3'b011,  // Write command
    CMD_PRE    = 3'b100,  // Precharge (single bank)
    CMD_PRE_AB = 3'b101,  // Precharge all banks
    CMD_REF    = 3'b110   // Refresh command
} hbm_cmd_t;

// -----------------------------------------------------------------------------
// Timing Parameters Structure
// -----------------------------------------------------------------------------
// All timing values in clock cycles (@clk_i)
// Typical HBM timing values for reference:
// - tRCD:  CAS to RAS delay (activate to read/write)
// - tRP:   Row precharge time
// - tRAS:  Row active time
// - tRC:   Row cycle time (activate to activate)
// - tCCD:  CAS-to-CAS delay (read/write burst spacing)
// - tRRD:  Row-to-row delay (different bank activation)
// - tFAW:  Four Bank Activation Window
// - tRFC:  Refresh cycle time
// - tREFI: Refresh interval

typedef struct packed {
    logic [7:0] tRCD;   // RAS to CAS delay (default: 4 cycles)
    logic [7:0] tRP;    // Row precharge time (default: 4 cycles)
    logic [7:0] tRAS;   // Row active time (default: 16 cycles)
    logic [7:0] tRC;    // Row cycle time (default: 20 cycles)
    logic [7:0] tCCD;   // CAS-to-CAS delay (default: 4 cycles)
    logic [7:0] tRRD;   // Row-to-row delay (default: 4 cycles)
    logic [7:0] tFAW;   // Four Bank Activation Window (default: 16 cycles)
    logic [7:0] tRFC;   // Refresh cycle time (default: 80 cycles)
    logic [15:0] tREFI; // Refresh interval (default: 3120 cycles)
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
// System Configuration Constants
// -----------------------------------------------------------------------------
// Number of HBM stacks
`define NUM_STACKS      8
// Number of channels per stack
`define NUM_CHANNELS    8
// Number of bank groups per channel
`define NUM_BANK_GROUPS 8
// Number of banks per bank group
`define NUM_BANKS       16

// -----------------------------------------------------------------------------
// Default Timing Parameters
// -----------------------------------------------------------------------------
// Standard HBM2 timing at 1GHz (1ns cycle time)
// tRCD, tRP, tRAS, tRC, tCCD, tRRD, tFAW, tRFC, tREFI
`define HBM_TIMING_DEFAULT  4,4,16,20,4,4,16,80,3120

`endif // HBM_TYPES_SVH
// verilator lint_on SYMRSVDWORD


