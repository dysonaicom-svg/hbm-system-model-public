// =============================================================================
// HBM Controller Testbench Main - C++ wrapper
// =============================================================================
// This file provides the main() function for Verilator --exe build

#include <verilated.h>
#include <verilated_vcd_c.h>
#include "Vhbm_controller_tb.h"

vluint64_t main_time = 0;

double sc_time_stamp() {
    return main_time;
}

int main(int argc, char** argv) {
    // Initialize Verilator
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    // Create testbench instance
    Vhbm_controller_tb* tb = new Vhbm_controller_tb();

    // Create VCD dumper
    VerilatedVcdC* tfp = new VerilatedVcdC();
    tb->trace(tfp, 99);
    tfp->open("hbm_controller_tb.vcd");

    // Reset signal
    tb->rst_n = 0;

    // Main simulation loop
    while (!Verilated::gotFinish()) {
        // Toggle clock
        tb->clk = 0;
        tb->eval();
        tfp->dump(main_time);
        main_time++;

        tb->clk = 1;
        tb->eval();
        tfp->dump(main_time);
        main_time++;

        // Release reset after 10 cycles
        if (main_time == 20) {
            tb->rst_n = 1;
        }

        // Timeout after 10000 cycles
        if (main_time > 10000) {
            printf("Timeout reached\n");
            break;
        }
    }

    // Final evaluation
    tb->eval();

    // Close VCD
    tfp->dump(main_time);
    tfp->close();

    // Cleanup
    delete tb;
    delete tfp;

    return 0;
}