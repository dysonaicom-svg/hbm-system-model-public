# =============================================================================
# RTL File List for HBM Controller
# Verilator compilation
# =============================================================================
#
# Usage: verilator --lint-only -f filelist.f
#        verilator --cc --exe --build -f filelist.f testbench.sv
#
# =============================================================================

# Include directories
+incdir+/home/ic/JXTF/HBM/rtl

# Type definitions (order matters - header first)
/home/ic/JXTF/HBM/rtl/hbm_types.svh

# Package definitions (UVM-based - for reference/simulation)
# Note: hbm_pkg.sv uses UVM which is not supported by verilator
# /home/ic/JXTF/HBM/rtl/hbm_pkg.sv

# Main controller RTL
/home/ic/JXTF/HBM/rtl/hbm_controller.sv

# DRAM model
/home/ic/JXTF/HBM/rtl/dram_model.sv

# Testbench (for simulation, add via command line: hbm_controller_tb.sv hbm_controller_tb_main.cpp)
# hbm_controller_tb.sv
