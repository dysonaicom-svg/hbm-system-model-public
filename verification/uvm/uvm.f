# ------------------------------------------------------------
# uvm.f - File list for HBM RTL simulation (Verilator)
# ------------------------------------------------------------

# Reference model files
+incdir+/home/ic/JXTF/HBM/verification/reference_model
/home/ic/JXTF/HBM/verification/reference_model/dram_ref_model.sv
/home/ic/JXTF/HBM/verification/reference_model/timing_checker.sv
/home/ic/JXTF/HBM/verification/reference_model/bandwidth_calc.sv
/home/ic/JXTF/HBM/verification/reference_model/addr_decoder_ref.sv

# RTL controller
+incdir+/home/ic/JXTF/HBM/rtl
/home/ic/JXTF/HBM/rtl/hbm_controller.sv

# Testbench top
/home/ic/JXTF/HBM/verification/uvm/hbm_tb.sv

# Main entry point
/home/ic/JXTF/HBM/verification/uvm/build/main.cpp