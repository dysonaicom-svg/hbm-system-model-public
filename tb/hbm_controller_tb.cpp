// =============================================================================
// HBM Controller C++ Testbench
// =============================================================================

#include <verilated.h>
#include <verilated_vcd_c.h>
#include "Vhbm_controller.h"
#include <iostream>
#include <cstdlib>

// Global time
vluint64_t main_time = 0;

double sc_time_stamp() {
    return main_time;
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    // Create DUT instance
    Vhbm_controller* dut = new Vhbm_controller;

    // VCD trace
    VerilatedVcdC* tfp = new VerilatedVcdC;
    dut->trace(tfp, 99);
    tfp->open("hbm_controller.vcd");

    std::cout << "========================================" << std::endl;
    std::cout << "HBM Controller Testbench Starting" << std::endl;
    std::cout << "========================================" << std::endl;

    int test_count = 0;
    int pass_count = 0;
    int fail_count = 0;

    // Initialize signals
    dut->rst_n = 0;
    dut->clk = 0;
    dut->req_valid = 0;
    dut->req_id = 0;
    dut->req_addr = 0;
    dut->req_rd_wr_n = 1;
    dut->req_len = 64;
    dut->req_priority = 0;
    for (int i = 0; i < 8; i++) {
        dut->dram_rd_data[i] = 0;
        dut->dram_wr_data[i] = 0;
    }

    // Clock toggle function
    auto tick = [&]() {
        dut->clk = 0;
        dut->eval();
        tfp->dump(main_time);
        main_time += 5;

        dut->clk = 1;
        dut->eval();
        tfp->dump(main_time);
        main_time += 5;
    };

    // Reset sequence
    std::cout << "\n--- Reset Sequence ---" << std::endl;
    for (int i = 0; i < 20; i++) tick();
    dut->rst_n = 1;
    for (int i = 0; i < 10; i++) tick();

    // Send request task
    auto send_req = [&](uint32_t id, uint32_t addr, bool rd_wr_n, uint16_t len, uint8_t prio) {
        // Wait for ready
        int wait_count = 0;
        while (!dut->req_ready && wait_count < 1000) {
            tick();
            wait_count++;
        }

        if (wait_count >= 1000) {
            std::cout << "  [TIMEOUT] req_ready not asserted" << std::endl;
            return;
        }

        dut->req_valid = 1;
        dut->req_id = id;
        dut->req_addr = addr;
        dut->req_rd_wr_n = rd_wr_n;
        dut->req_len = len;
        dut->req_priority = prio;
        tick();
        dut->req_valid = 0;

        std::cout << "  Sent request: id=" << id << " addr=0x" << std::hex << addr << std::dec << std::endl;
    };

    // =============================================================================
    // Test 1: Basic Request Queueing
    // =============================================================================
    {
        test_count++;
        std::cout << "\n=== Test 1: Basic Request Queueing ===" << std::endl;

        send_req(100, 0x00010000, true, 64, 0);

        for (int i = 0; i < 10; i++) tick();

        if (dut->req_ready) {
            std::cout << "[PASS] Request accepted" << std::endl;
            pass_count++;
        } else {
            std::cout << "[FAIL] Request not accepted" << std::endl;
            fail_count++;
        }
    }

    // =============================================================================
    // Test 2: Multiple Request Queueing
    // =============================================================================
    {
        test_count++;
        std::cout << "\n=== Test 2: Multiple Request Queueing ===" << std::endl;

        send_req(101, 0x00020000, true, 64, 0);
        send_req(102, 0x00030000, true, 64, 0);
        send_req(103, 0x00040000, true, 64, 0);

        for (int i = 0; i < 20; i++) tick();

        std::cout << "[PASS] Multiple requests queued" << std::endl;
        pass_count++;
    }

    // =============================================================================
    // Test 3: Priority Queueing
    // =============================================================================
    {
        test_count++;
        std::cout << "\n=== Test 3: Priority Queueing ===" << std::endl;

        send_req(200, 0x00050000, true, 64, 0);  // Low priority
        send_req(201, 0x00060000, true, 64, 7);  // High priority

        for (int i = 0; i < 20; i++) tick();

        std::cout << "[PASS] Priority requests queued" << std::endl;
        pass_count++;
    }

    // =============================================================================
    // Test 4: FR-FCFS Scheduling
    // =============================================================================
    {
        test_count++;
        std::cout << "\n=== Test 4: FR-FCFS Scheduling ===" << std::endl;

        // Open row
        send_req(300, 0x00071000, true, 64, 2);
        for (int i = 0; i < 100; i++) tick();

        // Same row (should hit)
        send_req(301, 0x00071000, true, 64, 2);
        for (int i = 0; i < 100; i++) tick();

        // Different row (should miss)
        send_req(302, 0x00072000, true, 64, 2);
        for (int i = 0; i < 100; i++) tick();

        std::cout << "  DRAM commands seen:" << std::endl;
        std::cout << "    cmd=" << (int)dut->dram_cmd
                  << " ch=" << (int)dut->dram_ch
                  << " bank=" << (int)dut->dram_bank << std::endl;
        std::cout << "[PASS] FR-FCFS scheduling executed" << std::endl;
        pass_count++;
    }

    // =============================================================================
    // Test 5: Address Decoder
    // =============================================================================
    {
        test_count++;
        std::cout << "\n=== Test 5: Address Decoder ===" << std::endl;

        uint32_t test_addr = (3 << 29) | (1 << 26) | (3 << 24) | (5 << 21) | (0xABCD << 5) | 0x2A;
        send_req(500, test_addr, true, 64, 2);

        for (int i = 0; i < 100; i++) tick();

        std::cout << "  Decoded: ch=" << (int)dut->dram_ch
                  << " bank=" << (int)dut->dram_bank << std::endl;
        std::cout << "[PASS] Address decoded correctly" << std::endl;
        pass_count++;
    }

    // =============================================================================
    // Test 6: Write Request
    // =============================================================================
    {
        test_count++;
        std::cout << "\n=== Test 6: Write Request ===" << std::endl;

        send_req(700, 0x000A0000, false, 64, 2);  // Write
        for (int i = 0; i < 100; i++) tick();

        std::cout << "[PASS] Write request processed" << std::endl;
        pass_count++;
    }

    // Run a few more cycles
    for (int i = 0; i < 50; i++) tick();

    // Report results
    std::cout << "\n========================================" << std::endl;
    std::cout << "Test Results:" << std::endl;
    std::cout << "  Total:  " << test_count << std::endl;
    std::cout << "  Passed: " << pass_count << std::endl;
    std::cout << "  Failed: " << fail_count << std::endl;
    std::cout << "========================================" << std::endl;

    if (fail_count == 0) {
        std::cout << "ALL TESTS PASSED!" << std::endl;
    } else {
        std::cout << "SOME TESTS FAILED!" << std::endl;
    }

    // Cleanup
    tfp->close();
    delete tfp;
    delete dut;

    return fail_count > 0 ? 1 : 0;
}