// ------------------------------------------------------------
// uvm_macros.svh - Simplified UVM macros for Verilator
// ------------------------------------------------------------

// =============================================================
// Stringification
// =============================================================
`define UVM_STRINGIFY(x) `"x`"
`define UVM_TOSTRING(x) `"x`"

`define UVM_FILE __FILE__
`define UVM_LINE __LINE__

// =============================================================
// Phase Macros
// =============================================================
`define uvm_phase_utils(TYPE)
`define uvm_update_sequence_lib
`define uvm_phase_callback(TYPE,PHASE)

// =============================================================
// Component Registration Macros (empty for stub)
// =============================================================
`define uvm_component_utils(TYPE)
`define uvm_component_param_utils(TYPE)

// =============================================================
// Object Registration Macros (empty for stub)
// =============================================================
`define uvm_object_utils(TYPE)
`define uvm_object_param_utils(TYPE)

// =============================================================
// Sequence Registration Macros (empty for stub)
// =============================================================
`define uvm_sequence_utils(TYPE)
`define uvm_declare_p_sequencer(PROXY_P_SEQUENCER)
`define uvm_add_p_sequencer(SEQUENCER, P_SEQUENCER)

// =============================================================
// Field Operation Macros (empty for stub)
// =============================================================
`define uvm_field_utils(TYPE)
`define uvm_field_int(ARG, FLAG)
`define uvm_field_string(ARG, FLAG)
`define uvm_field_object(ARG, FLAG)
`define uvm_field_array_int(ARG, FLAG)
`define uvm_field_array_object(ARG, FLAG)
`define uvm_field_aa_int_string(ARG, FLAG)
`define uvm_field_aa_int_int(ARG, FLAG)

// =============================================================
// Message Macros
// =============================================================
`define uvm_info(ID, MSG, VERBOSITY) \
    $display("[INFO] %s: %s", ID, MSG);

`define uvm_warning(ID, MSG) \
    $display("[WARN] %s: %s", ID, MSG);

`define uvm_error(ID, MSG) \
    $display("[ERROR] %s: %s", ID, MSG);

`define uvm_fatal(ID, MSG) \
    $display("[FATAL] %s: %s", ID, MSG); $finish;

// =============================================================
// Sequence Item Macros (empty for stub)
// =============================================================
`define uvm_create(ITEM)
`define uvm_send(ITEM)
`define uvm_rand_send(ITEM)
`define uvm_do(ITEM)
`define uvm_do_with_priority(ITEM, PRIORITY)
`define uvm_send_with_priority(ITEM, PRIORITY)
`define uvm_do_callbacks(T, CB, METHOD)
`define uvm_do_obj_callbacks(T, CB, METHOD)

// =============================================================
// Config Database Macros (empty for stub)
// =============================================================
`define uvm_config_db_set(C, INST, FIELD, VALUE)
`define uvm_config_db_get(C, INST, FIELD, VALUE)

// =============================================================
// Register Model Macros (empty for stub)
// =============================================================
`define uvm_reg_register(TYPE, NAME)
`define uvm_reg_field(NAME, SIZE, POS)
`define uvm_reg_bit(NAME, POS)

// =============================================================
// Coverage Macros (empty for stub)
// =============================================================
`define uvm_component_member_coverage(TYPE, COV)
`define uvm_member_coverage(TYPE, COV)

// =============================================================
// Task/Function Wrapper Macros (empty for stub)
// =============================================================
`define uvm_task_member(NAME, ARGS)
`define uvm_func_member(NAME, ARGS)

// =============================================================
// Verbosity Settings (empty for stub)
// =============================================================
`define uvm_verbosity_settings

// =============================================================
// Objection Macros (empty for stub)
// =============================================================
`define uvm_raise_objection(OBJ, DESC)
`define uvm_drop_objection(OBJ, DESC)

// =============================================================
// Sequence Macros (empty for stub)
// =============================================================
`define uvm_sequence_start(PREFIX, SEQ, SEQR)
`define uvm_sequence_item_begin(SEQ, SEQR, ITEM, PRIORITY)
`define uvm_sequence_item_end(SEQ, SEQR, ITEM)

// =============================================================
// Barrier/Event Macros (empty for stub)
// =============================================================
`define uvm_barrier_wait(BARRIER)
`define uvm_barrier_reset(BARRIER)
`define uvm_event_trigger(EVENT)
`define uvm_event_wait(EVENT)
`define uvm_event_wait_cancel(EVENT)