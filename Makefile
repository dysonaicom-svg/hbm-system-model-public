# HBM System Makefile
# =============================================================================

.PHONY: help test test-all test-quick clean benchmark docs coverage lint

# Python executable
PYTHON := python3
PYTEST := pytest

# Directories
TEST_DIR := tests
SRC_DIR := model sim

# Test options
PYTEST_FLAGS := -v --tb=short
COVERAGE_FLAG := --cov=. --cov-report=html --cov-report=xml

# =============================================================================
# Help
# =============================================================================

help:
	@echo "HBM System Makefile"
	@echo "==================="
	@echo ""
	@echo "Test targets:"
	@echo "  test           - Run all tests"
	@echo "  test-quick     - Run quick tests (no coverage)"
	@echo "  test-dram      - Run DRAM model tests"
	@echo "  test-controller - Run controller tests"
	@echo "  test-sim       - Run simulation tests"
	@echo "  test-hbm4      - Run HBM4 tests"
	@echo "  test-integration - Run integration tests"
	@echo "  test-regression - Run regression tests"
	@echo "  test-rtl       - Run RTL verification tests"
	@echo ""
	@echo "Quality targets:"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code with black"
	@echo "  typecheck      - Run type checking"
	@echo ""
	@echo "Other targets:"
	@echo "  benchmark      - Run performance benchmark"
	@echo "  coverage       - Generate coverage report"
	@echo "  docs           - Generate documentation"
	@echo "  clean          - Clean generated files"

# =============================================================================
# Testing
# =============================================================================

test: test-all

test-all:
	@echo "Running all tests..."
	$(PYTEST) tests/ $(PYTEST_FLAGS) $(COVERAGE_FLAG)

test-quick:
	@echo "Running quick tests..."
	$(PYTEST) tests/ $(PYTEST_FLAGS) -x

test-dram:
	@echo "Running DRAM model tests..."
	$(PYTEST) tests/dram/ $(PYTEST_FLAGS)

test-controller:
	@echo "Running controller tests..."
	$(PYTEST) tests/controller/ $(PYTEST_FLAGS)

test-sim:
	@echo "Running simulation tests..."
	$(PYTEST) tests/sim/ $(PYTEST_FLAGS)

test-hbm4:
	@echo "Running HBM4 tests..."
	$(PYTEST) tests/hbm4/ $(PYTEST_FLAGS)

test-integration:
	@echo "Running integration tests..."
	$(PYTEST) tests/integration/ $(PYTEST_FLAGS)

test-regression:
	@echo "Running regression tests..."
	$(PYTEST) tests/regression/ $(PYTEST_FLAGS)

test-rtl:
	@echo "Running RTL verification tests..."
	$(PYTEST) tests/verification/ $(PYTEST_FLAGS)

# =============================================================================
# Quality
# =============================================================================

lint:
	@echo "Running flake8..."
	flake8 $(SRC_DIR) tests/ --max-line-length=120 --ignore=E501,W503 || true

format:
	@echo "Formatting code with black..."
	black $(SRC_DIR) tests/ || true

typecheck:
	@echo "Running mypy type check..."
	mypy $(SRC_DIR) --ignore-missing-imports || true

# =============================================================================
# Benchmark & Coverage
# =============================================================================

benchmark:
	@echo "Running performance benchmark..."
	python -m sim.benchmark --output-dir=sim/results

coverage:
	@echo "Generating coverage report..."
	$(PYTEST) tests/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

# =============================================================================
# Documentation
# =============================================================================

docs:
	@echo "Checking documentation..."
	@test -d docs && echo "docs/ directory exists"
	@test -f README.md && echo "README.md exists"
	@test -f CLAUDE.md && echo "CLAUDE.md exists"

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	rm -rf sim/results/*.json 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true