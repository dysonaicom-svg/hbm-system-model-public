# =============================================================================
# HBM Controller RTL Makefile for Verilator
# =============================================================================
# Targets:
#   make lint   - Lint-only check without compilation
#   make sim    - Build and run simulation
#   make clean  - Remove generated files
#   make help   - Display this help
# =============================================================================

# Directory structure
RTL_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
RTL_DIR := $(patsubst %/,%,$(RTL_DIR))
OBJ_DIR := $(RTL_DIR)/obj_dir
LOG_DIR := $(RTL_DIR)/logs

# Verilator configuration
VERILATOR := verilator
VFLAGS := --lint-only -Wall -Wno-fatal

# Top module and testbench
TOP_MODULE ?= hbm_controller_tb
RTL_TOP := hbm_controller

# Source files (SystemVerilog)
RTL_SOURCES := \
	$(RTL_DIR)/hbm_types.svh \
	$(RTL_DIR)/hbm_controller.sv \
	$(RTL_DIR)/dram_model.sv

TB_SOURCE := $(RTL_DIR)/hbm_controller_tb.sv
TB_MAIN := $(RTL_DIR)/hbm_controller_tb_main.cpp

# File list for lint (all RTL modules)
FILELIST := $(RTL_DIR)/filelist.f

# File list for lint-only (excludes testbench, specifies top module)
FILELIST_LINT := $(RTL_DIR)/filelist_lint.f

# Build flags
CXX := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -O2
LDFLAGS := -lpthread

# Verilator build flags
VBUILD_CC := --cc --exe --build
VBUILD_CXXFLAGS := -CFLAGS "-std=c++17 -O2 -Wall"
VBUILD_LDFLAGS := -LDFLAGS "-lpthread"

# Simulation parameters
SIM_TIME ?= 10us
WAVEFORM ?= yes

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

# =============================================================================
# Target: help
# =============================================================================
.PHONY: help
help:
	@echo ""
	@echo "$(GREEN)HBM Controller RTL Makefile$(NC)"
	@echo "=============================="
	@echo ""
	@echo "Targets:"
	@echo "  $(YELLOW)make lint$(NC)   - Lint-only check (fast, no compilation)"
	@echo "  $(YELLOW)make sim$(NC)   - Build and run simulation"
	@echo "  $(YELLOW)make clean$(NC) - Remove generated files"
	@echo "  $(YELLOW)make help$(NC)  - Display this help"
	@echo ""
	@echo "Variables:"
	@echo "  SIM_TIME=50us  Set simulation time"
	@echo "  TOP_MODULE=   Set top module (default: hbm_controller_tb)"
	@echo ""
	@echo "Examples:"
	@echo "  make lint SIM_TIME=50us"
	@echo "  make sim TOP_MODULE=hbm_controller"
	@echo ""

# =============================================================================
# Target: lint
# =============================================================================
.PHONY: lint
lint: $(FILELIST)
	@echo "$(GREEN)== Running Verilator Lint Check ==$(NC)"
	@mkdir -p $(LOG_DIR)
	cd $(RTL_DIR) && $(VERILATOR) $(VFLAGS) -f $(FILELIST) --top-module $(RTL_TOP) 2>&1 | tee $(LOG_DIR)/lint.log
	@echo ""
	@echo "$(GREEN)== Lint Check Complete ==$(NC)"
	@echo "Log file: $(LOG_DIR)/lint.log"

# =============================================================================
# Target: sim (build and run)
# =============================================================================
.PHONY: sim
sim: $(OBJ_DIR)/V$(TOP_MODULE)
	@echo "$(GREEN)== Running Simulation ==$(NC)"
	$(OBJ_DIR)/Vhbm_controller_tb +TIME=$(SIM_TIME) 2>&1 | tee $(LOG_DIR)/sim.log

$(OBJ_DIR)/V$(TOP_MODULE): $(RTL_SOURCES) $(TB_SOURCE) $(TB_MAIN) $(FILELIST)
	@echo "$(GREEN)== Building with Verilator ==$(NC)"
	@mkdir -p $(OBJ_DIR) $(LOG_DIR)
	cd $(RTL_DIR) && $(VERILATOR) \
		--cc \
		--exe \
		--build \
		--sv \
		--no-timing \
		--trace \
		-Wno-fatal \
		--top-module $(TOP_MODULE) \
		-f $(FILELIST) \
		$(TB_SOURCE) \
		$(TB_MAIN) \
		--Mdir $(OBJ_DIR) \
		-CFLAGS "-std=c++17 -O2 -Wno-unused-but-set-variable" \
		-LDFLAGS "-lpthread" \
		2>&1 | tee $(LOG_DIR)/build.log
	@echo ""
	@echo "$(GREEN)== Build Complete ==$(NC)"
	@echo "Binary: $(OBJ_DIR)/V$(TOP_MODULE)"
	@echo ""
	@echo "To run: cd $(OBJ_DIR) && ./V$(TOP_MODULE)"
	@echo "To view waveforms: open $(OBJ_DIR)/V$(TOP_MODULE).vcd with gtkwave"

# =============================================================================
# Target: sim-debug (build with waveform generation)
# =============================================================================
.PHONY: sim-debug
sim-debug:
	$(MAKE) clean
	@echo "$(GREEN)== Building with Waveform Support ==$(NC)"
	@mkdir -p $(OBJ_DIR) $(LOG_DIR)
	cd $(RTL_DIR) && $(VERILATOR) \
		--cc \
		--exe \
		--build \
		--sv \
		--trace \
		--top-module $(TOP_MODULE) \
		-f $(FILELIST) \
		$(TB_SOURCE) \
		--Mdir $(OBJ_DIR) \
		-CFLAGS "-std=c++17 -O2" \
		-LDFLAGS "-lpthread" \
		2>&1 | tee $(LOG_DIR)/build-debug.log

	@echo ""
	@echo "$(GREEN)== Running with Waveform Tracing ==$(NC)"
	cd $(OBJ_DIR) && ./V$(TOP_MODULE) +TIME=$(SIM_TIME) 2>&1 | tee $(LOG_DIR)/sim-debug.log
	@echo ""
	@echo "Waveform file: $(OBJ_DIR)/V$(TOP_MODULE).vcd"
	@echo "View with: gtkwave $(OBJ_DIR)/V$(TOP_MODULE).vcd"

# =============================================================================
# Target: clean
# =============================================================================
.PHONY: clean
clean:
	@echo "$(YELLOW)== Cleaning Generated Files ==$(NC)"
	@rm -rf $(OBJ_DIR)
	@rm -rf $(LOG_DIR)
	@rm -f $(RTL_DIR)/*_all.list
	@echo "$(GREEN)== Clean Complete ==$(NC)"

# =============================================================================
# Target: clean-all (also removes verdicts.db if present)
# =============================================================================
.PHONY: clean-all
clean-all: clean
	@rm -f $(RTL_DIR)/verdicts.db

# =============================================================================
# Target: check - Verify toolchain is available
# =============================================================================
.PHONY: check
check:
	@echo "Checking toolchain..."
	@echo ""
	@echo "Verilator:"
	@if command -v $(VERILATOR) &> /dev/null; then \
		$(VERILATOR) --version 2>&1 | head -1; \
		echo "  Status: $(GREEN)FOUND$(NC)"; \
	else \
		echo "  Status: $(RED)NOT FOUND$(NC)"; \
		echo "  Install: apt install verilator"; \
	fi
	@echo ""
	@echo "GCC:"
	@if command -v $(CXX) &> /dev/null; then \
		$(CXX) --version 2>&1 | head -1; \
		echo "  Status: $(GREEN)FOUND$(NC)"; \
	else \
		echo "  Status: $(RED)NOT FOUND$(NC)"; \
		echo "  Install: apt install g++"; \
	fi
	@echo ""

# =============================================================================
# Default target
# =============================================================================
.DEFAULT_GOAL := help