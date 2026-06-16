#!/bin/bash
# =============================================================================
# HBM System CI Test Script
# 运行所有测试并生成报告
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_header() {
    echo -e "\n${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 检查 Python 版本
check_python() {
    print_header "Checking Python version"

    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo "Python version: $python_version"

    if [[ $(python3 -c 'import sys; print(sys.version_info >= (3, 8))') != "True" ]]; then
        print_error "Python 3.8+ required"
        exit 1
    fi
    print_success "Python version check passed"
}

# 检查依赖
check_dependencies() {
    print_header "Checking dependencies"

    if [ -f requirements.txt ]; then
        echo "Installing core dependencies..."
        # 只安装核心依赖（跳过可选的 systemverilog-parser）
        pip3 install numpy scipy pyyaml pytest pytest-cov matplotlib plotly python-json-logger -q 2>/dev/null || true
        print_success "Dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi
}

# 运行单元测试
run_unit_tests() {
    print_header "Running Unit Tests"

    echo "Running all tests..."
    PYTHONPATH=. pytest tests/ -v --tb=short -q

    if [ $? -eq 0 ]; then
        print_success "All unit tests passed"
    else
        print_error "Some unit tests failed"
        exit 1
    fi
}

# 运行集成测试
run_integration_tests() {
    print_header "Running Integration Tests"

    echo "Running integration tests..."
    PYTHONPATH=. pytest tests/integration/ -v --tb=short

    if [ $? -eq 0 ]; then
        print_success "All integration tests passed"
    else
        print_error "Some integration tests failed"
        exit 1
    fi
}

# 运行回归测试
run_regression_tests() {
    print_header "Running Regression Tests"

    echo "Running regression tests..."
    PYTHONPATH=. pytest tests/regression/ -v --tb=short

    if [ $? -eq 0 ]; then
        print_success "All regression tests passed"
    else
        print_error "Some regression tests failed"
        exit 1
    fi
}

# 运行性能基准测试
run_benchmark() {
    print_header "Running Performance Benchmark"

    echo "Running benchmark suite..."
    PYTHONPATH=. python3 -m sim.benchmark

    if [ $? -eq 0 ]; then
        print_success "Benchmark completed"
    else
        print_error "Benchmark failed"
        exit 1
    fi
}

# 生成测试报告
generate_reports() {
    print_header "Generating Reports"

    # 确保结果目录存在
    mkdir -p sim/results

    # 检查报告文件
    if [ -f "sim/results/report.html" ]; then
        print_success "HTML report generated: sim/results/report.html"
    fi

    if [ -f "sim/results/benchmark_report.html" ]; then
        print_success "Benchmark report generated: sim/results/benchmark_report.html"
    fi

    if [ -f "sim/benchmark_results.json" ]; then
        print_success "JSON results saved: sim/benchmark_results.json"
    fi
}

# 主函数
main() {
    print_header "HBM System CI Test Suite"

    echo "Starting CI tests..."
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    check_python
    check_dependencies
    run_unit_tests
    run_integration_tests
    run_regression_tests
    run_benchmark
    generate_reports

    print_header "CI Test Summary"
    print_success "All tests passed!"
    echo ""
    echo "Test results and reports available in:"
    echo "  - sim/benchmark_results.json"
    echo "  - sim/results/report.html"
    echo "  - sim/results/benchmark_report.html"
    echo ""
}

# 运行主函数
main "$@"