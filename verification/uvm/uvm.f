# ------------------------------------------------------------
# uvm.f - File list for HBM UVM verification
# ------------------------------------------------------------

# UVM Library
+incdir+/usr/share/verilator/uvm/src
/usr/share/verilator/uvm/src/uvm.svh

# Local packages
+incdir+.
./hbm_env_pkg.sv
./hbm_test_pkg.sv

# Testbench top
./hbm_tb.sv