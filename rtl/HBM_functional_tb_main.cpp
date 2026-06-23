// =============================================================================
// HBM Controller Functional Testbench Main - Simple driver
// =============================================================================
#include <iostream>
#include "verilated.h"
#include "verilated_vcd_c.h"
#include "Vhbm_functional_tb.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);

    // Enable tracing
    Verilated::traceEverOn(true);

    // Create testbench instance
    Vhbm_functional_tb* tb = new Vhbm_functional_tb;

    std::cout << std::endl;
    std::cout << "################################################################" << std::endl;
    std::cout << "#       HBM Controller Functional Testbench Driver               #" << std::endl;
    std::cout << "################################################################" << std::endl;

    int cycle_count = 0;

    // Main simulation loop - drive clock
    while (!Verilated::gotFinish() && cycle_count < 100000) {
        tb->clk = !tb->clk;
        tb->eval();
        if (tb->clk) cycle_count++;
    }

    std::cout << std::endl;
    std::cout << "################################################################" << std::endl;
    std::cout << "Simulation completed: " << cycle_count << " cycles" << std::endl;
    std::cout << "################################################################" << std::endl;

    delete tb;
    return 0;
}
