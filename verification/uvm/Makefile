# ------------------------------------------------------------
# Makefile for HBM UVM Verification
# ------------------------------------------------------------

# UVM_HOME - Path to UVM library
UVM_HOME ?= /usr/share/verilator/uvm
# Alternative locations to search
ifeq ($(wildcard $(UVM_HOME)/src/uvm.svh),)
    UVM_HOME := $(shell find /usr -name "uvm.svh" 2>/dev/null | head -1 | xargs dirname 2>/dev/null | xargs dirname 2>/dev/null)
endif
ifeq ($(wildcard $(UVM_HOME)/src/uvm.svh),)
    UVM_HOME := $(UVM_HOME)/..
endif

# Simulator settings
SIM ?= verilator
SIM_OPTS := --cc --exe --build
UVM_OPTS := +incdir+$(UVM_HOME)/src

# Source files
UVM_PKG := $(UVM_HOME)/src/uvm.svh
TB_TOP := hbm_tb.sv
ENV_PKG := hbm_env_pkg.sv
TEST_PKG := hbm_test_pkg.sv

# File list
UVM_F := uvm.f
UVM_F_CONTENTS := \
    $(UVM_PKG) \
    $(ENV_PKG) \
    $(TEST_PKG) \
    $(TB_TOP)

# Output
TOP_MODULE := hbm_tb
BUILD_DIR := build
EXEC := $(BUILD_DIR)/V$(TOP_MODULE)

# Test selection
TEST ?= hbm_random_test
RUN_OPTS := --trace

# ------------------------------------------------------------
# Compilation Rules
# ------------------------------------------------------------

.PHONY: all compile run clean help

all: compile run

compile: $(UVM_F)
	@echo "=== Compiling with $(SIM) ==="
	@mkdir -p $(BUILD_DIR)
	verilator \
		$(SIM_OPTS) \
		$(UVM_OPTS) \
		-f $(UVM_F) \
		--top-module $(TOP_MODULE) \
		-CFLAGS "-DUVM_REGEX_NONE" \
		$(foreach dir,$(INCDIR),-I$(dir))
	@echo "=== Compilation complete ==="

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

# ------------------------------------------------------------
# Run Simulation
# ------------------------------------------------------------

run: compile
	@echo "=== Running test: $(TEST) ==="
	@cd $(BUILD_DIR) && ./$(EXEC) $(RUN_OPTS) +UVM_TEST_NAME=$(TEST)

run_single:
	@echo "=== Running single read test ==="
	@cd $(BUILD_DIR) && ./$(EXEC) $(RUN_OPTS) +UVM_TEST_NAME=hbm_single_read_test

run_hotspot:
	@echo "=== Running hotspot test ==="
	@cd $(BUILD_DIR) && ./$(EXEC) $(RUN_OPTS) +UVM_TEST_NAME=hbm_hotspot_test

run_random:
	@echo "=== Running random traffic test ==="
	@cd $(BUILD_DIR) && ./$(EXEC) $(RUN_OPTS) +UVM_TEST_NAME=hbm_random_test

# ------------------------------------------------------------
# Clean Target
# ------------------------------------------------------------

clean:
	@echo "=== Cleaning build directory ==="
	@rm -rf $(BUILD_DIR)
	@rm -f *.log *.vcd *.fst *.out

.PHONY: clean-all
clean-all: clean
	@rm -f *.log *.vcd

# ------------------------------------------------------------
# Help
# ------------------------------------------------------------

help:
	@echo "HBM UVM Verification Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Compile and run default test"
	@echo "  compile      - Compile sources only"
	@echo "  run          - Run simulation with TEST (default: random)"
	@echo "  run_single   - Run single read test"
	@echo "  run_hotspot  - Run hotspot test"
	@echo "  run_random   - Run random traffic test"
	@echo "  clean        - Clean build directory"
	@echo "  clean-all    - Clean all generated files"
	@echo "  help         - Show this help"
	@echo ""
	@echo "Variables:"
	@echo "  UVM_HOME=$(UVM_HOME)"
	@echo "  SIM=$(SIM)"
	@echo "  TEST=$(TEST)"