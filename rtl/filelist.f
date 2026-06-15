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
+incdir+.

# Type definitions (order matters - header first)
hbm_types.svh

# Package definitions (UVM-based - for reference/simulation)
# Note: hbm_pkg.sv uses UVM which is not supported by verilator
# hbm_pkg.sv

# Main controller RTL
hbm_controller.sv

# DRAM model
dram_model.sv

# Testbench (for simulation, not lint - add via command line)
# hbm_controller_tb.sv
