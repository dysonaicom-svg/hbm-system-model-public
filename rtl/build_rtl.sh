#!/bin/bash
# =============================================================================
# HBM Controller RTL Build Script
# =============================================================================
# This script documents the toolchain requirements for RTL compilation
# =============================================================================

set -e

echo "============================================================"
echo "HBM Controller RTL Build"
echo "============================================================"

# Detect available simulators
check_simulator() {
    local sim=$1
    if command -v $sim &> /dev/null; then
        echo "  $sim: $(command -v $sim)"
        return 0
    else
        echo "  $sim: NOT FOUND"
        return 1
    fi
}

echo ""
echo "Checking available simulators..."

VERILATOR_FOUND=0
IVERILOG_FOUND=0
VCS_FOUND=0
QUESTA_FOUND=0

check_simulator verilator && VERILATOR_FOUND=1
check_simulator iverilog && IVERILOG_FOUND=1
check_simulator vcs && VCS_FOUND=1
check_simulator qverilog && QUESTA_FOUND=1
check_simulator vsim && QUESTA_FOUND=1

echo ""
echo "Toolchain Requirements:"
echo "----------------------"

# Verilator requirements
if [ $VERILATOR_FOUND -eq 1 ]; then
    echo ""
    echo "Verilator $(verilator --version 2>/dev/null | head -1):"
    echo "  Status: AVAILABLE"
    echo "  Build command: verilator --cc --exe --build --sv --timing ..."
    echo "  Note: Requires GCC with C++20 coroutine support"
    echo "  Check: g++ -std=c++20 -fcoroutines -x c++ - <<< 'await std::suspend_always{};' 2>&1"
else
    echo "Verilator: NOT AVAILABLE"
fi

# iverilog requirements
if [ $IVERILOG_FOUND -eq 1 ]; then
    echo ""
    echo "Icarus Verilog $(iverilog -V 2>&1 | head -1):"
    echo "  Status: AVAILABLE"
    echo "  Limitations: Limited SystemVerilog support"
    echo "  Note: May need simplified RTL for compatibility"
else
    echo "Icarus Verilog: NOT AVAILABLE"
fi

# Commercial simulators
if [ $VCS_FOUND -eq 1 ]; then
    echo ""
    echo "Synopsys VCS: AVAILABLE (RECOMMENDED)"
    echo "  Full SystemVerilog 2012 support"
    echo "  Build: vcs -sverilog ..."
fi

if [ $QUESTA_FOUND -eq 1 ]; then
    echo ""
    echo "Siemens Questa/ModelSim: AVAILABLE (RECOMMENDED)"
    echo "  Full UVM support"
    echo "  Build: qverilog -sv ..."
fi

echo ""
echo "============================================================"
echo "Build Instructions"
echo "============================================================"
echo ""

# Verilator build (if supported)
if [ $VERILATOR_FOUND -eq 1 ]; then
    echo "1. Verilator Build (recommended with GCC 12+):"
    echo "   cd rtl"
    echo "   verilator --cc --exe --build --sv --timing \\"
    echo "     --top-module hbm_controller_tb \\"
    echo "     -I. \\"
    echo "     hbm_controller_tb.sv \\"
    echo "     hbm_controller.sv \\"
    echo "     dram_model.sv \\"
    echo "     hbm_types.svh"
    echo ""
    echo "   # Run simulation:"
    echo "   cd obj_dir"
    echo "   ./Vhbm_controller_tb"
    echo ""
fi

# Questa build (if available)
if [ $QUESTA_FOUND -eq 1 ]; then
    echo "2. Questa/ModelSim Build:"
    echo "   cd verification/uvm"
    echo "   make compile"
    echo "   make run"
    echo ""
fi

# VCS build (if available)
if [ $VCS_FOUND -eq 1 ]; then
    echo "3. VCS Build:"
    echo "   cd rtl"
    echo "   vcs -sverilog -uvm -ntb_opts uvm-1.2 \\"
    echo "     hbm_types.svh hbm_pkg.sv hbm_controller.sv \\"
    echo "     dram_model.sv hbm_controller_tb.sv"
    echo "   ./simv"
    echo ""
fi

# Summary
echo "============================================================"
echo "Summary"
echo "============================================================"
echo ""
echo "RTL Files:"
echo "  - hbm_types.svh    : Type definitions"
echo "  - hbm_pkg.sv       : UVM package (requires commercial simulator)"
echo "  - hbm_controller.sv: Main controller RTL"
echo "  - dram_model.sv    : DRAM model RTL"
echo "  - hbm_controller_tb.sv: Testbench"
echo ""
echo "Verification:"
if [ $QUESTA_FOUND -eq 1 ] || [ $VCS_FOUND -eq 1 ]; then
    echo "  Status: READY (commercial simulator available)"
else
    echo "  Status: NEED_TOOLCHAIN"
    echo "  Action: Install Verilator with GCC 12+ or Questa/VCS"
fi
echo ""
