# RTL File List for HBM Controller
# Verilator compilation

# Type definitions (order matters - header first)
+incdir+rtl
rtl/hbm_types.svh

# Package definitions (UVM-based - for reference/simulation)
# Note: hbm_pkg.sv uses UVM which is not supported by verilator
# rtl/hbm_pkg.sv

# Main controller RTL
rtl/hbm_controller.sv