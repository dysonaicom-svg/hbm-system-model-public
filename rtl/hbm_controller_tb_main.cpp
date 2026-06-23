// =============================================================================
// HBM Controller Testbench Main - Simple driver for no-timing simulation
// =============================================================================
#include <iostream>
#include "verilated.h"
#include "Vhbm_controller_tb_simple.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    // Create DUT instance
    Vhbm_controller_tb_simple* dut = new Vhbm_controller_tb_simple;

    std::cout << "========================================" << std::endl;
    std::cout << "HBM Controller RTL Simulation Started" << std::endl;
    std::cout << "========================================" << std::endl;

    int cycle_count = 0;

    // Main simulation loop - just drive clock
    // Testbench has its own $finish after 50 cycles
    while (!Verilated::gotFinish() && cycle_count < 1000) {
        dut->clk = !dut->clk;
        dut->eval();
        cycle_count++;
    }

    std::cout << "Simulation completed: " << cycle_count << " cycles" << std::endl;

    delete dut;
    return 0;
}