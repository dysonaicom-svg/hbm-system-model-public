#!/bin/bash
# RTL 仿真基准测试脚本
# 用法: ./scripts/run_rtl_benchmark.sh [--sim-only | --model-only | --compare]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RTL_DIR="$PROJECT_DIR/rtl"

show_help() {
    echo "HBM RTL 仿真基准测试"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --sim-only     仅运行 RTL 仿真"
    echo "  --model-only   仅运行 Model 仿真"
    echo "  --compare     对比 RTL 和 Model"
    echo "  --quick       快速测试 (10us)"
    echo "  --full        完整测试 (100us)"
    echo "  -h, --help     显示帮助"
}

MODE="compare"
TIME="10us"

while [[ $# -gt 0 ]]; do
    case $1 in
        --sim-only) MODE="sim"; shift ;;
        --model-only) MODE="model"; shift ;;
        --compare) MODE="compare"; shift ;;
        --quick) TIME="10us"; shift ;;
        --full) TIME="100us"; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "未知选项: $1"; show_help; exit 1 ;;
    esac
done

echo "模式: $MODE, 时间: $TIME"

# RTL 仿真
run_rtl_sim() {
    echo "=== 运行 RTL 仿真 ==="
    cd "$RTL_DIR"
    make clean 2>/dev/null || true
    make sim SIM_TIME="$TIME" 2>&1 | tee logs/rtl_sim.log
}

# Model 仿真
run_model_sim() {
    echo "=== 运行 Model 仿真 ==="
    cd "$PROJECT_DIR"
    python3 -c "
from sim.simulator import SimulationConfig, HBMSimulator, TrafficPattern
config = SimulationConfig(
    simulation_time_us=10.0,
    traffic_pattern=TrafficPattern.RANDOM,
    request_rate=0.9,
    read_ratio=0.7,
    seed=42
)
sim = HBMSimulator(config)
stats = sim.run()
print(f'Reults: completed={stats.completed_requests}, throughput={stats.throughput_gbps:.2f} GB/s, row_hit_rate={stats.row_hit_rate:.2%}')
"
}

case $MODE in
    sim) run_rtl_sim ;;
    model) run_model_sim ;;
    compare) 
        run_model_sim
        run_rtl_sim
        echo "=== 对比完成 ==="
        ;;
esac

echo "完成!"
