// =============================================================================
// HBM Type Definitions
// =============================================================================
// Type definitions for High Bandwidth Memory (HBM) SystemVerilog model
// Supports HBM2, HBM3, and HBM4 specifications
// DFI 5.0/5.1 Compliance for HBM4 Controller-PHY Interface
// Reference: DFI 5.0 Specification, JEDEC JESD270-4A
// =============================================================================

`ifndef HBM_TYPES_SVH
`define HBM_TYPES_SVH

// verilator lint_off SYMRSVDWORD

// =============================================================================
// DFI 5.0 Version and Compliance
// =============================================================================
`define DFI_VERSION_MAJOR  5
`define DFI_VERSION_MINOR  0
`define DFI_COMPLIANT

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

// =============================================================================
// DFI 5.0 Command Encoding
// DFI commands are the interface protocol between controller and PHY
// Reference: DFI 5.0 Specification Table 4-1
// =============================================================================
typedef enum logic [3:0] {
    DFI_CMD_NOP    = 4'b0000,  // No operation
    DFI_CMD_ACT   = 4'b0001,  // Activate
    DFI_CMD_PRE   = 4'b0010,  // Precharge
    DFI_CMD_PREA  = 4'b0011,  // Precharge all
    DFI_CMD_RD    = 4'b0100,  // Read
    DFI_CMD_WR    = 4'b0101,  // Write
    DFI_CMD_RDA   = 4'b0110,  // Read with auto-precharge
    DFI_CMD_WRA   = 4'b0111,  // Write with auto-precharge
    DFI_CMD_REFab = 4'b1000,  // All-bank refresh
    DFI_CMD_REFsb = 4'b1001,  // Per-bank refresh
    DFI_CMD_RFMab = 4'b1010,  // All-bank row flash memory refresh
    DFI_CMD_RFMsb = 4'b1011,  // Per-bank row flash memory refresh
    DFI_CMD_MRS   = 4'b1100,  // Mode register set
    DFI_CMD_SRE   = 4'b1101,  // Self-refresh entry
    DFI_CMD_SRX   = 4'b1110,  // Self-refresh exit
    DFI_CMD_PDE   = 4'b1111   // Power-down entry
} dfi_cmd_t;

// =============================================================================
// DFI 5.0 Low Power State Machine States
// Reference: DFI 5.0 Specification Section 3.4
// =============================================================================
typedef enum logic [1:0] {
    DFI_LP_IDLE          = 2'b00,  // Normal operation state
    DFI_LP_CTRL          = 2'b01,  // Controller low-power state (PHY still active)
    DFI_LP_DATA          = 2'b10,  // Data path low-power state
    DFI_LP_FREQ_CHANGE   = 2'b11   // Frequency change in progress
} dfi_lp_state_t;

// =============================================================================
// DFI 5.0 Frequency Change State Machine States
// Reference: DFI 5.0 Specification Section 3.5
// =============================================================================
typedef enum logic [2:0] {
    DFI_FC_IDLE      = 3'b000,  // Normal operation, no frequency change
    DFI_FC_REQUESTED = 3'b001,  // Frequency change requested
    DFI_FC_ENTERING  = 3'b010,  // Entering frequency change state
    DFI_FC_ACTIVE    = 3'b011,  // In frequency change (PHY being reconfigured)
    DFI_FC_EXITING   = 3'b100,  // Exiting frequency change state
    DFI_FC_LOCKING   = 3'b101,  // PLL/DLL re-locking phase
    DFI_FC_COMPLETE  = 3'b110   // Frequency change complete
} dfi_fc_state_t;

// =============================================================================
// DFI 5.0 Signal Bundles
// Complete signal definitions for Controller-to-PHY and PHY-to-Controller
// Reference: DFI 5.0 Specification Tables 4-1 through 4-4
// =============================================================================

// DFI Address type - expanded for HBM4 42-bit addressing
typedef struct packed {
    logic [15:0] row;            // Row address (16 bits, 64K rows)
    logic [5:0]  col;           // Column address (6 bits, 64 columns)
    logic [3:0]  bank;          // Bank address (4 bits, 16 banks)
    logic [2:0]  bank_group;   // Bank group address (3 bits, 8 groups)
    logic        pseudo_ch;     // Pseudo-channel (1 bit, 2 per channel)
    logic [4:0]  channel;      // Channel address (5 bits, 32 channels)
    logic [1:0]  stack;        // Stack identifier (2 bits, 4 stacks)
} dfi_addr_t;

// DFI Control Update Signals (DFI 5.0)
typedef struct packed {
    logic        ctrlupd_req;      // Controller requests control update
    logic        ctrlupd_ack;      // PHY acknowledges control update
    logic        ctrlupd_auto;     // Auto-control update enable
} dfi_ctrlupd_t;

// DFI Frequency Change Signals (DFI 5.0)
typedef struct packed {
    logic        freq_change_en;   // Controller requests frequency change
    logic        freq_change_ack;  // PHY acknowledges frequency change
    logic [7:0]  freq_target;     // Target frequency (in 100 MHz units)
    logic [7:0]  freq_current;    // Current frequency indicator
} dfi_freq_change_t;

// DFI Power Management Signals (DFI 5.0)
typedef struct packed {
    logic        pwr_up_req;       // Controller requests power up
    logic        pwr_up_done;      // Power-up sequence complete
    logic        pwr_down_req;     // Controller requests power down
    logic        pwr_down_ack;     // PHY acknowledges power down
    logic [1:0]  pwr_state;       // Power state indicator
} dfi_power_t;

// DFI Low Power State Signals (DFI 5.0)
typedef struct packed {
    logic        lp_req;           // Low power entry request
    logic        lp_ack;           // Low power acknowledgment
    logic        lp_wakeup;        // Low power wakeup signal
    logic [1:0]  lp_state;        // Current low power state
    logic        lp_force_cmd;     // Force commands during LP exit
} dfi_lp_ctrl_t;

// DFI Training and Calibration Signals (DFI 5.0)
typedef struct packed {
    logic        training_req;     // Training request
    logic        training_ack;     // Training acknowledgment
    logic        cal_req;          // Calibration request
    logic        cal_done;         // Calibration complete
    logic [3:0]  training_mode;   // Training mode selector
    logic        training_start;  // Training sequence start
} dfi_training_t;

// DFI Data Control Signals
typedef struct packed {
    logic        wrdata_en;        // Write data enable
    logic        wrdata_mask;      // Write data mask
    logic        rddata_en;        // Read data enable
    logic        rddata_valid;     // Read data valid
    logic [7:0]  rddata_offset;   // Read data offset compensation
} dfi_data_ctrl_t;

// DFI Complete Signal Bundle (Controller to PHY)
typedef struct packed {
    // Command and address
    logic        cmd_en;           // Command enable
    logic [3:0]  cmd;              // Command code
    dfi_addr_t   addr;             // Address
    logic [3:0]  bank;             // Bank address (redundant for convenience)
    logic        chip;             // Chip select

    // Control update (DFI 5.0)
    logic        ctrlupd_req;      // Control update request

    // Frequency change (DFI 5.0)
    logic        freq_change_en;   // Frequency change enable

    // Power management (DFI 5.0)
    logic        pwr_up_req;       // Power up request
    logic        pwr_down_req;     // Power down request

    // Low power (DFI 5.0)
    logic        lp_req;           // Low power request
    logic        lp_wakeup;        // Low power wakeup

    // Training (DFI 5.0)
    logic        training_req;     // Training request
    logic        cal_req;          // Calibration request

    // Data control
    logic        wrdata_en;        // Write data enable
    logic        rddata_en;        // Read data enable
} dfi_ctrl_phy_t;

// DFI Complete Signal Bundle (PHY to Controller)
typedef struct packed {
    // Status
    logic        phy_ready;        // PHY ready indicator
    logic        lp_ack;           // Low power acknowledgment
    logic        ctrlupd_ack;      // Control update acknowledgment
    logic        freq_change_ack;  // Frequency change acknowledgment
    logic        pwr_up_done;      // Power up done
    logic        pwr_down_ack;    // Power down acknowledgment

    // Training status (DFI 5.0)
    logic        training_ack;     // Training acknowledgment
    logic        cal_done;        // Calibration done
    logic [1:0]  cal_status;      // Calibration status
    logic        training_complete;// Training sequence complete

    // Data status
    logic        rddata_valid;     // Read data valid
    logic        rddata_en;        // Read data enable

    // LP state indicator
    logic [1:0]  lp_state;        // Current low power state
} dfi_phy_ctrl_t;

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

// =============================================================================
// DFI 5.0 Timing Parameters
// Reference: DFI 5.0 Specification Table 3-1
// All values in clock cycles @ dfi_clk
// =============================================================================

typedef struct packed {
    // PHY write latency parameters
    logic [7:0] tPHY_wrlAT;      // PHY write data ready time (default: 5 cycles)
    logic [7:0] tPHY_wrlAT_max;  // Maximum write latency (default: 10 cycles)

    // PHY read latency parameters
    logic [7:0] tPHY_rdLat;      // PHY read data delay (default: 5 cycles)
    logic [7:0] tPHY_rdLat_max;  // Maximum read latency (default: 10 cycles)

    // Frequency change timing (DFI 5.0)
    logic [7:0] tFC_LATENCY;     // Frequency change latency (default: 8 cycles)
    logic [7:0] tFC_EXIT;        // Exit frequency change (default: 4 cycles)

    // Low power entry/exit timing (DFI 5.0)
    logic [7:0] tLP_CTRL_ENTER;  // LP_CTRL entry latency (default: 2 cycles)
    logic [7:0] tLP_CTRL_EXIT;   // LP_CTRL exit latency (default: 2 cycles)
    logic [7:0] tLP_DATA_ENTER;  // LP_DATA entry latency (default: 4 cycles)
    logic [7:0] tLP_DATA_EXIT;   // LP_DATA exit latency (default: 4 cycles)

    // Control update timing (DFI 5.0)
    logic [7:0] tCTRLUPD_LATENCY;// Control update acknowledgment latency (default: 4 cycles)

    // Power management timing (DFI 5.0)
    logic [7:0] tPWR_UP;         // Power-up latency (default: 2 cycles)
    logic [7:0] tPWR_DOWN;       // Power-down latency (default: 2 cycles)
} dfi_timing_t;

// DFI 5.0 Default Timing Parameters
`define DFI_TIMING_DEFAULT  5,10,5,10,8,4,2,2,4,4,4,2,2
// tPHY_wrlAT, tPHY_wrlAT_max, tPHY_rdLat, tPHY_rdLat_max,
// tFC_LATENCY, tFC_EXIT,
// tLP_CTRL_ENTER, tLP_CTRL_EXIT, tLP_DATA_ENTER, tLP_DATA_EXIT,
// tCTRLUPD_LATENCY, tPWR_UP, tPWR_DOWN

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

// =============================================================================
// DFI 5.0 Interface Configuration Constants
// =============================================================================
`define DFI_MAX_FREQ_RATIO    4     // Maximum frequency ratio supported
`define DFI_MIN_LATENCY       2     // Minimum latency in cycles
`define DFI_MAX_LATENCY       255   // Maximum latency value
`define DFI_LP_TIMEOUT        1000  // Low power timeout in cycles
`define DFI_CTRLUPD_TIMEOUT   256   // Control update timeout

// DFI 5.0 Frequency Change Configuration
`define DFI_FC_MIN_FREQ       100   // Minimum frequency (100 MHz)
`define DFI_FC_MAX_FREQ       1600  // Maximum frequency (1600 MHz)
`define DFI_FC_FREQ_STEP      100   // Frequency step size (100 MHz)

// DFI 5.0 Training Mode Definitions
typedef enum logic [3:0] {
    DFI_TRAIN_NONE       = 4'h0,  // No training active
    DFI_TRAIN_WRLVL      = 4'h1,  // Write leveling
    DFI_TRAIN_GATE       = 4'h2,  // Gate training
    DFI_TRAIN_RDLVL      = 4'h3,  // Read leveling
    DFI_TRAIN_WEDGE      = 4'h4,  // Write eye centering
    DFI_TRAIN_REDD       = 4'h5,  // Read data eye deskew
    DFI_TRAIN_WRREYE     = 4'h6,  // Write/read data eye
    DFI_TRAIN_ADDR_CMD    = 4'h7,  // Address/command training
    DFI_TRAIN_MPR        = 4'h8,  // MPR pattern training
    DFI_TRAIN_RDDQS      = 4'h9,  // Read DQS training
    DFI_TRAIN_WR_DQ      = 4'hA,  // Write DQ training
    DFI_TRAIN_RD_DQ      = 4'hB   // Read DQ training
} dfi_training_mode_t;

// DFI 5.0 Calibration Status Codes
typedef enum logic [1:0] {
    DFI_CAL_NOT_STARTED = 2'b00,  // Calibration not started
    DFI_CAL_IN_PROGRESS = 2'b01,  // Calibration in progress
    DFI_CAL_COMPLETE    = 2'b10,  // Calibration complete
    DFI_CAL_FAILED      = 2'b11   // Calibration failed
} dfi_cal_status_t;

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


