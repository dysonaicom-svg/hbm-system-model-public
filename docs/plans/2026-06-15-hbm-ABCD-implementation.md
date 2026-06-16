# HBM 系统完整实现计划 (ABCD)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成 HBM 系统模型的性能基准测试、RTL 实现、UVM 验证环境和参考模型

**Architecture:** 基于 Python 原型实现，转换为 SystemVerilog RTL，同时构建 UVM 验证环境和性能参考模型

**Tech Stack:** Python (原型) → SystemVerilog (RTL) + UVM (验证)

---

## 模块概览

| 模块 | 任务 | 文件 |
|------|------|------|
| A. 性能基准测试 | 运行仿真，分析性能 | `sim/benchmark.py`, `tests/sim/test_benchmark.py` |
| B. RTL 实现 | 控制器 + DRAM 模型 | `rtl/hbm_controller.sv`, `rtl/dram_model.sv` |
| C. UVM 验证环境 | 验证平台 | `verification/uvm/` |
| D. 参考模型 | 性能参考模型 | `verification/reference_model/` |

---

## A. 性能基准测试

### Task A.1: 创建基准测试框架

**Files:**
- Create: `sim/benchmark.py`
- Test: `tests/sim/test_benchmark.py`

**Step 1: 创建基准测试模块**

```python
"""HBM System Performance Benchmark
性能基准测试模块 - 分析不同流量模式下的吞吐量和延迟
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Optional
from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats, TrafficPattern


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    pattern: str
    request_rate: float
    total_requests: int
    completed: int
    row_hit_rate: float
    avg_latency: float
    throughput_gbps: float
    simulation_time_ms: float


class HBMBenchmark:
    """HBM 性能基准测试器"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def run_single(
        self,
        pattern: TrafficPattern,
        request_rate: float,
        time_us: float = 100.0,
        seed: Optional[int] = None
    ) -> BenchmarkResult:
        """运行单个基准测试"""
        config = SimulationConfig(
            simulation_time_us=time_us,
            traffic_pattern=pattern,
            request_rate=request_rate,
            read_ratio=0.7,
            seed=seed
        )

        start = time.time()
        sim = HBMSimulator(config)
        stats = sim.run()
        elapsed_ms = (time.time() - start) * 1000

        return BenchmarkResult(
            pattern=pattern.value,
            request_rate=request_rate,
            total_requests=stats.total_requests,
            completed=stats.completed_requests,
            row_hit_rate=stats.row_hit_rate,
            avg_latency=stats.avg_latency,
            throughput_gbps=stats.throughput_gbps,
            simulation_time_ms=elapsed_ms
        )

    def run_suite(self) -> List[BenchmarkResult]:
        """运行完整基准测试套件"""
        patterns = [
            TrafficPattern.RANDOM,
            TrafficPattern.SEQUENTIAL,
            TrafficPattern.STRIDE,
            TrafficPattern.HOT_SPOT,
        ]

        rates = [0.3, 0.5, 0.8, 1.0]

        for pattern in patterns:
            for rate in rates:
                print(f"Running {pattern.value} @ rate={rate}...")
                result = self.run_single(pattern, rate, time_us=100.0, seed=42)
                self.results.append(result)

        return self.results

    def print_results(self):
        """打印结果表格"""
        print("\n" + "=" * 90)
        print(f"{'Pattern':<15} {'Rate':>6} {'Reqs':>8} {'Completed':>10} "
              f"{'Hit%':>8} {'Latency':>10} {'TPut':>10} {'Time':>8}")
        print("-" * 90)

        for r in self.results:
            print(f"{r.pattern:<15} {r.request_rate:>6.2f} {r.total_requests:>8} "
                  f"{r.completed:>10} {r.row_hit_rate:>8.1%} {r.avg_latency:>10.1f} "
                  f"{r.throughput_gbps:>10.2f} {r.simulation_time_ms:>8.1f}")

        print("=" * 90)


def main():
    """运行基准测试"""
    print("=" * 60)
    print("HBM Performance Benchmark Suite")
    print("=" * 60)

    bench = HBMBenchmark()
    bench.run_suite()
    bench.print_results()

    # 保存结果
    import json
    results_dict = [
        {
            "pattern": r.pattern,
            "request_rate": r.request_rate,
            "total_requests": r.total_requests,
            "completed": r.completed,
            "row_hit_rate": r.row_hit_rate,
            "avg_latency": r.avg_latency,
            "throughput_gbps": r.throughput_gbps,
            "simulation_time_ms": r.simulation_time_ms
        }
        for r in bench.results
    ]

    with open("sim/benchmark_results.json", "w") as f:
        json.dump(results_dict, f, indent=2)

    print("\nResults saved to sim/benchmark_results.json")


if __name__ == "__main__":
    main()
```

**Step 2: 创建测试文件**

```python
"""Benchmark Tests
性能基准测试
"""

import sys
sys.path.insert(0, '/home/ic/JXTF/HBM')

import pytest
from sim.benchmark import HBMBenchmark, BenchmarkResult, TrafficPattern


class TestHBMBenchmark:
    """测试 HBM 基准测试器"""

    def test_benchmark_creation(self):
        bench = HBMBenchmark()
        assert len(bench.results) == 0

    def test_single_benchmark(self):
        bench = HBMBenchmark()
        result = bench.run_single(
            pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            time_us=10.0,
            seed=42
        )

        assert isinstance(result, BenchmarkResult)
        assert result.pattern == "random"
        assert result.request_rate == 0.5
        assert result.total_requests >= 0
        assert result.row_hit_rate >= 0.0
        assert result.throughput_gbps >= 0.0

    def test_benchmark_suite(self):
        """测试基准测试套件"""
        bench = HBMBenchmark()

        # 只测试少量配置快速验证
        patterns = [TrafficPattern.RANDOM, TrafficPattern.SEQUENTIAL]
        rates = [0.3, 0.5]

        for pattern in patterns:
            for rate in rates:
                result = bench.run_single(pattern, rate, time_us=10.0, seed=42)
                bench.results.append(result)

        assert len(bench.results) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Step 3: 运行测试**

Run: `python3 -m pytest tests/sim/test_benchmark.py -v`
Expected: PASS

**Step 4: 运行基准测试**

Run: `python3 sim/benchmark.py`
Expected: 输出性能表格

**Step 5: 提交**

```bash
git add sim/benchmark.py tests/sim/test_benchmark.py
git commit -m "feat: add HBM performance benchmark suite"
```

---

## B. RTL 实现

### Task B.1: 创建 RTL 目录结构

**Files:**
- Create: `rtl/hbm_controller.sv`
- Create: `rtl/dram_model.sv`
- Create: `rtl/hbm_pkg.sv`
- Create: `rtl/hbm_types.svh`

**Step 1: 创建类型定义头文件**

```systemverilog
// hbm_types.svh - HBM 类型定义
// 参考设计文档 2026-06-15-hbm-system-model-design.md

`ifndef HBM_TYPES_SVH
`define HBM_TYPES_SVH

// 地址映射 (Address Mapping)
// 根据设计文档 5.1.5 节
// HBM3 地址位分配: Row[15:0] - Bank[3:0] - BankGroup[2:0] - Channel[2:0] - Stack[2:0]
typedef struct packed {
    logic [2:0]  stack;        // Stack ID (0-7)
    logic [2:0]  channel;      // Channel ID (0-7)
    logic [2:0]  bank_group;   // Bank Group ID (0-7)
    logic [3:0]  bank;         // Bank ID (0-15)
    logic [15:0] row;          // Row ID
    logic [9:0]  col;          // Column (burst aligned)
} hbm_addr_t;

// 请求类型
typedef enum logic [2:0] {
    REQ_READ  = 3'b001,
    REQ_WRITE = 3'b010,
    REQ_ACT   = 3'b011,
    REQ_PRE   = 3'b100,
    REQ_REF   = 3'b101,
    REQ_NOP   = 3'b000
} hbm_req_type_t;

// 请求状态
typedef enum logic [1:0] {
    REQ_IDLE      = 2'b00,
    REQ_PENDING   = 2'b01,
    REQ_IN_FLIGHT = 2'b10,
    REQ_COMPLETE  = 2'b11
} hbm_req_state_t;

// Bank 状态
typedef enum logic [2:0] {
    BANK_IDLE     = 3'b000,
    BANK_ACTIVE   = 3'b001,
    BANK_BUSY     = 3'b010,
    BANK_REFRESH  = 3'b011,
    BANK_POWER_DOWN = 3'b100
} hbm_bank_state_t;

// DRAM 命令
typedef enum logic [3:0] {
    CMD_NOP    = 4'b0000,
    CMD_ACT    = 4'b0001,
    CMD_READ   = 4'b0010,
    CMD_WRITE  = 4'b0011,
    CMD_PRE    = 4'b0100,
    CMD_PRE_AB = 4'b0101,
    CMD_REF    = 4'b0110,
    CMD_SRE    = 4'b0111,
    CMD_PDE    = 4'b1000,
    CMD_SX     = 4'b1001
} hbm_cmd_t;

// HBM3 时序参数 (cycles @ 1.28 GHz)
typedef struct packed {
    logic [8:0]  tRCD;   // RAS to CAS delay: 17 cycles
    logic [8:0]  tRP;    // Precharge time: 17 cycles
    logic [8:0]  tRAS;   // Active to precharge: 42 cycles
    logic [8:0]  tRC;    // Row cycle time: 59 cycles
    logic [4:0]  tCCD;   // CAS to CAS delay: 5 cycles
    logic [4:0]  tRRD;   // Rank row to rank delay: 5 cycles
    logic [8:0]  tFAW;   // Four bank activation window: 26 cycles
    logic [9:0]  tRFC;   // Refresh cycle: 295 cycles
    logic [13:0] tREFI;  // Refresh interval: 5000 cycles
} hbm_timing_t;

// 请求结构
typedef struct packed {
    logic [31:0]         req_id;
    hbm_addr_t           addr;
    hbm_req_type_t       req_type;
    logic [15:0]         length;      // burst count
    logic [2:0]          priority;    // 0=low, 7=high
    hbm_req_state_t      state;
    logic [15:0]         cycle_submitted;
    logic [15:0]         cycle_complete;
} hbm_req_t;

// 响应结构
typedef struct packed {
    logic [31:0]         req_id;
    logic                success;
    logic [7:0]          status;
    logic [15:0]         latency;
    hbm_addr_t           addr;
} hbm_resp_t;

// 常量定义
localparam NUM_STACKS          = 8;
localparam NUM_CHANNELS        = 8;
localparam NUM_BANK_GROUPS     = 8;
localparam NUM_BANKS           = 16;
localparam ROW_SIZE            = 2048;  // bytes
localparam BURST_LENGTH        = 32;    // FLINE
localparam CACHE_LINE_SIZE     = 64;    // bytes

// 默认时序参数 (HBM3)
localparam HBM3_TIMING = '{
    tRCD:   9'd17,
    tRP:    9'd17,
    tRAS:   9'd42,
    tRC:    9'd59,
    tCCD:   5'd5,
    tRRD:   5'd5,
    tFAW:   9'd26,
    tRFC:   10'd295,
    tREFI:  14'd5000
};

`endif // HBM_TYPES_SVH
```

**Step 2: 创建 HBM 包文件**

```systemverilog
// hbm_pkg.sv - HBM 包定义
// 包含所有 HBM 相关的子模块和定义

`timescale 1ns / 1ps

package hbm_pkg;
    import uvm_pkg::*;
    
    // 包含类型定义
    `include "hbm_types.svh"
    
    // 寄存器模型
    typedef struct packed {
        logic [31:0] ctrl_cfg;
        logic [31:0] timing_cfg;
        logic [31:0] queue_cfg;
        logic [31:0] refresh_cfg;
    } hbm_reg_t;
    
    // 配置类
    class hbm_configuration extends uvm_object;
        `uvm_object_utils(hbm_configuration)
        
        int stack_count = 8;
        int channels_per_stack = 8;
        int banks_per_channel = 16;
        int queue_depth = 32;
        bit enable_qos = 1;
        bit enable_refresh = 1;
        
        function new(string name = "hbm_configuration");
            super.new(name);
        endfunction
    endclass
    
    // 请求事务
    class hbm_transaction extends uvm_sequence_item;
        `uvm_object_utils(hbm_transaction)
        
        rand hbm_addr_t addr;
        rand hbm_req_type_t req_type;
        rand logic [15:0] length;
        rand logic [2:0] priority;
        logic [31:0] req_id;
        logic [15:0] cycle_submitted;
        
        constraint valid_addr {
            addr.stack < NUM_STACKS;
            addr.channel < NUM_CHANNELS;
            addr.bank_group < NUM_BANK_GROUPS;
            addr.bank < NUM_BANKS;
        }
        
        constraint valid_length {
            length inside {16, 32, 64, 128};
        }
        
        function new(string name = "hbm_transaction");
            super.new(name);
        endfunction
    endclass
    
endpackage
```

**Step 3: 创建 DRAM 模型 RTL**

```systemverilog
// dram_model.sv - HBM DRAM 模型
// 实现 Bank 状态机和时序检查
// 参考 model/dram/dram_model.py

`timescale 1ns / 1ps
`include "hbm_types.svh"

module dram_model #(
    parameter STACK_ID = 0,
    parameter NUM_CHANNELS = 8,
    parameter NUM_BANKS = 16
)(
    input  wire             clk,
    input  wire             rst_n,
    
    // 命令接口
    input  wire [3:0]      cmd,
    input  wire [2:0]      ch_id,
    input  wire [3:0]      bank_id,
    input  wire [15:0]     row_id,
    
    // 数据接口
    input  wire [255:0]    wr_data,
    output wire [255:0]    rd_data,
    
    // 状态输出
    output wire [2:0]      bank_state [NUM_CHANNELS][NUM_BANKS],
    output wire            refresh_active,
    
    // 配置
    input  wire [8:0]      tRCD,
    input  wire [8:0]      tRP,
    input  wire [8:0]      tRAS,
    input  wire [8:0]      tRC
);
    
    // Bank 状态机状态
    typedef enum logic [2:0] {
        S_IDLE = 3'b000,
        S_ACTIVE = 3'b001,
        S_BUSY = 3'b010,
        S_REFRESH = 3'b011
    } bank_state_t;
    
    // Bank 状态数组
    bank_state_t bank_state_r [NUM_CHANNELS][NUM_BANKS];
    bank_state_t bank_state_n [NUM_CHANNELS][NUM_BANKS];
    
    // 行状态
    logic [15:0] open_row [NUM_CHANNELS][NUM_BANKS];
    
    // 计时器
    logic [9:0] timer [NUM_CHANNELS][NUM_BANKS];
    
    // 命令解码
    wire cmd_act = (cmd == CMD_ACT);
    wire cmd_read = (cmd == CMD_READ);
    wire cmd_write = (cmd == CMD_WRITE);
    wire cmd_pre = (cmd == CMD_PRE);
    wire cmd_ref = (cmd == CMD_REF);
    
    // 内存阵列 (简化的 SRAM 模型)
    logic [255:0] mem_array [NUM_CHANNELS][NUM_BANKS][16'h10000];
    
    // 输出赋值
    assign bank_state = bank_state_r;
    
    // Bank 状态机
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                for (int bk = 0; bk < NUM_BANKS; bk++) begin
                    bank_state_r[ch][bk] <= S_IDLE;
                    timer[ch][bk] <= '0;
                end
            end
        end else begin
            bank_state_r <= bank_state_n;
            // 计时器递减
            for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                for (int bk = 0; bk < NUM_BANKS; bk++) begin
                    if (timer[ch][bk] > 0)
                        timer[ch][bk] <= timer[ch][bk] - 1;
                end
            end
        end
    end
    
    // 状态转移逻辑
    always_comb begin
        bank_state_n = bank_state_r;
        
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            for (int bk = 0; bk < NUM_BANKS; bk++) begin
                case (bank_state_r[ch][bk])
                    S_IDLE: begin
                        if (cmd_act && (ch_id == ch) && (bank_id == bk))
                            bank_state_n[ch][bk] = S_ACTIVE;
                        else if (cmd_ref && (ch_id == ch))
                            bank_state_n[ch][bk] = S_REFRESH;
                    end
                    
                    S_ACTIVE: begin
                        if (cmd_read || cmd_write) begin
                            if ((ch_id == ch) && (bank_id == bk))
                                bank_state_n[ch][bk] = S_BUSY;
                        end else if (cmd_pre) begin
                            if ((ch_id == ch) && (bank_id == bk))
                                bank_state_n[ch][bk] = S_IDLE;
                        end
                    end
                    
                    S_BUSY: begin
                        if (timer[ch][bk] == 0) begin
                            if (cmd_pre)
                                bank_state_n[ch][bk] = S_IDLE;
                            else
                                bank_state_n[ch][bk] = S_ACTIVE;
                        end
                    end
                    
                    S_REFRESH: begin
                        if (timer[ch][bk] == 0)
                            bank_state_n[ch][bk] = S_IDLE;
                    end
                endcase
            end
        end
    end
    
    // 数据读写
    always_ff @(posedge clk) begin
        if (rst_n) begin
            for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                for (int bk = 0; bk < NUM_BANKS; bk++) begin
                    // 写操作
                    if (cmd_write && (ch_id == ch) && (bank_id == bk)) begin
                        mem_array[ch][bk][row_id] <= wr_data;
                    end
                    
                    // 更新计时器
                    if (cmd_read || cmd_write) begin
                        timer[ch][bk] <= tCCD;  // CAS to CAS delay
                    end else if (cmd_pre) begin
                        timer[ch][bk] <= tRP;
                    end else if (cmd_act) begin
                        timer[ch][bk] <= tRCD;
                    end
                end
            end
        end
    end
    
    // 读数据输出
    assign rd_data = mem_array[ch_id][bank_id][row_id];
    
    // 刷新状态
    assign refresh_active = 1'b0;  // 简化实现

endmodule
```

**Step 4: 创建 HBM 控制器 RTL**

```systemverilog
// hbm_controller.sv - HBM 内存控制器
// 实现地址解码、请求队列、FR-FCFS 调度
// 参考 model/controller/controller.py

`timescale 1ns / 1ps
`include "hbm_types.svh"

module hbm_controller #(
    parameter NUM_CHANNELS = 8,
    parameter QUEUE_DEPTH = 32
)(
    input  wire             clk,
    input  wire             rst_n,
    
    // 请求输入
    input  wire            req_valid,
    input  wire [31:0]      req_id,
    input  wire [31:0]      req_addr,
    input  wire             req_rd_wr_n,  // 0=write, 1=read
    input  wire [15:0]      req_len,
    input  wire [2:0]       req_priority,
    
    // 请求就绪
    output wire             req_ready,
    
    // 响应输出
    output wire            resp_valid,
    output wire [31:0]      resp_id,
    output wire             resp_success,
    output wire [7:0]       resp_status,
    
    // DRAM 接口
    output wire [3:0]       dram_cmd,
    output wire [2:0]       dram_ch,
    output wire [3:0]       dram_bank,
    output wire [15:0]      dram_row,
    input  wire [255:0]    dram_rd_data,
    output wire [255:0]     dram_wr_data,
    
    // 状态输出
    output wire [31:0]      stat_requests,
    output wire [31:0]      stat_completed,
    output wire [7:0]       stat_hit_rate
);
    
    // ==================== 地址解码 ====================
    // 地址位分配 (根据 hbm_types.svh):
    // [31:29] - Stack[2:0]
    // [28:26] - Channel[2:0]
    // [25:23] - BankGroup[2:0]
    // [22:19] - Bank[3:0]
    // [18:3]  - Row[15:0]
    // [2:1]   - Col[9:8]
    // [0]     - Reserved
    
    wire [2:0]  addr_stack;
    wire [2:0]  addr_channel;
    wire [2:0]  addr_bank_group;
    wire [3:0]  addr_bank;
    wire [15:0] addr_row;
    wire [9:0]  addr_col;
    
    assign addr_stack      = req_addr[31:29];
    assign addr_channel    = req_addr[28:26];
    assign addr_bank_group = req_addr[25:23];
    assign addr_bank       = req_addr[22:19];
    assign addr_row        = req_addr[18:3];
    assign addr_col        = {req_addr[2:1], 8'b0};
    
    // ==================== 请求队列 ====================
    typedef struct packed {
        logic [31:0]         req_id;
        logic [31:0]         req_addr;
        logic                is_read;
        logic [15:0]         length;
        logic [2:0]          priority;
        logic [15:0]         row;
        logic [3:0]          bank;
        logic [2:0]          channel;
        logic [2:0]          bank_group;
        logic                valid;
        logic [15:0]         age;
    } queue_entry_t;
    
    queue_entry_t request_queue [QUEUE_DEPTH];
    logic [$clog2(QUEUE_DEPTH)-1:0] wr_ptr, rd_ptr;
    logic queue_full, queue_empty;
    
    // 队列写入
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= '0;
            for (int i = 0; i < QUEUE_DEPTH; i++) begin
                request_queue[i].valid <= 1'b0;
            end
        end else if (req_valid && !queue_full) begin
            request_queue[wr_ptr].req_id     <= req_id;
            request_queue[wr_ptr].req_addr   <= req_addr;
            request_queue[wr_ptr].is_read   <= ~req_rd_wr_n;
            request_queue[wr_ptr].length     <= req_len;
            request_queue[wr_ptr].priority   <= req_priority;
            request_queue[wr_ptr].row        <= addr_row;
            request_queue[wr_ptr].bank       <= addr_bank;
            request_queue[wr_ptr].channel     <= addr_channel;
            request_queue[wr_ptr].bank_group <= addr_bank_group;
            request_queue[wr_ptr].valid      <= 1'b1;
            request_queue[wr_ptr].age        <= '0;
            wr_ptr <= wr_ptr + 1;
        end
    end
    
    assign req_ready = ~queue_full;
    assign queue_empty = (rd_ptr == wr_ptr) && !request_queue[wr_ptr].valid;
    assign queue_full = ((wr_ptr + 1) == rd_ptr) || 
                        (request_queue[wr_ptr].valid && (wr_ptr == rd_ptr));
    
    // ==================== FR-FCFS 调度器 ====================
    // 优先级: row_hit > priority > age
    logic [$clog2(QUEUE_DEPTH)-1:0] selected_entry;
    logic selected_valid;
    
    // 简化的 FR-FCFS 选择
    always_comb begin
        selected_entry = rd_ptr;
        selected_valid = 1'b0;
        
        for (int i = 0; i < QUEUE_DEPTH; i++) begin
            if (request_queue[i].valid) begin
                if (!selected_valid) begin
                    selected_entry = i[$clog2(QUEUE_DEPTH)-1:0];
                    selected_valid = 1'b1;
                end else begin
                    // 更高优先级
                    if (request_queue[i].priority > request_queue[selected_entry].priority) begin
                        selected_entry = i[$clog2(QUEUE_DEPTH)-1:0];
                    end
                    // 相同优先级，更老
                    else if ((request_queue[i].priority == request_queue[selected_entry].priority) &&
                             (request_queue[i].age > request_queue[selected_entry].age)) begin
                        selected_entry = i[$clog2(QUEUE_DEPTH)-1:0];
                    end
                end
            end
        end
    end
    
    // ==================== DRAM 命令生成 ====================
    typedef enum logic [2:0] {
        S_IDLE,
        S_ACTIVATE,
        S_READ,
        S_WRITE,
        S_PRECHARGE,
        S_COMPLETE
    } fsm_state_t;
    
    fsm_state_t fsm_state, fsm_next;
    
    logic [2:0]  cur_channel;
    logic [3:0]  cur_bank;
    logic [15:0] cur_row;
    logic [31:0] cur_req_id;
    logic        cur_is_read;
    
    // 状态机
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fsm_state <= S_IDLE;
            rd_ptr <= '0;
        end else begin
            fsm_state <= fsm_next;
            
            // 更新队列读指针
            if ((fsm_state == S_COMPLETE) && (resp_valid))
                rd_ptr <= rd_ptr + 1;
            
            // 年龄递增
            for (int i = 0; i < QUEUE_DEPTH; i++) begin
                if (request_queue[i].valid)
                    request_queue[i].age <= request_queue[i].age + 1;
            end
        end
    end
    
    // 状态转移
    always_comb begin
        fsm_next = fsm_state;
        
        case (fsm_state)
            S_IDLE: begin
                if (selected_valid)
                    fsm_next = S_ACTIVATE;
            end
            
            S_ACTIVATE: begin
                fsm_next = S_READ;  // 简化：直接进入读
            end
            
            S_READ, S_WRITE: begin
                fsm_next = S_PRECHARGE;
            end
            
            S_PRECHARGE: begin
                fsm_next = S_COMPLETE;
            end
            
            S_COMPLETE: begin
                fsm_next = S_IDLE;
            end
            
            default: fsm_next = S_IDLE;
        endcase
    end
    
    // 命令输出
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dram_cmd   <= CMD_NOP;
            dram_ch    <= '0;
            dram_bank  <= '0;
            dram_row   <= '0;
            dram_wr_data <= '0;
        end else begin
            case (fsm_state)
                S_ACTIVATE: begin
                    dram_cmd  <= CMD_ACT;
                    dram_ch   <= request_queue[selected_entry].channel;
                    dram_bank <= request_queue[selected_entry].bank;
                    dram_row  <= request_queue[selected_entry].row;
                end
                
                S_READ: begin
                    dram_cmd <= CMD_READ;
                end
                
                S_WRITE: begin
                    dram_cmd <= CMD_WRITE;
                    dram_wr_data <= 256'hDEADBEEF;  // 测试数据
                end
                
                S_PRECHARGE: begin
                    dram_cmd  <= CMD_PRE;
                end
                
                default: begin
                    dram_cmd <= CMD_NOP;
                end
            endcase
        end
    end
    
    // ==================== 响应生成 ====================
    logic resp_valid_r;
    logic [31:0] resp_id_r;
    logic resp_success_r;
    logic [7:0] resp_status_r;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            resp_valid_r  <= 1'b0;
        end else begin
            resp_valid_r  <= (fsm_state == S_COMPLETE);
            resp_id_r     <= request_queue[selected_entry].req_id;
            resp_success_r <= 1'b1;
            resp_status_r <= 8'h0;
        end
    end
    
    assign resp_valid   = resp_valid_r;
    assign resp_id      = resp_id_r;
    assign resp_success = resp_success_r;
    assign resp_status  = resp_status_r;
    
    // ==================== 统计 ====================
    logic [31:0] req_count, comp_count;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            req_count   <= '0;
            comp_count  <= '0;
        end else begin
            if (req_valid && req_ready)
                req_count <= req_count + 1;
            if (resp_valid)
                comp_count <= comp_count + 1;
        end
    end
    
    assign stat_requests = req_count;
    assign stat_completed = comp_count;
    assign stat_hit_rate = 8'd50;  // 简化

endmodule
```

**Step 5: 创建测试平台**

```systemverilog
// hbm_controller_tb.sv - 控制器测试平台
// 验证基本功能和时序

`timescale 1ns / 1ps
`include "hbm_types.svh"

module hbm_controller_tb;
    
    reg         clk = 0;
    reg         rst_n = 0;
    
    // 请求接口
    reg         req_valid = 0;
    reg  [31:0] req_id = 0;
    reg  [31:0] req_addr = 0;
    reg         req_rd_wr_n = 1;
    reg  [15:0] req_len = 64;
    reg  [2:0]  req_priority = 0;
    wire        req_ready;
    
    // 响应接口
    wire        resp_valid;
    wire [31:0] resp_id;
    wire        resp_success;
    wire [7:0]  resp_status;
    
    // DRAM 接口
    wire [3:0]  dram_cmd;
    wire [2:0]  dram_ch;
    wire [3:0]  dram_bank;
    wire [15:0] dram_row;
    wire [255:0] dram_wr_data;
    wire [255:0] dram_rd_data;
    
    // 状态
    wire [31:0] stat_requests;
    wire [31:0] stat_completed;
    wire [7:0]  stat_hit_rate;
    
    // 时钟生成
    always #390 clk = ~clk;  // 781ps period @ 1.28GHz
    
    // DUT
    hbm_controller #(
        .NUM_CHANNELS(8),
        .QUEUE_DEPTH(32)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .req_valid(req_valid),
        .req_id(req_id),
        .req_addr(req_addr),
        .req_rd_wr_n(req_rd_wr_n),
        .req_len(req_len),
        .req_priority(req_priority),
        .req_ready(req_ready),
        .resp_valid(resp_valid),
        .resp_id(resp_id),
        .resp_success(resp_success),
        .resp_status(resp_status),
        .dram_cmd(dram_cmd),
        .dram_ch(dram_ch),
        .dram_bank(dram_bank),
        .dram_row(dram_row),
        .dram_rd_data(dram_rd_data),
        .dram_wr_data(dram_wr_data),
        .stat_requests(stat_requests),
        .stat_completed(stat_completed),
        .stat_hit_rate(stat_hit_rate)
    );
    
    // 内存模型
    wire [2:0] bank_state [8][16];
    dram_model #(
        .STACK_ID(0),
        .NUM_CHANNELS(8),
        .NUM_BANKS(16)
    ) dram (
        .clk(clk),
        .rst_n(rst_n),
        .cmd(dram_cmd),
        .ch_id(dram_ch),
        .bank_id(dram_bank),
        .row_id(dram_row),
        .wr_data(dram_wr_data),
        .rd_data(dram_rd_data),
        .bank_state(bank_state),
        .refresh_active(),
        .tRCD(9'd17),
        .tRP(9'd17),
        .tRAS(9'd42),
        .tRC(9'd59)
    );
    
    // 测试过程
    initial begin
        $display("=== HBM Controller TB Start ===");
        
        // 复位
        rst_n = 0;
        repeat(10) @(posedge clk);
        rst_n = 1;
        repeat(5) @(posedge clk);
        
        // 测试1: 单个读请求
        $display("[Test 1] Single Read Request");
        @(posedge clk);
        req_valid = 1;
        req_id = 32'h1;
        req_addr = 32'h0001_0000;  // Channel 0, Bank 0
        req_rd_wr_n = 1;
        req_len = 64;
        req_priority = 3'd5;
        
        @(posedge clk);
        while (!req_ready) @(posedge clk);
        req_valid = 0;
        
        // 等待完成
        repeat(100) @(posedge clk);
        
        // 测试2: 多个请求
        $display("[Test 2] Multiple Requests");
        repeat(5) begin
            @(posedge clk);
            if (req_ready) begin
                req_valid = 1;
                req_id = req_id + 1;
                req_addr = req_addr + 32'h1000;
                req_rd_wr_n = $random;
            end
        end
        req_valid = 0;
        
        repeat(200) @(posedge clk);
        
        $display("=== HBM Controller TB Complete ===");
        $display("Requests: %d, Completed: %d", stat_requests, stat_completed);
        $finish;
    end
    
    // 波形保存
    initial begin
        $dumpfile("hbm_controller_tb.vcd");
        $dumpvars(0, hbm_controller_tb);
    end

endmodule
```

**Step 6: 编译和运行测试**

Run: `cd rtl && verilator --cc --exe --build hbm_controller_tb.sv hbm_controller.sv dram_model.sv hbm_pkg.sv 2>&1`
Expected: 编译成功

**Step 7: 提交**

```bash
git add rtl/
git commit -m "feat: add HBM RTL implementation (controller + dram model)"
```

---

## C. UVM 验证环境

### Task C.1: 创建 UVM 验证框架

**Files:**
- Create: `verification/uvm/hbm_env.sv`
- Create: `verification/uvm/hbm_sequence.sv`
- Create: `verification/uvm/hbm_driver.sv`
- Create: `verification/uvm/hbm_monitor.sv`
- Create: `verification/uvm/hbm_scoreboard.sv`
- Create: `verification/uvm/hbm_test.sv`
- Create: `verification/uvm/Makefile`

**Step 1: 创建 UVM 环境**

```systemverilog
// hbm_env.sv - UVM 验证环境
// 基于 hbm_pkg.sv 构建完整的验证环境

`timescale 1ns / 1ps
`include "hbm_types.svh"

package hbm_env_pkg;
    import uvm_pkg::*;
    import hbm_pkg::*;
    
    // 虚拟接口定义
    interface hbm_if (
        input logic clk,
        input logic rst_n
    );
        // 请求通道
        logic        req_valid;
        logic [31:0] req_id;
        logic [31:0] req_addr;
        logic        req_rd_wr_n;
        logic [15:0] req_len;
        logic [2:0]  req_priority;
        logic        req_ready;
        
        // 响应通道
        logic        resp_valid;
        logic [31:0] resp_id;
        logic        resp_success;
        logic [7:0]  resp_status;
        
        // DRAM 接口
        logic [3:0]  dram_cmd;
        logic [2:0]  dram_ch;
        logic [3:0]  dram_bank;
        logic [15:0] dram_row;
        logic [255:0] dram_rd_data;
        logic [255:0] dram_wr_data;
        
        // 时钟接口
        clocking cb @(posedge clk);
            default input #1step output #0;
            output req_valid, req_id, req_addr, req_rd_wr_n, req_len, req_priority;
            input  req_ready;
            input  resp_valid, resp_id, resp_success, resp_status;
            output dram_cmd, dram_ch, dram_bank, dram_row, dram_wr_data;
            input  dram_rd_data;
        endclocking
    endinterface
    
    // Agent 配置
    class hbm_agent_config extends uvm_object;
        `uvm_object_utils(hbm_agent_config)
        
        bit is_active = 1;
        bit has_driver = 1;
        bit has_monitor = 1;
        
        function new(string name = "hbm_agent_config");
            super.new(name);
        endfunction
    endclass
    
    // Driver
    class hbm_driver extends uvm_driver #(hbm_transaction);
        `uvm_component_utils(hbm_driver)
        
        hbm_agent_config cfg;
        virtual hbm_if vif;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual hbm_if)::get(this, "", "vif", vif))
                `uvm_fatal("NOVIF", "Virtual interface not set");
        endfunction
        
        task run_phase(uvm_phase phase);
            forever begin
                seq_item_port.get_next_item(req);
                drive_request(req);
                seq_item_port.item_done();
            end
        endtask
        
        task drive_request(hbm_transaction req);
            @(vif.cb);
            vif.cb.req_valid <= 1;
            vif.cb.req_id <= req.req_id;
            vif.cb.req_addr <= {req.addr.stack, req.addr.channel, 
                               req.addr.bank_group, req.addr.bank,
                               req.addr.row, 10'b0};
            vif.cb.req_rd_wr_n <= (req.req_type == REQ_READ);
            vif.cb.req_len <= req.length;
            vif.cb.req_priority <= req.priority;
            
            @(vif.cb);
            while (!vif.cb.req_ready)
                @(vif.cb);
            vif.cb.req_valid <= 0;
        endtask
    endclass
    
    // Monitor
    class hbm_monitor extends uvm_monitor;
        `uvm_component_utils(hbm_monitor)
        
        uvm_analysis_port #(hbm_transaction) item_collected_port;
        virtual hbm_if vif;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
            item_collected_port = new("item_collected_port", this);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual hbm_if)::get(this, "", "vif", vif))
                `uvm_fatal("NOVIF", "Virtual interface not set");
        endfunction
        
        task run_phase(uvm_phase phase);
            super.run_phase(phase);
            forever begin
                @(vif.cb);
                if (vif.req_valid && vif.req_ready) begin
                    collect_request();
                end
                if (vif.resp_valid) begin
                    collect_response();
                end
            end
        endtask
        
        task collect_request();
            hbm_transaction tr;
            tr = hbm_transaction::type_id::create("tr");
            tr.req_id = vif.req_id;
            tr.req_type = vif.req_rd_wr_n ? REQ_READ : REQ_WRITE;
            tr.length = vif.req_len;
            tr.priority = vif.req_priority;
            item_collected_port.write(tr);
        endtask
        
        task collect_response();
            // 实现响应收集
        endtask
    endclass
    
    // Sequencer
    typedef uvm_sequencer #(hbm_transaction) hbm_sequencer;
    
    // Agent
    class hbm_agent extends uvm_agent;
        `uvm_component_utils(hbm_agent)
        
        hbm_agent_config cfg;
        hbm_driver drv;
        hbm_monitor mon;
        hbm_sequencer seqr;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            cfg = hbm_agent_config::type_id::create("cfg");
            
            if (cfg.is_active && cfg.has_driver) begin
                drv = hbm_driver::type_id::create("drv", this);
            end
            if (cfg.has_monitor) begin
                mon = hbm_monitor::type_id::create("mon", this);
            end
            if (cfg.is_active) begin
                seqr = hbm_sequencer::type_id::create("seqr", this);
            end
        endfunction
        
        function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            if (cfg.is_active && cfg.has_driver) begin
                drv.seq_item_port.connect(seqr.seq_item_export);
            end
        endfunction
    endclass
    
    // Scoreboard
    class hbm_scoreboard extends uvm_scoreboard;
        `uvm_component_utils(hbm_scoreboard)
        
        uvm_analysis_export #(hbm_transaction) req_export;
        uvm_analysis_export #(hbm_transaction) resp_export;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
            req_export = new("req_export", this);
            resp_export = new("resp_export", this);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
        endfunction
        
        function void write_req(hbm_transaction t);
            `uvm_info("SCO", $sformatf("Received request: %s", t.convert2str()), UVM_MEDIUM);
        endfunction
        
        function void write_resp(hbm_transaction t);
            `uvm_info("SCO", $sformatf("Received response: %s", t.convert2str()), UVM_MEDIUM);
        endfunction
    endclass
    
    // Environment
    class hbm_env extends uvm_env;
        `uvm_component_utils(hbm_env)
        
        hbm_agent agent;
        hbm_scoreboard scb;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            agent = hbm_agent::type_id::create("agent", this);
            scb = hbm_scoreboard::type_id::create("scb", this);
        endfunction
        
        function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.mon.item_collected_port.connect(scb.req_export);
        endfunction
    endclass

endpackage
```

**Step 2: 创建测试用例**

```systemverilog
// hbm_test.sv - UVM 测试用例
// 包含基本测试和随机测试

`timescale 1ns / 1ps
`include "hbm_types.svh"

module hbm_test_pkg;
    import uvm_pkg::*;
    import hbm_env_pkg::*;
    import hbm_pkg::*;
    
    // 基本序列
    class single_read_seq extends uvm_sequence #(hbm_transaction);
        `uvm_object_utils(single_read_seq)
        
        function new(string name = "single_read_seq");
            super.new(name);
        endfunction
        
        task body();
            hbm_transaction req;
            req = hbm_transaction::type_id::create("req");
            start_item(req);
            assert(req.randomize() with {
                req.req_type == REQ_READ;
                req.addr.channel == 0;
                req.addr.bank == 0;
            });
            finish_item(req);
        endtask
    endclass
    
    // 随机序列
    class random_traffic_seq extends uvm_sequence #(hbm_transaction);
        `uvm_object_utils(random_traffic_seq)
        
        int num_requests = 100;
        
        function new(string name = "random_traffic_seq");
            super.new(name);
        endfunction
        
        task body();
            for (int i = 0; i < num_requests; i++) begin
                hbm_transaction req;
                req = hbm_transaction::type_id::create("req");
                start_item(req);
                assert(req.randomize());
                finish_item(req);
                #100;
            end
        endtask
    endclass
    
    // 热点访问序列
    class hotspot_seq extends uvm_sequence #(hbm_transaction);
        `uvm_object_utils(hotspot_seq)
        
        int num_requests = 100;
        
        function new(string name = "hotspot_seq");
            super.new(name);
        endfunction
        
        task body();
            for (int i = 0; i < num_requests; i++) begin
                hbm_transaction req;
                req = hbm_transaction::type_id::create("req");
                start_item(req);
                assert(req.randomize() with {
                    req.addr.bank == 0;
                    req.addr.row inside {[0:15]};
                });
                finish_item(req);
            end
        endtask
    endclass
    
    // 测试用例
    class hbm_base_test extends uvm_test;
        `uvm_component_utils(hbm_base_test)
        
        hbm_env env;
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            env = hbm_env::type_id::create("env", this);
            
            // 设置配置
            uvm_config_db#(hbm_configuration)::set(this, "env.agent", "cfg", 
                hbm_configuration::type_id::create("cfg"));
        endfunction
        
        function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            `uvm_info("TEST", "Test environment built", UVM_MEDIUM);
        endfunction
        
        task run_phase(uvm_phase phase);
            super.run_phase(phase);
        endtask
    endclass
    
    class hbm_random_test extends hbm_base_test;
        `uvm_component_utils(hbm_random_test)
        
        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
        
        task run_phase(uvm_phase phase);
            random_traffic_seq seq;
            phase.raise_objection(this);
            begin
                seq = random_traffic_seq::type_id::create("seq");
                fork
                    seq.start(env.agent.seqr);
                join_none
                #10us;
            end
            phase.drop_objection(this);
        endtask
    endclass

endmodule
```

**Step 3: 创建 Makefile**

```makefile
# verification/uvm/Makefile

UVM_HOME ?= /usr/share/questasim/uvm-1.2
WORK = work

.SILENT:

all: comp run

comp:
    vlog -work $(WORK) \
        -f uvm.f \
        +incdir+../../rtl \
        ../../rtl/hbm_types.svh \
        ../../rtl/hbm_pkg.sv \
        hbm_env_pkg.sv \
        hbm_test_pkg.sv

run: comp
    vsim -c -do "run -all; quit" \
        -L $(WORK) \
        work.hbm_random_test

clean:
    rm -rf $(WORK) *.vcd *.log

.PHONY: all comp run clean
```

**Step 4: 创建文件列表**

```text
# verification/uvm/uvm.f
+incdir+../../
../../rtl/hbm_types.svh
../../rtl/hbm_pkg.sv
hbm_env_pkg.sv
hbm_test_pkg.sv
hbm_tb.sv
```

**Step 5: 提交**

```bash
git add verification/uvm/
git commit -m "feat: add UVM verification environment"
```

---

## D. 参考模型

### Task D.1: 创建性能参考模型

**Files:**
- Create: `verification/reference_model/dram_ref_model.sv`
- Create: `verification/reference_model/addr_decoder_ref.sv`
- Create: `verification/reference_model/timing_checker.sv`
- Create: `verification/reference_model/bandwidth_calc.sv`

**Step 1: 创建 DRAM 参考模型**

```systemverilog
// dram_ref_model.sv - DRAM 性能参考模型
// 用于与 RTL 实现对比验证
// 参考 model/dram/dram_model.py

`timescale 1ns / 1ps
`include "hbm_types.svh"

module dram_ref_model #(
    parameter NUM_BANKS = 16,
    parameter ROW_DEPTH = 65536
)(
    input  logic              clk,
    input  logic              rst_n,
    
    // 命令接口
    input  logic [3:0]        cmd,
    input  logic [3:0]        bank_id,
    input  logic [15:0]       row_id,
    
    // 数据接口
    input  logic [255:0]      wr_data,
    output logic [255:0]      rd_data,
    
    // 性能统计
    output logic [31:0]       stat_act_count,
    output logic [31:0]       stat_read_count,
    output logic [31:0]       stat_write_count,
    output logic [31:0]       stat_row_hits,
    output logic [31:0]       stat_row_misses,
    output real               stat_avg_latency
);
    
    // Bank 状态
    typedef struct {
        logic [2:0]  state;
        logic [15:0] open_row;
        logic [9:0]  timer;
    } bank_info_t;
    
    bank_info_t banks [NUM_BANKS];
    
    // 内存阵列
    logic [255:0] mem [NUM_BANKS][ROW_DEPTH];
    
    // 统计计数器
    logic [31:0] act_count, read_count, write_count;
    logic [31:0] hit_count, miss_count;
    logic [63:0] total_latency;
    logic [31:0] completed_count;
    
    // 命令解码
    logic cmd_act   = (cmd == CMD_ACT);
    logic cmd_read  = (cmd == CMD_READ);
    logic cmd_write = (cmd == CMD_WRITE);
    logic cmd_pre   = (cmd == CMD_PRE);
    
    // Bank 状态更新
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int b = 0; b < NUM_BANKS; b++) begin
                banks[b].state <= 3'b000;
                banks[b].open_row <= '0;
                banks[b].timer <= '0;
            end
            act_count <= '0;
            read_count <= '0;
            write_count <= '0;
            hit_count <= '0;
            miss_count <= '0;
            total_latency <= '0;
            completed_count <= '0;
        end else begin
            // 处理命令
            if (cmd_act && banks[bank_id].state == 3'b000) begin
                banks[bank_id].state <= 3'b001;  // ACTIVE
                banks[bank_id].open_row <= row_id;
                banks[bank_id].timer <= 9'd17;    // tRCD
                act_count <= act_count + 1;
            end
            
            if ((cmd_read || cmd_write) && banks[bank_id].state == 3'b001) begin
                banks[bank_id].state <= 3'b010;  // BUSY
                banks[bank_id].timer <= 9'd5;     // tCCD
                
                if (cmd_read) begin
                    read_count <= read_count + 1;
                end else begin
                    write_count <= write_count + 1;
                end
                
                // 行命中/未命中统计
                if (banks[bank_id].open_row == row_id) begin
                    hit_count <= hit_count + 1;
                end else begin
                    miss_count <= miss_count + 1;
                end
            end
            
            if (cmd_pre) begin
                banks[bank_id].state <= 3'b000;  // IDLE
                banks[bank_id].timer <= 9'd17;   // tRP
            end
            
            // 计时器递减
            for (int b = 0; b < NUM_BANKS; b++) begin
                if (banks[b].timer > 0) begin
                    banks[b].timer <= banks[b].timer - 1;
                end
                if (banks[b].timer == 1) begin
                    banks[b].state <= 3'b001;  // 返回 ACTIVE
                end
            end
            
            // 更新延迟统计
            if (cmd_read || cmd_write) begin
                total_latency <= total_latency + 32;
                completed_count <= completed_count + 1;
            end
        end
    end
    
    // 内存访问
    always_ff @(posedge clk) begin
        if (cmd_write && banks[bank_id].state != 3'b000) begin
            mem[bank_id][row_id] <= wr_data;
        end
        rd_data <= mem[bank_id][row_id];
    end
    
    // 统计输出
    assign stat_act_count = act_count;
    assign stat_read_count = read_count;
    assign stat_write_count = write_count;
    assign stat_row_hits = hit_count;
    assign stat_row_misses = miss_count;
    assign stat_avg_latency = completed_count > 0 ? 
                              real'(total_latency) / real'(completed_count) : 0.0;

endmodule
```

**Step 2: 创建地址解码器参考模型**

```systemverilog
// addr_decoder_ref.sv - 地址解码器参考模型
// 实现多种地址映射方案
// 参考 model/controller/address_decoder.py

`timescale 1ns / 1ps
`include "hbm_types.svh"

module addr_decoder_ref (
    input  logic [31:0]  addr_in,
    input  logic [2:0]  mapping_mode,  // 0=RBC, 1=BCR, 2=CRB
    
    output logic [2:0]  stack,
    output logic [2:0]  channel,
    output logic [2:0]  bank_group,
    output logic [3:0]  bank,
    output logic [15:0] row,
    output logic [9:0]   col
);
    
    // RBC 映射 (Row-Bank-Channel) - 默认
    // [31:29] Stack [28:26] Channel [25:23] BankGroup [22:19] Bank [18:3] Row [2:0] Col
    logic [2:0]  stack_rbc, channel_rbc, bg_rbc;
    logic [3:0]  bank_rbc;
    logic [15:0] row_rbc;
    logic [9:0]  col_rbc;
    
    assign stack_rbc     = addr_in[31:29];
    assign channel_rbc   = addr_in[28:26];
    assign bg_rbc        = addr_in[25:23];
    assign bank_rbc      = addr_in[22:19];
    assign row_rbc       = addr_in[18:3];
    assign col_rbc       = {addr_in[2:0], 7'b0};
    
    // BCR 映射 (Bank-Channel-Row)
    // 交换 bank 和 channel
    logic [2:0]  stack_bcr, channel_bcr, bg_bcr;
    logic [3:0]  bank_bcr;
    logic [15:0] row_bcr;
    logic [9:0]  col_bcr;
    
    assign stack_bcr     = addr_in[31:29];
    assign bank_bcr      = addr_in[28:25];
    assign channel_bcr   = {addr_in[24:22]};
    assign bg_bcr        = addr_in[21:19];
    assign row_bcr       = addr_in[18:3];
    assign col_bcr       = {addr_in[2:0], 7'b0};
    
    // 选择输出
    always_comb begin
        case (mapping_mode)
            3'd0: begin  // RBC
                stack = stack_rbc;
                channel = channel_rbc;
                bank_group = bg_rbc;
                bank = bank_rbc;
                row = row_rbc;
                col = col_rbc;
            end
            3'd1: begin  // BCR
                stack = stack_bcr;
                channel = channel_bcr;
                bank_group = bg_bcr;
                bank = bank_bcr;
                row = row_bcr;
                col = col_bcr;
            end
            default: begin  // RBC
                stack = stack_rbc;
                channel = channel_rbc;
                bank_group = bg_rbc;
                bank = bank_rbc;
                row = row_rbc;
                col = col_rbc;
            end
        endcase
    end

endmodule
```

**Step 3: 创建带宽计算器**

```systemverilog
// bandwidth_calc.sv - 带宽计算参考模型
// 实时计算 HBM 带宽利用率

`timescale 1ns / 1ps

module bandwidth_calc #(
    parameter WINDOW_SIZE = 1000  // 统计窗口大小
)(
    input  logic        clk,
    input  logic        rst_n,
    
    input  logic        data_valid,
    input  logic [15:0] data_bytes,
    
    output real         bandwidth_gbps,
    output real         efficiency_pct
);
    
    // 参数
    localparam REAL_CLK_FREQ = 1.28e9;  // 1.28 GHz
    localparam BUS_WIDTH = 1024;          // 1024 bits
    localparam PEAK_BW = REAL_CLK_FREQ * BUS_WIDTH / 1e9;  // GB/s
    
    // 滑动窗口计数
    logic [31:0] window_count;
    logic [31:0] total_bytes_window;
    logic [15:0] window_index;
    
    // 计算
    real current_bw;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            window_count <= '0;
            total_bytes_window <= '0;
            window_index <= '0;
        end else begin
            if (data_valid) begin
                total_bytes_window <= total_bytes_window + data_bytes;
                window_count <= window_count + 1;
            end
            
            // 窗口更新
            window_index <= window_index + 1;
            if (window_index >= WINDOW_SIZE) begin
                window_index <= '0;
                window_count <= '0;
                total_bytes_window <= '0;
            end
        end
    end
    
    // 计算带宽
    real window_us;
    always_comb begin
        window_us = real'(window_index) * 781.25 / 1e6;  // 假设 781.25ps 周期
        if (window_us > 0) begin
            current_bw = real'(total_bytes_window) / window_us / 1e3;  // GB/s
        end else begin
            current_bw = 0.0;
        end
    end
    
    assign bandwidth_gbps = current_bw;
    assign efficiency_pct = (current_bw / PEAK_BW) * 100.0;

endmodule
```

**Step 4: 提交**

```bash
git add verification/reference_model/
git commit -m "feat: add HBM reference models for verification"
```

---

## 验证步骤

### Python 基准测试
```bash
cd /home/ic/JXTF/HBM
python3 sim/benchmark.py
```

### RTL 仿真
```bash
cd /home/ic/JXTF/HBM/rtl
verilator --cc --exe --build hbm_controller_tb.sv hbm_controller.sv dram_model.sv
./obj_dir/hbm_controller_tb
```

### UVM 验证
```bash
cd /home/ic/JXTF/HBM/verification/uvm
make
```

---

## 预期结果

| 模块 | 验证方式 | 预期结果 |
|------|----------|----------|
| A. 基准测试 | Python | 4 种流量模式 × 4 种请求率测试通过 |
| B. RTL | Verilator | 控制器 + DRAM 模型编译通过 |
| C. UVM | Questa/ModelSim | 验证环境构建成功 |
| D. 参考模型 | 对比仿真 | 与 Python 模型结果一致 |