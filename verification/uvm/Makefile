# ------------------------------------------------------------
# Makefile for HBM UVM Verification
# ------------------------------------------------------------

# UVM_HOME - Path to UVM library
# Use local stub for syntax checking if system UVM not available
UVM_HOME ?= ./uvm_stub
# Alternative locations to search
ifeq ($(wildcard $(UVM_HOME)/src/uvm.svh),)
    UVM_HOME := $(shell find /usr -name "uvm.svh" 2>/dev/null | head -1 | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null)
endif
ifeq ($(wildcard $(UVM_HOME)/src/uvm.svh),)
    UVM_HOME := $(UVM_HOME)/..
endif

# RTL sources for reference model
RTL_DIR := $(shell cd ../.. && pwd)/rtl
REF_MODEL_DIR := ../reference_model

# Simulator settings
SIM ?= verilator
SIM_OPTS := --cc --exe --build
UVM_OPTS := +incdir+$(UVM_HOME)/src
COV_OPTS := --coverage --coverage-line --coverage-func --coverage-toggle
TRACE_OPTS := --trace --trace-structs --trace-depth 999

# Source files
UVM_PKG := $(UVM_HOME)/src/uvm.svh
TB_TOP := hbm_tb.sv
ENV_PKG := hbm_env_pkg.sv
TEST_PKG := hbm_test_pkg.sv

# Reference model files
REF_MODELS := \
    $(REF_MODEL_DIR)/dram_ref_model.sv \
    $(REF_MODEL_DIR)/timing_checker.sv \
    $(REF_MODEL_DIR)/bandwidth_calc.sv \
    $(REF_MODEL_DIR)/addr_decoder_ref.sv

# RTL files (if available)
RTL_FILES := $(wildcard $(RTL_DIR)/*.sv) $(wildcard $(RTL_DIR)/*.svh)

# File list
UVM_F := uvm.f
UVM_F_CONTENTS := \
    $(UVM_PKG) \
    $(ENV_PKG) \
    $(TEST_PKG) \
    $(TB_TOP) \
    $(REF_MODELS)

# Output
TOP_MODULE := hbm_tb
BUILD_DIR := build
EXEC := $(BUILD_DIR)/V$(TOP_MODULE)

# Coverage output
COV_DIR := coverage
COV_DB := $(COV_DIR)/simdata.db

# Test selection
TEST ?= hbm_random_test
RUN_OPTS := --trace
WAVEFORM ?= dump.vcd

# Verbosity level
UVM_VERBOSITY ?= UVM_MEDIUM

# ------------------------------------------------------------
# Compilation Rules
# ------------------------------------------------------------

.PHONY: all compile run clean help

all: compile run

# Default compilation with Verilator
compile: $(UVM_F)
	@echo "=== Compiling with $(SIM) ==="
	@mkdir -p $(BUILD_DIR)
	verilator \
		$(SIM_OPTS) \
		$(UVM_OPTS) \
		$(COV_OPTS) \
		$(TRACE_OPTS) \
		-f $(UVM_F) \
		--top-module $(TOP_MODULE) \
		-CFLAGS "-DUVM_REGEX_NONE -g" \
		--Mdir $(BUILD_DIR) \
		$(foreach dir,$(INCDIR),-I$(dir))
	@echo "=== Compilation complete ==="

# Quick compilation without coverage
compile-quick: $(UVM_F)
	@echo "=== Quick compile (no coverage) ==="
	@mkdir -p $(BUILD_DIR)
	verilator \
		--cc --exe --build \
		$(UVM_OPTS) \
		$(TRACE_OPTS) \
		-f $(UVM_F) \
		--top-module $(TOP_MODULE) \
		-CFLAGS "-DUVM_REGEX_NONE" \
		--Mdir $(BUILD_DIR) \
		$(foreach dir,$(INCDIR),-I$(dir))
	@echo "=== Quick compilation complete ==="

# Compilation with RTL controller
compile-rtl: $(UVM_F)
	@echo "=== Compiling with RTL controller ==="
	@mkdir -p $(BUILD_DIR)
	verilator \
		$(SIM_OPTS) \
		$(UVM_OPTS) \
		$(COV_OPTS) \
		$(TRACE_OPTS) \
		$(if $(RTL_FILES),-y $(RTL_DIR) -y $(RTL_DIR)/include,) \
		-f $(UVM_F) \
		--top-module $(TOP_MODULE) \
		-CFLAGS "-DUVM_REGEX_NONE -DUSE_RTL_CONTROLLER" \
		--Mdir $(BUILD_DIR) \
		$(foreach dir,$(INCDIR),-I$(dir))
	@echo "=== RTL compilation complete ==="

# Alternative: single-file compilation with xrun
xrun-compile:
	@echo "=== Compiling with Cadence Xcelium ==="
	@(cd $(BUILD_DIR) && xrun \
		-f ../$(UVM_F) \
		-uvm \
		-R \
		-seed random \
		-access +rwc \
		-input uvm_run)

# Alternative: Questa compilation
questa-compile:
	@echo "=== Compiling with Questa ==="
	vlog \
		-f $(UVM_F) \
		-uvm \
		-suppress 2005 \
		-coverage \
		-o $(BUILD_DIR)/work

# ------------------------------------------------------------
# Run Simulation
# ------------------------------------------------------------

run: compile
	@echo "=== Running test: $(TEST) ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=$(TEST) \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM) \
		$(RUN_OPTS)

# Run with specific test
run-test: compile
	@echo "=== Running test: $(TEST) ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=$(TEST) \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM) \
		$(RUN_OPTS)

# Run single read test
run_single:
	@echo "=== Running single read test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_single_read_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run single write test
run_write:
	@echo "=== Running single write test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_single_write_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run write-read test
run_write_read:
	@echo "=== Running write-read test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_write_read_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run hotspot test
run_hotspot:
	@echo "=== Running hotspot test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_hotspot_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run random traffic test
run_random:
	@echo "=== Running random traffic test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_random_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run bank stress test
run_bank_stress:
	@echo "=== Running bank stress test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_bank_stress_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run row hammer test
run_row_hammer:
	@echo "=== Running row hammer test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_row_hammer_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run AXI4 test
run_axi4:
	@echo "=== Running AXI4 test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_axi4_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run comprehensive test
run_comprehensive:
	@echo "=== Running comprehensive test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_comprehensive_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# ================================================================
# QoS Priority Tests
# ================================================================

# Run QoS priority test
run_qos_priority:
	@echo "=== Running QoS priority test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_qos_priority_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run QoS starvation prevention test
run_qos_starvation:
	@echo "=== Running QoS starvation prevention test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_qos_starvation_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run QoS deadline test
run_qos_deadline:
	@echo "=== Running QoS deadline test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_qos_deadline_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run QoS mixed traffic test
run_qos_mixed:
	@echo "=== Running QoS mixed traffic test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_qos_mixed_traffic_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# ================================================================
# Refresh Conflict Tests
# ================================================================

# Run refresh conflict test
run_refresh_conflict:
	@echo "=== Running refresh conflict test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_refresh_conflict_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run refresh timing test
run_refresh_timing:
	@echo "=== Running refresh timing test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_refresh_timing_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run per-bank refresh test
run_per_bank_refresh:
	@echo "=== Running per-bank refresh test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_per_bank_refresh_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run refresh during active test
run_refresh_during_active:
	@echo "=== Running refresh during active test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_refresh_during_active_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run auto-refresh test
run_auto_refresh:
	@echo "=== Running auto-refresh test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_auto_refresh_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# ================================================================
# Multi-Channel Interleaving Tests
# ================================================================

# Run multi-channel interleaving test
run_multi_channel_interleave:
	@echo "=== Running multi-channel interleaving test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_multi_channel_interleave_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run channel conflict test
run_channel_conflict:
	@echo "=== Running channel conflict test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_channel_conflict_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# ================================================================
# Bank Contention Tests
# ================================================================

# Run bank group conflict test
run_bank_group_conflict:
	@echo "=== Running bank group conflict test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_bank_group_conflict_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run bank activation conflict test
run_bank_activation_conflict:
	@echo "=== Running bank activation conflict test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_bank_activation_conflict_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run bank round-robin test
run_bank_round_robin:
	@echo "=== Running bank round-robin test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_bank_round_robin_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run bank open/close test
run_bank_open_close:
	@echo "=== Running bank open/close test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_bank_open_close_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run cross-bank scheduling test
run_cross_bank_scheduling:
	@echo "=== Running cross-bank scheduling test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_cross_bank_scheduling_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run bank contention stress test
run_bank_contention_stress:
	@echo "=== Running bank contention stress test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_bank_contention_stress_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# ================================================================
# Boundary Condition Tests
# ================================================================

# Run max address test
run_max_address:
	@echo "=== Running max address test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_max_address_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run min address test
run_min_address:
	@echo "=== Running min address test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_min_address_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run address overflow test
run_address_overflow:
	@echo "=== Running address overflow test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_address_overflow_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run queue full test
run_queue_full:
	@echo "=== Running queue full test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_queue_full_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run queue empty test
run_queue_empty:
	@echo "=== Running queue empty test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_queue_empty_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run burst boundary test
run_burst_boundary:
	@echo "=== Running burst boundary test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_burst_boundary_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run timing boundary test
run_timing_boundary:
	@echo "=== Running timing boundary test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_timing_boundary_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# Run data pattern boundary test
run_data_pattern_boundary:
	@echo "=== Running data pattern boundary test ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) \
		+UVM_TEST_NAME=hbm_data_pattern_boundary_test \
		+UVM_VERBOSITY=$(UVM_VERBOSITY) \
		+DUMP_VCD=$(WAVEFORM)

# ================================================================
# Test Suite Targets
# ================================================================

# Run all QoS tests
test-qos: compile
	@echo "=== Running all QoS tests ==="
	@$(MAKE) run_qos_priority
	@$(MAKE) run_qos_starvation
	@$(MAKE) run_qos_deadline
	@$(MAKE) run_qos_mixed
	@echo "=== QoS tests complete ==="

# Run all refresh tests
test-refresh: compile
	@echo "=== Running all refresh tests ==="
	@$(MAKE) run_refresh_conflict
	@$(MAKE) run_refresh_timing
	@$(MAKE) run_per_bank_refresh
	@$(MAKE) run_refresh_during_active
	@$(MAKE) run_auto_refresh
	@echo "=== Refresh tests complete ==="

# Run all bank contention tests
test-bank: compile
	@echo "=== Running all bank contention tests ==="
	@$(MAKE) run_bank_group_conflict
	@$(MAKE) run_bank_activation_conflict
	@$(MAKE) run_bank_round_robin
	@$(MAKE) run_bank_open_close
	@$(MAKE) run_cross_bank_scheduling
	@$(MAKE) run_bank_contention_stress
	@echo "=== Bank contention tests complete ==="

# Run all boundary tests
test-boundary: compile
	@echo "=== Running all boundary tests ==="
	@$(MAKE) run_max_address
	@$(MAKE) run_min_address
	@$(MAKE) run_address_overflow
	@$(MAKE) run_queue_full
	@$(MAKE) run_queue_empty
	@$(MAKE) run_burst_boundary
	@$(MAKE) run_timing_boundary
	@$(MAKE) run_data_pattern_boundary
	@echo "=== Boundary tests complete ==="

# Run all multi-channel tests
test-multi-channel: compile
	@echo "=== Running all multi-channel tests ==="
	@$(MAKE) run_multi_channel_interleave
	@$(MAKE) run_channel_conflict
	@echo "=== Multi-channel tests complete ==="

# Run all new tests
test-new: compile
	@echo "=== Running all new tests ==="
	@$(MAKE) test-qos
	@$(MAKE) test-refresh
	@$(MAKE) test-bank
	@$(MAKE) test-boundary
	@$(MAKE) test-multi-channel
	@echo "=== All new tests complete ==="

# Run all tests (comprehensive)
test-all-full: compile
	@echo "=== Running all tests (comprehensive) ==="
	@$(MAKE) run_single
	@$(MAKE) run_write
	@$(MAKE) run_write_read
	@$(MAKE) run_hotspot
	@$(MAKE) run_random
	@$(MAKE) run_bank_stress
	@$(MAKE) test-qos
	@$(MAKE) test-refresh
	@$(MAKE) test-bank
	@$(MAKE) test-boundary
	@$(MAKE) test-multi-channel
	@$(MAKE) run_comprehensive
	@echo "=== All tests complete ==="

# ------------------------------------------------------------
# Coverage
# ------------------------------------------------------------

.PHONY: coverage

coverage: compile
	@echo "=== Generating coverage report ==="
	@mkdir -p $(COV_DIR)
	verilator_coverage \
		--annotate $(COV_DIR) \
		$(wildcard $(BUILD_DIR)/coverage.dat)
	@echo "=== Coverage report generated in $(COV_DIR) ==="

# ------------------------------------------------------------
# Clean Targets
# ------------------------------------------------------------

clean:
	@echo "=== Cleaning build directory ==="
	@rm -rf $(BUILD_DIR)
	@rm -f *.log *.vcd *.fst *.out *.dat

.PHONY: clean-all
clean-all: clean
	@rm -rf $(COV_DIR)
	@rm -f *.log *.vcd

# Clean everything including generated files
clean-full:
	@echo "=== Full clean ==="
	@rm -rf $(BUILD_DIR) $(COV_DIR)
	@rm -f *.log *.vcd *.fst *.out *.dat
	@find . -name "*.v" -newer Makefile -delete 2>/dev/null || true

# ------------------------------------------------------------
# Help
# ------------------------------------------------------------

help:
	@echo "HBM UVM Verification Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all              - Compile and run default test"
	@echo "  compile          - Compile sources only"
	@echo "  compile-quick    - Quick compile without coverage"
	@echo "  compile-rtl      - Compile with RTL controller"
	@echo "  run              - Run simulation (default: random)"
	@echo "  run-test         - Run simulation with TEST variable"
	@echo ""
	@echo "  -- Basic Tests --"
	@echo "  run_single       - Run single read test"
	@echo "  run_write        - Run single write test"
	@echo "  run_write_read   - Run write-read test"
	@echo "  run_hotspot      - Run hotspot test"
	@echo "  run_random       - Run random traffic test"
	@echo "  run_bank_stress  - Run bank stress test"
	@echo "  run_comprehensive- Run comprehensive test"
	@echo ""
	@echo "  -- QoS Priority Tests --"
	@echo "  run_qos_priority     - Run QoS priority test"
	@echo "  run_qos_starvation   - Run QoS starvation prevention test"
	@echo "  run_qos_deadline     - Run QoS deadline test"
	@echo "  run_qos_mixed        - Run QoS mixed traffic test"
	@echo ""
	@echo "  -- Refresh Tests --"
	@echo "  run_refresh_conflict       - Run refresh conflict test"
	@echo "  run_refresh_timing         - Run refresh timing test"
	@echo "  run_per_bank_refresh       - Run per-bank refresh test"
	@echo "  run_refresh_during_active  - Run refresh during active test"
	@echo "  run_auto_refresh          - Run auto-refresh test"
	@echo ""
	@echo "  -- Bank Contention Tests --"
	@echo "  run_bank_group_conflict      - Run bank group conflict test"
	@echo "  run_bank_activation_conflict - Run bank activation conflict test"
	@echo "  run_bank_round_robin         - Run bank round-robin test"
	@echo "  run_bank_open_close           - Run bank open/close test"
	@echo "  run_cross_bank_scheduling      - Run cross-bank scheduling test"
	@echo "  run_bank_contention_stress    - Run bank contention stress test"
	@echo ""
	@echo "  -- Multi-Channel Tests --"
	@echo "  run_multi_channel_interleave - Run multi-channel interleaving test"
	@echo "  run_channel_conflict          - Run channel conflict test"
	@echo ""
	@echo "  -- Boundary Tests --"
	@echo "  run_max_address           - Run max address test"
	@echo "  run_min_address           - Run min address test"
	@echo "  run_address_overflow      - Run address overflow test"
	@echo "  run_queue_full            - Run queue full test"
	@echo "  run_queue_empty           - Run queue empty test"
	@echo "  run_burst_boundary        - Run burst boundary test"
	@echo "  run_timing_boundary       - Run timing boundary test"
	@echo "  run_data_pattern_boundary - Run data pattern boundary test"
	@echo ""
	@echo "  -- Test Suites --"
	@echo "  test-qos          - Run all QoS tests"
	@echo "  test-refresh      - Run all refresh tests"
	@echo "  test-bank         - Run all bank contention tests"
	@echo "  test-multi-channel - Run all multi-channel tests"
	@echo "  test-boundary     - Run all boundary tests"
	@echo "  test-new          - Run all new tests"
	@echo "  test-all-full     - Run all tests (comprehensive)"
	@echo "  coverage          - Generate coverage report"
	@echo "  clean             - Clean build directory"
	@echo "  clean-all         - Clean all generated files"
	@echo "  clean-full        - Full clean including generated RTL"
	@echo "  help              - Show this help"
	@echo ""
	@echo "Variables:"
	@echo "  UVM_HOME=$(UVM_HOME)"
	@echo "  SIM=$(SIM)"
	@echo "  TEST=$(TEST)"
	@echo "  UVM_VERBOSITY=$(UVM_VERBOSITY)"
	@echo "  WAVEFORM=$(WAVEFORM)"
	@echo ""
	@echo "Examples:"
	@echo "  make compile TEST=hbm_single_read_test"
	@echo "  make run TEST=hbm_hotspot_test UVM_VERBOSITY=UVM_HIGH"
	@echo "  make clean && make all"

# ------------------------------------------------------------
# Test Targets
# ------------------------------------------------------------

test-single:
	@$(MAKE) run_single

test-write:
	@$(MAKE) run_write

test-write-read:
	@$(MAKE) run_write_read

test-hotspot:
	@$(MAKE) run_hotspot

test-random:
	@$(MAKE) run_random

test-bank-stress:
	@$(MAKE) run_bank_stress

test-row-hammer:
	@$(MAKE) run_row_hammer

test-axi4:
	@$(MAKE) run_axi4

test-comprehensive:
	@$(MAKE) run_comprehensive

# Run all tests sequentially
test-all: compile
	@echo "=== Running all tests ==="
	@$(MAKE) run_single
	@$(MAKE) run_write
	@$(MAKE) run_write_read
	@$(MAKE) run_hotspot
	@$(MAKE) run_random
	@$(MAKE) run_bank_stress
	@$(MAKE) run_comprehensive
	@echo "=== All tests complete ==="

# Run all tests in parallel (faster for CI)
test-all-parallel: compile
	@echo "=== Running all tests in parallel ==="
	@mkdir -p $(COV_DIR)
	@cd $(BUILD_DIR) && ./$(EXEC) +UVM_TEST_NAME=hbm_single_read_test +UVM_VERBOSITY=$(UVM_VERBOSITY) & \
	@cd $(BUILD_DIR) && ./$(EXEC) +UVM_TEST_NAME=hbm_single_write_test +UVM_VERBOSITY=$(UVM_VERBOSITY) & \
	@cd $(BUILD_DIR) && ./$(EXEC) +UVM_TEST_NAME=hbm_hotspot_test +UVM_VERBOSITY=$(UVM_VERBOSITY) & \
	@cd $(BUILD_DIR) && ./$(EXEC) +UVM_TEST_NAME=hbm_random_test +UVM_VERBOSITY=$(UVM_VERBOSITY) & \
	@wait
	@echo "=== All tests complete ==="

# ------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------

.PHONY: deps
deps:
	@echo "=== Checking dependencies ==="
	@which verilator > /dev/null && echo "Verilator: found" || echo "Verilator: NOT FOUND"
	@which xrun > /dev/null && echo "Xcelium: found" || echo "Xcelium: NOT FOUND"
	@which vlog > /dev/null && echo "Questa: found" || echo "Questa: NOT FOUND"
	@ls -la $(UVM_HOME)/src/uvm.svh 2>/dev/null && echo "UVM: found" || echo "UVM: NOT FOUND"