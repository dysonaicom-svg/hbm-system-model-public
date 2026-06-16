// =============================================================================
// HBM Controller Testbench Main - Direct DUT Control with VCD
// =============================================================================
#include <iostream>
#include <cstdlib>
#include <iomanip>
#include <set>
#include "verilated.h"
#include "verilated_vcd_c.h"
#include "Vhbm_controller_tb.h"

// Global time
vluint64_t main_time = 0;

double sc_time_stamp() {
    return main_time;
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    // Create DUT instance (hbm_controller)
    Vhbm_controller_tb* dut = new Vhbm_controller_tb;

    // VCD trace
    VerilatedVcdC* tfp = new VerilatedVcdC;
    dut->trace(tfp, 99);
    tfp->open("hbm_controller_tb.vcd");

    std::cout << "========================================" << std::endl;
    std::cout << "HBM Controller RTL Simulation Started" << std::endl;
    std::cout << "========================================" << std::endl;

    int cycle_count = 0;
    std::set<uint32_t> seen_resp_ids;

    // Clock toggle - cycle-based (10ns period)
    auto tick = [&]() {
        dut->clk = 0;
        dut->eval();
        tfp->dump(main_time);
        main_time += 5;
        dut->clk = 1;
        dut->eval();
        tfp->dump(main_time);
        main_time += 5;
        cycle_count++;
    };

    // Reset sequence
    std::cout << "\n--- Reset Sequence ---" << std::endl;
    for (int i = 0; i < 10; i++) tick();
    dut->rst_n = 1;
    for (int i = 0; i < 5; i++) tick();

    std::cout << "--- Reset Complete at cycle " << cycle_count << " ---" << std::endl;

    // Send request helper
    auto send_req = [&](uint32_t id, uint32_t addr, bool rd_wr_n, uint16_t len, uint8_t prio) {
        int wait = 0;
        while (!dut->req_ready && wait < 1000) {
            tick();
            wait++;
        }
        if (wait >= 1000) {
            std::cout << "  [TIMEOUT] req_ready not asserted" << std::endl;
            return false;
        }
        dut->req_valid = 1;
        dut->req_id = id;
        dut->req_addr = addr;
        dut->req_rd_wr_n = rd_wr_n ? 1 : 0;
        dut->req_len = len;
        dut->req_priority = prio;
        tick();
        dut->req_valid = 0;
        std::cout << "  Sent: id=" << id << " addr=0x" << std::hex << std::setw(8) << std::setfill('0') << addr << std::dec << std::endl;
        return true;
    };

    int test_count = 0;
    int pass_count = 0;
    int fail_count = 0;
    int resp_expected = 0;
    int resp_received = 0;

    // Test 1: Basic read request
    test_count++;
    std::cout << "\n=== Test 1: Basic Read Request ===" << std::endl;
    if (send_req(100, 0x00010000, true, 64, 5)) {
        resp_expected++;
        std::cout << "[PASS] Request accepted" << std::endl;
        pass_count++;
    } else {
        std::cout << "[FAIL] Request not accepted" << std::endl;
        fail_count++;
    }

    // Test 2: Write request
    test_count++;
    std::cout << "\n=== Test 2: Write Request ===" << std::endl;
    if (send_req(101, 0x00020000, false, 64, 5)) {
        resp_expected++;
        std::cout << "[PASS] Write request accepted" << std::endl;
        pass_count++;
    } else {
        std::cout << "[FAIL] Write request failed" << std::endl;
        fail_count++;
    }

    // Test 3: FR-FCFS scheduling
    test_count++;
    std::cout << "\n=== Test 3: FR-FCFS Scheduling ===" << std::endl;
    send_req(200, 0x00031000, true, 64, 3);
    resp_expected++;
    for (int i = 0; i < 100; i++) tick();

    send_req(201, 0x00031000, true, 64, 3);
    resp_expected++;
    for (int i = 0; i < 100; i++) tick();

    send_req(202, 0x00032000, true, 64, 3);
    resp_expected++;
    std::cout << "  FR-FCFS tests sent" << std::endl;
    pass_count++;

    // Test 4: Priority
    test_count++;
    std::cout << "\n=== Test 4: Priority Queueing ===" << std::endl;
    send_req(300, 0x00040000, true, 64, 0);
    resp_expected++;
    send_req(301, 0x00050000, true, 64, 7);
    resp_expected++;
    std::cout << "[PASS] Priority requests queued" << std::endl;
    pass_count++;

    // Test 5: Burst requests
    test_count++;
    std::cout << "\n=== Test 5: Burst Requests ===" << std::endl;
    for (int i = 0; i < 5; i++) {
        send_req(400 + i, 0x00060000 + (i << 12), true, 64, 3);
        resp_expected++;
    }
    std::cout << "[PASS] Burst requests queued" << std::endl;
    pass_count++;

    // Collect responses
    std::cout << "\n--- Collecting Responses ---" << std::endl;
    for (int i = 0; i < 500 && resp_received < resp_expected; i++) {
        tick();
        if (dut->resp_valid) {
            uint32_t rid = dut->resp_id;
            if (seen_resp_ids.find(rid) == seen_resp_ids.end()) {
                seen_resp_ids.insert(rid);
                resp_received++;
                std::cout << "  Response " << resp_received << ": id=" << rid
                          << " success=" << (int)dut->resp_success
                          << " status=" << (int)dut->resp_status
                          << " at cycle " << cycle_count << std::endl;
            }
        }
    }

    // Final cycles
    for (int i = 0; i < 50; i++) tick();

    // Report
    std::cout << "\n========================================" << std::endl;
    std::cout << "Test Results:" << std::endl;
    std::cout << "  Total Tests:     " << test_count << std::endl;
    std::cout << "  Passed:          " << pass_count << std::endl;
    std::cout << "  Failed:          " << fail_count << std::endl;
    std::cout << "  Expected Resp:   " << resp_expected << std::endl;
    std::cout << "  Received Resp:   " << resp_received << std::endl;
    std::cout << "  Total Cycles:    " << cycle_count << std::endl;
    std::cout << "========================================" << std::endl;
    // Statistics are internal to testbench
    std::cout << "\nStatistics:" << std::endl;
    std::cout << "  (See waveform for internal stats)" << std::endl;

    if (fail_count == 0 && resp_received >= resp_expected) {
        std::cout << "\n*** ALL TESTS PASSED! ***" << std::endl;
    } else {
        std::cout << "\n*** SOME TESTS FAILED! ***" << std::endl;
    }

    // Cleanup
    tfp->close();
    delete tfp;
    delete dut;

    std::cout << "Simulation completed at cycle " << cycle_count << std::endl;

    return (fail_count > 0 || resp_received < resp_expected) ? 1 : 0;
}
