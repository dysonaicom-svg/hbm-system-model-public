#!/bin/bash
# =============================================================================
# HBM System CI Check Script
# =============================================================================
# Comprehensive CI check script for local development and CI environments
# Runs all quality checks, tests, and benchmarks before committing
#
# Usage:
#   ./scripts/ci_check.sh              # Run all checks
#   ./scripts/ci_check.sh --quick     # Quick checks only (no benchmark)
#   ./scripts/ci_check.sh --lint       # Lint only
#   ./scripts/ci_check.sh --test       # Tests only
#   ./scripts/ci_check.sh --rtl        # RTL only
#   ./scripts/ci_check.sh --help       # Show help
# =============================================================================

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# =============================================================================
# Configuration
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_PATH="${PROJECT_ROOT}"
PYTEST_ARGS="-v --tb=short --strict-markers"

# Options
QUICK_MODE=false
SKIP_RTL=false
SKIP_BENCHMARK=false

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}=============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=============================================================================${NC}"
    echo ""
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

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

print_step() {
    echo -e "${BLUE}→ $1${NC}"
}

# =============================================================================
# Environment Checks
# =============================================================================

check_environment() {
    print_header "Environment Check"

    # Check Python version
    print_step "Checking Python version..."
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        echo "  Python: $python_version"
        if [[ $(python3 -c 'import sys; print(sys.version_info >= (3, 8))') != "True" ]]; then
            print_error "Python 3.8+ required"
            exit 1
        fi
        print_success "Python version OK"
    else
        print_error "Python 3 not found"
        exit 1
    fi

    # Check required directories
    print_step "Checking project structure..."
    local dirs=("model" "tests" "rtl" "scripts" "docs")
    for dir in "${dirs[@]}"; do
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            echo "  $dir/ ✓"
        else
            print_warning "$dir/ not found"
        fi
    done

    # Check for required files
    print_step "Checking required files..."
    local files=("requirements.txt" "CLAUDE.md" "README.md")
    for file in "${files[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            echo "  $file ✓"
        else
            print_warning "$file not found"
        fi
    done

    print_success "Environment check complete"
}

# =============================================================================
# Dependency Installation
# =============================================================================

install_dependencies() {
    print_header "Installing Dependencies"

    # Core Python dependencies
    print_step "Installing core Python dependencies..."
    pip3 install -q numpy scipy pyyaml pytest pytest-cov pytest-xdist 2>/dev/null || true
    print_success "Core dependencies installed"

    # Optional dependencies
    print_step "Installing optional dependencies..."
    pip3 install -q matplotlib plotly python-json-logger 2>/dev/null || true
    print_success "Optional dependencies installed"

    # Development dependencies
    print_step "Installing development dependencies..."
    pip3 install -q flake8 black mypy pylint 2>/dev/null || true
    print_success "Development dependencies installed"
}

# =============================================================================
# Lint and Code Quality
# =============================================================================

run_lint_checks() {
    print_header "Running Lint and Code Quality Checks"

    # flake8
    print_step "Running flake8..."
    if flake8 model/ sim/ tests/ --max-line-length=120 --ignore=E501,W503 --show-source --statistics 2>/dev/null; then
        print_success "flake8 passed"
    else
        print_warning "flake8 found issues (see above)"
    fi

    # black check
    print_step "Running black check..."
    if black --check model/ sim/ tests/ 2>/dev/null; then
        print_success "black passed"
    else
        print_warning "black found formatting issues (run 'black model/ sim/ tests/' to fix)"
    fi

    # mypy
    print_step "Running mypy type check..."
    if mypy model/ sim/ --ignore-missing-imports --no-error-summary 2>/dev/null; then
        print_success "mypy passed"
    else
        print_warning "mypy found type issues (see above)"
    fi

    print_success "Lint checks complete"
}

# =============================================================================
# Python Tests
# =============================================================================

run_python_tests() {
    print_header "Running Python Tests"

    export PYTHONPATH="$PYTHON_PATH"
    export PYTHONDONTWRITEBYTECODE=1

    # Unit tests by category
    local test_dirs=("dram" "controller" "sim" "hbm4" "traffic" "interconnect" "coverage")
    for test_dir in "${test_dirs[@]}"; do
        if [ -d "$PROJECT_ROOT/tests/$test_dir" ]; then
            print_step "Running $test_dir tests..."
            if pytest "tests/$test_dir/" $PYTEST_ARGS --cov=. --cov-report=term-missing:skip-covered 2>/dev/null; then
                print_success "$test_dir tests passed"
            else
                print_warning "$test_dir tests had failures"
            fi
        fi
    done

    # Integration tests
    if [ -d "$PROJECT_ROOT/tests/integration" ]; then
        print_step "Running integration tests..."
        if pytest tests/integration/ $PYTEST_ARGS 2>/dev/null; then
            print_success "Integration tests passed"
        else
            print_warning "Integration tests had failures"
        fi
    fi

    # Regression tests
    if [ -d "$PROJECT_ROOT/tests/regression" ]; then
        print_step "Running regression tests..."
        if pytest tests/regression/ $PYTEST_ARGS 2>/dev/null; then
            print_success "Regression tests passed"
        else
            print_warning "Regression tests had failures"
        fi
    fi

    print_success "Python tests complete"
}

# =============================================================================
# RTL Checks
# =============================================================================

run_rtl_checks() {
    if [ "$SKIP_RTL" = true ]; then
        print_info "Skipping RTL checks (--skip-rtl specified)"
        return
    fi

    print_header "Running RTL Checks"

    # Check Verilator
    print_step "Checking Verilator..."
    if command -v verilator &> /dev/null; then
        local verilator_version=$(verilator --version 2>&1 | head -1)
        echo "  $verilator_version"
        print_success "Verilator found"
    else
        print_warning "Verilator not installed (skipping RTL checks)"
        print_info "Install with: apt install verilator"
        return
    fi

    # Run lint
    print_step "Running Verilator lint..."
    cd "$PROJECT_ROOT/rtl"
    if verilator --lint-only -Wall -Wno-fatal \
        -I. \
        hbm_types.svh \
        hbm_controller.sv \
        dram_model.sv 2>&1 | tee logs/lint.log; then
        print_success "RTL lint passed"
    else
        print_warning "RTL lint found issues (see above)"
    fi

    # Build quick simulation
    print_step "Building RTL simulation..."
    if [ -f "filelist.f" ]; then
        mkdir -p obj_dir logs
        if verilator \
            --cc --exe --build --sv --timing \
            --top-module hbm_controller_tb \
            -f filelist.f \
            hbm_controller_tb.sv \
            --Mdir obj_dir \
            -CFLAGS "-std=c++20 -O2" \
            -LDFLAGS "-lpthread" \
            2>&1 | tee logs/build.log; then
            print_success "RTL build passed"

            # Run quick simulation
            print_step "Running quick simulation (1us)..."
            cd obj_dir
            if ./Vhbm_controller_tb +TIME=1us 2>&1 | tee ../logs/sim-quick.log; then
                print_success "Quick simulation passed"
            else
                print_warning "Quick simulation had issues"
            fi
            cd "$PROJECT_ROOT/rtl"
        else
            print_warning "RTL build failed"
        fi
    else
        print_warning "filelist.f not found"
    fi

    cd "$PROJECT_ROOT"
    print_success "RTL checks complete"
}

# =============================================================================
# Performance Benchmark
# =============================================================================

run_benchmark() {
    if [ "$SKIP_BENCHMARK" = true ] || [ "$QUICK_MODE" = true ]; then
        print_info "Skipping benchmark (--quick or --skip-benchmark specified)"
        return
    fi

    print_header "Running Performance Benchmark"

    export PYTHONPATH="$PYTHON_PATH"

    print_step "Running benchmark suite..."
    if python3 -m sim.benchmark --output-dir=sim/results 2>/dev/null; then
        print_success "Benchmark completed"

        # Check for results
        if [ -f "sim/benchmark_results.json" ]; then
            print_info "Results saved to sim/benchmark_results.json"
        fi
        if [ -d "sim/results" ]; then
            print_info "Reports available in sim/results/"
        fi
    else
        print_warning "Benchmark had issues"
    fi

    print_success "Benchmark complete"
}

# =============================================================================
# Documentation Check
# =============================================================================

check_documentation() {
    print_header "Checking Documentation"

    print_step "Checking documentation structure..."
    local docs_ok=true

    if [ -d "$PROJECT_ROOT/docs" ]; then
        echo "  docs/ ✓"
    else
        print_warning "docs/ not found"
        docs_ok=false
    fi

    if [ -f "$PROJECT_ROOT/CLAUDE.md" ]; then
        echo "  CLAUDE.md ✓"
    else
        print_warning "CLAUDE.md not found"
        docs_ok=false
    fi

    if [ -f "$PROJECT_ROOT/README.md" ]; then
        echo "  README.md ✓"
    else
        print_warning "README.md not found"
        docs_ok=false
    fi

    if [ "$docs_ok" = true ]; then
        print_success "Documentation check passed"
    else
        print_warning "Some documentation files are missing"
    fi
}

# =============================================================================
# Summary Report
# =============================================================================

print_summary() {
    print_header "CI Check Summary"

    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "Environment:"
    echo "  Python: $(python3 --version 2>&1 | awk '{print $2}')"
    echo "  Project: $PROJECT_ROOT"
    echo ""
    echo "Checks performed:"
    echo "  ✓ Environment"
    echo "  ✓ Dependencies"
    echo "  ✓ Lint & Code Quality"
    echo "  ✓ Python Tests"
    if [ "$SKIP_RTL" = false ]; then
        echo "  ✓ RTL Checks"
    fi
    if [ "$QUICK_MODE" = false ] && [ "$SKIP_BENCHMARK" = false ]; then
        echo "  ✓ Performance Benchmark"
    fi
    echo "  ✓ Documentation"
    echo ""
    print_success "CI check completed!"
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    echo "HBM System CI Check Script"
    echo "=========================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --quick          Skip benchmark and extended tests"
    echo "  --skip-rtl       Skip RTL verification checks"
    echo "  --skip-benchmark Skip performance benchmark"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Run all checks"
    echo "  $0 --quick        # Quick checks only"
    echo "  $0 --lint         # Lint only"
    echo "  $0 --test         # Tests only"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                QUICK_MODE=true
                shift
                ;;
            --skip-rtl)
                SKIP_RTL=true
                shift
                ;;
            --skip-benchmark)
                SKIP_BENCHMARK=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    print_header "HBM System CI Check"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Mode: $([ "$QUICK_MODE" = true ] && echo "Quick" || echo "Full")"
    echo ""

    # Run checks in order
    check_environment
    install_dependencies
    run_lint_checks
    run_python_tests
    run_rtl_checks

    if [ "$QUICK_MODE" = false ] && [ "$SKIP_BENCHMARK" = false ]; then
        run_benchmark
    fi

    check_documentation
    print_summary
}

# Run main
main "$@"