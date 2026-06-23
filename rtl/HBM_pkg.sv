// =============================================================================
// HBM Package
// =============================================================================
// High Bandwidth Memory UVM verification package
// =============================================================================

`ifndef HBM_PKG_SV
`define HBM_PKG_SV

package hbm_pkg;

// -----------------------------------------------------------------------------
// Imports
// -----------------------------------------------------------------------------
import uvm_pkg::*;

// -----------------------------------------------------------------------------
// Include type definitions
// -----------------------------------------------------------------------------
`include "hbm_types.svh"

// -----------------------------------------------------------------------------
// HBM Configuration Class
// -----------------------------------------------------------------------------
// Note: Constants are defined in hbm_types.svh (NUM_STACKS, NUM_CHANNELS, etc.)
class hbm_configuration extends uvm_object;

    // Configuration fields
    rand int                   num_stacks;
    rand int                   num_channels;
    rand int                   num_bank_groups;
    rand int                   num_banks;
    rand hbm_timing_t          timing;
    rand int                   queue_depth;
    rand bit                   enable_pwr_gating;
    rand bit                   enable_xact_fabric;

    // Default constraints for HBM3
    constraint reasonable_config {
        num_stacks      inside {1, 2, 4, 8};
        num_channels    inside {1, 2, 4, 8};
        num_bank_groups inside {1, 2, 4, 8};
        num_banks       inside {4, 8, 16};
        queue_depth     inside {[4:64]};
        timing.tRCD  inside {[1:16]};
        timing.tRP   inside {[1:16]};
        timing.tRAS  inside {[4:64]};
        timing.tRC   inside {[8:128]};
        timing.tCCD  inside {[1:16]};
        timing.tRRD  inside {[1:16]};
        timing.tFAW  inside {[4:64]};
        timing.tRFC  inside {[16:256]};
        timing.tREFI inside {[100:10000]};
    }

    `uvm_object_utils_begin(hbm_configuration)
        `uvm_field_int(num_stacks,        UVM_DEFAULT)
        `uvm_field_int(num_channels,       UVM_DEFAULT)
        `uvm_field_int(num_bank_groups,    UVM_DEFAULT)
        `uvm_field_int(num_banks,          UVM_DEFAULT)
        `uvm_field_int(queue_depth,        UVM_DEFAULT)
        `uvm_field_int(enable_pwr_gating, UVM_DEFAULT)
        `uvm_field_int(enable_xact_fabric, UVM_DEFAULT)
    `uvm_object_utils_end

    // ---------------------------------------------------------------------------
    // Constructor
    // ---------------------------------------------------------------------------
    function new(string name = "hbm_config");
        super.new(name);
        set_defaults();
    endfunction : new

    // ---------------------------------------------------------------------------
    // Set default configuration values
    // ---------------------------------------------------------------------------
    function void set_defaults();
        num_stacks        = NUM_STACKS;
        num_channels      = NUM_CHANNELS;
        num_bank_groups   = NUM_BANK_GROUPS;
        num_banks         = NUM_BANKS;
        timing            = HBM_TIMING_DEFAULT;
        queue_depth       = 16;
        enable_pwr_gating = 1'b0;
        enable_xact_fabric = 1'b1;
    endfunction : set_defaults

    // ---------------------------------------------------------------------------
    // Calculate total memory size
    // ---------------------------------------------------------------------------
    function automatic int get_total_banks();
        return num_stacks * num_channels * num_bank_groups * num_banks;
    endfunction : get_total_banks

    // ---------------------------------------------------------------------------
    // Print configuration
    // ---------------------------------------------------------------------------
    virtual function void print_config();
        `uvm_info("HBM_CONFIG", $sformatf(
            "HBM Configuration:\n"  &
            "  Stacks:        %0d\n"  &
            "  Channels:      %0d\n"  &
            "  Bank Groups:   %0d\n"  &
            "  Banks:         %0d\n"  &
            "  Total Banks:   %0d\n"  &
            "  Queue Depth:   %0d\n"  &
            "  Power Gating:  %0s\n"  &
            "  Xaction Fabric: %0s\n"  &
            "  Timing:\n"           &
            "    tRCD:  %0d\n"       &
            "    tRP:   %0d\n"       &
            "    tRAS:  %0d\n"       &
            "    tRC:   %0d\n"       &
            "    tCCD:  %0d\n"       &
            "    tRRD:  %0d\n"       &
            "    tFAW:  %0d\n"       &
            "    tRFC:  %0d\n"       &
            "    tREFI: %0d",
            num_stacks, num_channels, num_bank_groups, num_banks,
            get_total_banks(), queue_depth,
            enable_pwr_gating ? "enabled" : "disabled",
            enable_xact_fabric ? "enabled" : "disabled",
            timing.tRCD, timing.tRP, timing.tRAS, timing.tRC,
            timing.tCCD, timing.tRRD, timing.tFAW, timing.tRFC, timing.tREFI
        ), UVM_MEDIUM);
    endfunction : print_config

endclass : hbm_configuration

// -----------------------------------------------------------------------------
// HBM Transaction Class
// -----------------------------------------------------------------------------
class hbm_transaction extends uvm_sequence_item;

    // Transaction fields
    rand hbm_addr_t        addr;
    rand hbm_req_type_t    req_type;
    rand logic [7:0]       length;
    rand logic [7:0]       req_id;
    rand logic             priority;
    rand logic [31:0]      data[];  // Dynamic data array

    // Status fields
    hbm_req_state_t        state;
    bit                    error;
    string                 error_message;

    // Timing tracking
    time                   submitted_time;
    time                   completed_time;

    // ---------------------------------------------------------------------------
    // Constructor
    // ---------------------------------------------------------------------------
    function new(string name = "hbm_transaction");
        super.new(name);
        req_type = REQ_NOP;
        state    = REQ_IDLE;
        error    = 1'b0;
        length   = 8'd4;  // Default burst length 4
        priority = 1'b0;  // Normal priority
    endfunction : new

    // ---------------------------------------------------------------------------
    // UVM automation macros
    // ---------------------------------------------------------------------------
    `uvm_object_utils_begin(hbm_transaction)
        `uvm_field_object(addr,      UVM_DEFAULT)
        `uvm_field_int(addr,         UVM_DEFAULT | UVM_NOPACK)
        `uvm_field_enum(hbm_req_type_t, req_type, UVM_DEFAULT)
        `uvm_field_int(length,       UVM_DEFAULT)
        `uvm_field_int(req_id,       UVM_DEFAULT)
        `uvm_field_int(priority,     UVM_DEFAULT)
        `uvm_field_enum(hbm_req_state_t, state, UVM_DEFAULT)
        `uvm_field_int(error,        UVM_DEFAULT)
        `uvm_field_string(error_message, UVM_DEFAULT)
    `uvm_object_utils_end

    // ---------------------------------------------------------------------------
    // Constraint: Valid request type for read/write
    // ---------------------------------------------------------------------------
    constraint valid_access {
        req_type inside {REQ_READ, REQ_WRITE, REQ_ACT, REQ_PRE, REQ_REF};
    }

    // ---------------------------------------------------------------------------
    // Constraint: Valid burst length
    // ---------------------------------------------------------------------------
    constraint valid_length {
        length inside {4, 8};
    }

    // ---------------------------------------------------------------------------
    // Copy function
    // ---------------------------------------------------------------------------
    function void copy(uvm_object rhs = null);
        hbm_transaction that;
        super.copy(rhs);
        if (rhs != null) begin
            if (!$cast(that, rhs)) begin
                `uvm_fatal("COPY_CAST", "Failed to cast hbm_transaction")
            end
            this.addr          = that.addr;
            this.req_type     = that.req_type;
            this.length       = that.length;
            this.req_id       = that.req_id;
            this.priority     = that.priority;
            this.state        = that.state;
            this.error        = that.error;
            this.error_message = that.error_message;
        end
    endfunction : copy

    // ---------------------------------------------------------------------------
    // Clone function
    // ---------------------------------------------------------------------------
    function uvm_object clone();
        hbm_transaction that;
        that = new();
        that.copy(this);
        return that;
    endfunction : clone

    // ---------------------------------------------------------------------------
    // Compare function
    // ---------------------------------------------------------------------------
    function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        hbm_transaction that;
        do_compare = super.do_compare(rhs, comparer);
        if (!$cast(that, rhs)) begin
            do_compare = 0;
            return do_compare;
        end
        do_compare &= comparer.compare_field("addr", this.addr, that.addr, $bits(addr));
        do_compare &= comparer.compare_field("req_type", this.req_type, that.req_type, $bits(req_type));
        do_compare &= comparer.compare_field("length", this.length, that.length, 8);
        do_compare &= comparer.compare_field("req_id", this.req_id, that.req_id, 8);
        do_compare &= comparer.compare_field("priority", this.priority, that.priority, 1);
        do_compare &= comparer.compare_field("state", this.state, that.state, $bits(state));
        do_compare &= comparer.compare_field("error", this.error, that.error, 1);
    endfunction : do_compare

    // ---------------------------------------------------------------------------
    // Print transaction
    // ---------------------------------------------------------------------------
    function void do_print(uvm_printer printer);
        super.do_print(printer);
        printer.print_generic("addr", "hbm_addr_t", -2, $sformatf(
            "{stack:%0d, ch:%0d, bg:%0d, bk:%0d, row:%0d, col:%0d}",
            addr.stack, addr.channel, addr.bank_group, addr.bank,
            addr.row, addr.col
        ));
        printer.print_string("req_type", req_type.name());
        printer.print_field("length", length, 8);
        printer.print_field("req_id", req_id, 8);
        printer.print_field("priority", priority, 1);
        printer.print_string("state", state.name());
        printer.print_field("error", error, 1);
        if (error && error_message.len() > 0) begin
            printer.print_string("error_message", error_message);
        end
    endfunction : do_print

    // ---------------------------------------------------------------------------
    // Record transaction for debug
    // ---------------------------------------------------------------------------
    function void do_record(uvm_recorder recorder);
        super.do_record(recorder);
        recorder.record_field("addr_stack", addr.stack, 3);
        recorder.record_field("addr_channel", addr.channel, 3);
        recorder.record_field("addr_bank_group", addr.bank_group, 3);
        recorder.record_field("addr_bank", addr.bank, 4);
        recorder.record_field("addr_row", addr.row, 16);
        recorder.record_field("addr_col", addr.col, 10);
        recorder.record_enum("req_type", req_type);
        recorder.record_field("length", length, 8);
        recorder.record_field("req_id", req_id, 8);
        recorder.record_enum("state", state);
    endfunction : do_record

    // ---------------------------------------------------------------------------
    // Pack for bus protocol
    // ---------------------------------------------------------------------------
    function int do_pack(uvm_packer packer);
        int unsigned byte_count = 0;
        super.do_pack(packer);
        packer.pack_field(addr.stack, 3);
        packer.pack_field(addr.channel, 3);
        packer.pack_field(addr.bank_group, 3);
        packer.pack_field(addr.bank, 4);
        packer.pack_field(addr.row, 16);
        packer.pack_field(addr.col, 10);
        packer.pack_enum(req_type);
        packer.pack_field(length, 8);
        packer.pack_field(priority, 1);
        byte_count = (packer.get_packed_size() + 7) / 8;
        return byte_count;
    endfunction : do_pack

    // ---------------------------------------------------------------------------
    // Unpack from bus protocol
    // ---------------------------------------------------------------------------
    function int do_unpack(uvm_packer packer);
        int unsigned byte_count = 0;
        super.do_unpack(packer);
        addr.stack       = packer.unpack_field(3);
        addr.channel     = packer.unpack_field(3);
        addr.bank_group  = packer.unpack_field(3);
        addr.bank        = packer.unpack_field(4);
        addr.row         = packer.unpack_field(16);
        addr.col         = packer.unpack_field(10);
        req_type         = packer.unpack_enum(req_type);
        length           = packer.unpack_field(8);
        priority         = packer.unpack_field(1);
        byte_count = (packer.get_packed_size() + 7) / 8;
        return byte_count;
    endfunction : do_unpack

    // ---------------------------------------------------------------------------
    // Set error
    // ---------------------------------------------------------------------------
    function void set_error(string msg);
        error = 1'b1;
        error_message = msg;
    endfunction : set_error

    // ---------------------------------------------------------------------------
    // Clear error
    // ---------------------------------------------------------------------------
    function void clear_error();
        error = 1'b0;
        error_message = "";
    endfunction : clear_error

    // ---------------------------------------------------------------------------
    // Convert to string for debug
    // ---------------------------------------------------------------------------
    function string convert2string();
        string s;
        s = $sformatf("hbm_transaction[%0d]: ", req_id);
        s = {s, $sformatf("addr={stack:%0d,ch:%0d,bg:%0d,bk:%0d,row:%0d,col:%0d} ",
            addr.stack, addr.channel, addr.bank_group, addr.bank,
            addr.row, addr.col)};
        s = {s, $sformatf("type=%s ", req_type.name())};
        s = {s, $sformatf("len=%0d ", length)};
        s = {s, $sformatf("pri=%0d ", priority)};
        s = {s, $sformatf("state=%s ", state.name())};
        if (error) begin
            s = {s, $sformatf("ERROR: %s", error_message)};
        end
        return s;
    endfunction : convert2string

endclass : hbm_transaction

// -----------------------------------------------------------------------------
// Utility Functions
// -----------------------------------------------------------------------------

// Convert request type to DRAM command
function automatic hbm_cmd_t req_to_cmd(hbm_req_type_t req);
    case (req)
        REQ_ACT:   return CMD_ACT;
        REQ_READ:  return CMD_READ;
        REQ_WRITE: return CMD_WRITE;
        REQ_PRE:   return CMD_PRE;
        REQ_REF:   return CMD_REF;
        default:   return CMD_NOP;
    endcase
endfunction : req_to_cmd

// Check if request type is a read operation
function automatic bit is_read_req(hbm_req_type_t req);
    return (req == REQ_READ);
endfunction : is_read_req

// Check if request type is a write operation
function automatic bit is_write_req(hbm_req_type_t req);
    return (req == REQ_WRITE);
endfunction : is_write_req

// Check if request type requires bank activation
function automatic bit requires_activation(hbm_req_type_t req);
    return (req inside {REQ_READ, REQ_WRITE});
endfunction : requires_activation

endpackage : hbm_pkg

`endif // HBM_PKG_SV