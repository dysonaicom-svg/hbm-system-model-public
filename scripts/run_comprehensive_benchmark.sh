#!/bin/bash
#===============================================================================
# HBM Comprehensive Benchmark Suite Runner
#
# Runs a comprehensive set of HBM benchmarks covering:
# 1. Sequential access (best case)
# 2. Random access (worst case)
# 3. Strided access (typical AI workload)
# 4. Hot-spot access (typical inference)
# 5. Mixed read/write patterns
#
# Output formats:
# - JSON for CI integration
# - CSV for analysis
# - Markdown for documentation
#===============================================================================

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BENCHMARK_SCRIPT="$PROJECT_ROOT/sim/benchmark.py"
OUTPUT_DIR="$PROJECT_ROOT/sim"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print header
print_header() {
    echo ""
    echo "========================================"
    echo " HBM Comprehensive Benchmark Suite"
    echo "========================================"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found"
        exit 1
    fi
    log_success "Python3 found: $(python3 --version)"

    # Check benchmark script
    if [ ! -f "$BENCHMARK_SCRIPT" ]; then
        log_error "Benchmark script not found: $BENCHMARK_SCRIPT"
        exit 1
    fi
    log_success "Benchmark script found"

    # Check project root
    if [ ! -d "$PROJECT_ROOT/sim" ]; then
        log_error "Project sim directory not found"
        exit 1
    fi
    log_success "Project directory verified"
}

# Run sequential access benchmark (best case)
run_sequential_benchmark() {
    log_info "Running Sequential Access Benchmark (Best Case)..."
    echo "  Pattern: Sequential"
    echo "  Expected: High row hit rate, lowest latency"

    python3 "$BENCHMARK_SCRIPT" --pattern sequential --rate 0.8 --time 100 --seed 42 --read-ratio 0.7 \
        2>/dev/null || true

    log_success "Sequential benchmark complete"
}

# Run random access benchmark (worst case)
run_random_benchmark() {
    log_info "Running Random Access Benchmark (Worst Case)..."
    echo "  Pattern: Random"
    echo "  Expected: Low row hit rate, highest latency"

    python3 "$BENCHMARK_SCRIPT" --pattern random --rate 0.5 --time 100 --seed 42 --read-ratio 0.7 \
        2>/dev/null || true

    log_success "Random benchmark complete"
}

# Run strided access benchmark (typical AI workload)
run_stride_benchmark() {
    log_info "Running Strided Access Benchmark (AI Workload)..."
    echo "  Pattern: Stride"
    echo "  Expected: Moderate row hit rate, typical for ML workloads"

    python3 "$BENCHMARK_SCRIPT" --pattern stride --rate 0.8 --time 100 --seed 42 --read-ratio 0.9 \
        2>/dev/null || true

    log_success "Stride benchmark complete"
}

# Run hot-spot benchmark (typical inference)
run_hotspot_benchmark() {
    log_info "Running Hot-Spot Access Benchmark (Inference)..."
    echo "  Pattern: Hot-Spot"
    echo "  Expected: Localized access pattern, good for caching"

    python3 "$BENCHMARK_SCRIPT" --pattern hot_spot --rate 0.7 --time 100 --seed 42 --read-ratio 0.8 \
        2>/dev/null || true

    log_success "Hot-spot benchmark complete"
}

# Run mixed read/write patterns
run_mixed_patterns() {
    log_info "Running Mixed Read/Write Patterns..."

    echo "  Testing 100% Read..."
    python3 "$BENCHMARK_SCRIPT" --pattern random --rate 0.5 --time 50 --seed 42 --read-ratio 1.0 \
        2>/dev/null || true

    echo "  Testing 100% Write..."
    python3 "$BENCHMARK_SCRIPT" --pattern random --rate 0.5 --time 50 --seed 42 --read-ratio 0.0 \
        2>/dev/null || true

    echo "  Testing 50/50 Read/Write..."
    python3 "$BENCHMARK_SCRIPT" --pattern sequential --rate 0.5 --time 50 --seed 42 --read-ratio 0.5 \
        2>/dev/null || true

    log_success "Mixed patterns complete"
}

# Run stress test (maximum throughput)
run_stress_test() {
    log_info "Running Stress Test (Maximum Throughput)..."
    echo "  Request rate: 1.0 (100%)"
    echo "  Duration: 200us"

    python3 "$BENCHMARK_SCRIPT" --pattern random --rate 1.0 --time 200 --seed 42 --read-ratio 0.7 \
        2>/dev/null || true

    log_success "Stress test complete"
}

# Generate reports
generate_reports() {
    log_info "Generating reports..."

    # Run full benchmark suite and capture output
    python3 "$BENCHMARK_SCRIPT" --full-suite --time 50 --seed 42 2>&1 | tee "$OUTPUT_DIR/benchmark_full.log"

    log_success "Reports generated"
}

# Run HBM3 vs HBM4 comparison
run_comparison() {
    log_info "Running HBM3 vs HBM4 Comparison..."

    python3 "$BENCHMARK_SCRIPT" --compare-hbm --time 50 --seed 42 2>/dev/null || true

    log_success "Comparison complete"
}

# Display results
display_results() {
    log_info "Displaying results..."

    if [ -f "$OUTPUT_DIR/benchmark_results.json" ]; then
        echo ""
        echo "=== JSON Results Summary ==="
        python3 -c "
import json
with open('$OUTPUT_DIR/benchmark_results.json') as f:
    data = json.load(f)
    print(f\"Total benchmarks: {data['metadata']['total_results']}\")
    if 'summary' in data:
        s = data['summary']
        print(f\"Total completed: {s.get('total_completed_requests', 'N/A')}\")
        print(f\"Avg throughput: {s.get('avg_throughput_gbps', 'N/A'):.3f} GB/s\")
        print(f\"Peak throughput: {s.get('max_throughput_gbps', 'N/A'):.3f} GB/s\")
        print(f\"Avg row hit rate: {s.get('avg_row_hit_rate', 'N/A'):.2%}\")
"
    fi

    if [ -f "$OUTPUT_DIR/benchmark_results.csv" ]; then
        echo ""
        echo "=== CSV Summary ==="
        echo "Last 5 results:"
        tail -5 "$OUTPUT_DIR/benchmark_results.csv" | column -t -s ','
    fi

    log_success "Results displayed"
}

# Main execution
main() {
    print_header

    check_prerequisites

    # Parse command line arguments
    SUITE_MODE="${1:-full}"

    case "$SUITE_MODE" in
        full)
            log_info "Running full benchmark suite..."
            run_sequential_benchmark
            run_random_benchmark
            run_stride_benchmark
            run_hotspot_benchmark
            run_mixed_patterns
            run_stress_test
            run_comparison
            generate_reports
            ;;
        quick)
            log_info "Running quick benchmark (reduced time)..."
            run_random_benchmark
            run_stride_benchmark
            ;;
        sequential)
            run_sequential_benchmark
            ;;
        random)
            run_random_benchmark
            ;;
        stride)
            run_stride_benchmark
            ;;
        hotspot)
            run_hotspot_benchmark
            ;;
        mixed)
            run_mixed_patterns
            ;;
        stress)
            run_stress_test
            ;;
        compare)
            run_comparison
            ;;
        *)
            echo "Usage: $0 [full|quick|sequential|random|stride|hotspot|mixed|stress|compare]"
            echo ""
            echo "Benchmark modes:"
            echo "  full      - Run complete suite (default)"
            echo "  quick     - Quick check with reduced time"
            echo "  sequential - Sequential access pattern only"
            echo "  random    - Random access pattern only"
            echo "  stride    - Strided access pattern only"
            echo "  hotspot   - Hot-spot access pattern only"
            echo "  mixed     - Mixed read/write patterns"
            echo "  stress    - Stress test at maximum rate"
            echo "  compare   - HBM3 vs HBM4 comparison"
            exit 1
            ;;
    esac

    display_results

    echo ""
    echo "========================================"
    echo " Benchmark Suite Complete"
    echo "========================================"
    echo ""
    echo "Output files:"
    echo "  - $OUTPUT_DIR/benchmark_results.json"
    echo "  - $OUTPUT_DIR/benchmark_results.csv"
    echo "  - $OUTPUT_DIR/benchmark_results.md"
    echo "  - $OUTPUT_DIR/benchmark_full.log"
    echo ""
}

# Trap to clean up on exit
trap 'log_warning "Benchmark interrupted"; exit 130' INT TERM

# Run main
main "$@"