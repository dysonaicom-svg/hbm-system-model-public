// =============================================================================
// HBM Controller Functional Testbench Main - Clock-driven driver
// =============================================================================
#include <iostream>
#include "verilated.h"
#include "Vhbm_functional_tb.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    // Create testbench instance
    Vhbm_functional_tb* tb = new Vhbm_functional_tb;

    std::cout << std::endl;
    std::cout << "################################################################" << std::endl;
    std::cout << "#       HBM Controller Functional Testbench Driver               #" << std::endl;
    std::cout << "################################################################" << std::endl;

    int max_cycles = 200000;

    // Initialize clock to 0
    tb->clk = 0;

    // Main simulation loop - drive clock
    for (int cycle = 0; cycle < max_cycles && !Verilated::gotFinish(); cycle++) {
        // Toggle clock
        tb->clk = !tb->clk;
        // Evaluate
        tb->eval();
        // Check if testbench finished
        if (Verilated::gotFinish()) break;
        // Second half cycle
        tb->clk = !tb->clk;
        tb->eval();
    }

    std::cout << std::endl;
    std::cout << "################################################################" << std::endl;
    std::cout << "Simulation completed: " << max_cycles << " cycles" << std::endl;
    std::cout << "################################################################" << std::endl;

    delete tb;
    return 0;
}
