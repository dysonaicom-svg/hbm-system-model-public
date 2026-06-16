# =============================================================================
# HBM Controller RTL Makefile for Verilator (Simplified)
# =============================================================================
# Targets:
#   make lint   - Lint-only check without compilation
#   make sim    - Build and run simulation
#   make clean  - Remove generated files
# =============================================================================

# Directory structure
RTL_DIR := $(shell pwd)
OBJ_DIR := $(RTL_DIR)/obj_dir
LOG_DIR := $(RTL_DIR)/logs

# Verilator configuration
VERILATOR := verilator
VFLAGS := --lint-only -Wall -Wno-fatal

# Top module and testbench
TOP_MODULE ?= hbm_controller_tb_simple

# Source files (SystemVerilog)
RTL_SOURCES := \
	$(RTL_DIR)/hbm_types.svh \
	$(RTL_DIR)/hbm_controller.sv \
	$(RTL_DIR)/dram_model.sv

TB_SOURCE := $(RTL_DIR)/hbm_controller_tb_simple.sv

# File list for lint
FILELIST := $(RTL_DIR)/filelist.f

# Build flags
CXX := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -O2
LDFLAGS := -lpthread

# Simulation parameters
SIM_TIME ?= 10us

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

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
	@echo "Examples:"
	@echo "  make lint SIM_TIME=50us"
	@echo "  make sim TOP_MODULE=hbm_controller_tb_simple"
	@echo ""

# Target: lint
.PHONY: lint
lint: $(FILELIST)
	@echo "$(GREEN)== Running Verilator Lint Check ==$(NC)"
	@mkdir -p $(LOG_DIR)
	cd $(RTL_DIR) && $(VERILATOR) $(VFLAGS) -f $(FILELIST) --top-module hbm_controller 2>&1 | tee $(LOG_DIR)/lint.log
	@echo ""
	@echo "$(GREEN)== Lint Check Complete ==$(NC)"
	@echo "Log file: $(LOG_DIR)/lint.log"

# Target: sim (build and run)
.PHONY: sim
sim: $(OBJ_DIR)/V$(TOP_MODULE)
	@echo "$(GREEN)== Running Simulation ==$(NC)"
	cd $(OBJ_DIR) && ./V$(TOP_MODULE) +TIME=$(SIM_TIME) 2>&1 | tee $(LOG_DIR)/sim.log

$(OBJ_DIR)/V$(TOP_MODULE): $(RTL_SOURCES) $(TB_SOURCE) $(FILELIST)
	@echo "$(GREEN)== Building with Verilator ==$(NC)"
	@mkdir -p $(OBJ_DIR) $(LOG_DIR)
	cd $(RTL_DIR) && $(VERILATOR) \
		--cc \
		--build \
		--sv \
		--no-timing \
		-Wno-fatal \
		--top-module $(TOP_MODULE) \
		-f $(FILELIST) \
		--Mdir $(OBJ_DIR) \
		-CFLAGS "-std=c++17 -O2" \
		-LDFLAGS "-lpthread" \
		2>&1 | tee $(LOG_DIR)/build.log
	@echo ""
	@echo "$(GREEN)== Build Complete ==$(NC)"
	@echo "Binary: $(OBJ_DIR)/V$(TOP_MODULE)"
	@echo ""
	@echo "To run: cd $(OBJ_DIR) && ./V$(TOP_MODULE)"
	@echo "To view waveforms: open $(OBJ_DIR)/$(TOP_MODULE).vcd with gtkwave"

# Target: clean
.PHONY: clean
clean:
	@echo "$(YELLOW)== Cleaning Generated Files ==$(NC)"
	@rm -rf $(OBJ_DIR)
	@rm -rf $(LOG_DIR)
	@echo "$(GREEN)== Clean Complete ==$(NC)"

.DEFAULT_GOAL := help
