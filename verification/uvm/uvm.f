# ------------------------------------------------------------
# uvm.f - File list for HBM RTL simulation (Verilator)
# ------------------------------------------------------------

# UVM stub library
+incdir+/home/ic/JXTF/HBM/verification/uvm/uvm_stub/src
/home/ic/JXTF/HBM/verification/uvm/uvm_stub/src/uvm.svh

# Reference model files
+incdir+/home/ic/JXTF/HBM/verification/reference_model
/home/ic/JXTF/HBM/verification/reference_model/dram_ref_model.sv
/home/ic/JXTF/HBM/verification/reference_model/timing_checker.sv
/home/ic/JXTF/HBM/verification/reference_model/bandwidth_calc.sv
/home/ic/JXTF/HBM/verification/reference_model/addr_decoder_ref.sv

# Environment and test packages
+incdir+/home/ic/JXTF/HBM/verification/uvm
/home/ic/JXTF/HBM/verification/uvm/hbm_env_pkg.sv
/home/ic/JXTF/HBM/verification/uvm/hbm_test_pkg.sv

# Additional test packages
+incdir+/home/ic/JXTF/HBM/verification/uvm/tests
/home/ic/JXTF/HBM/verification/uvm/tests/hbm_qos_test_pkg.sv
/home/ic/JXTF/HBM/verification/uvm/tests/hbm_refresh_test_pkg.sv
/home/ic/JXTF/HBM/verification/uvm/tests/hbm_bank_contention_test_pkg.sv
/home/ic/JXTF/HBM/verification/uvm/tests/hbm_boundary_test_pkg.sv
/home/ic/JXTF/HBM/verification/uvm/tests/hbm_new_tests_pkg.sv
/home/ic/JXTF/HBM/verification/uvm/tests/test_multi_channel_seq.sv

# Testbench top
/home/ic/JXTF/HBM/verification/uvm/hbm_tb.sv