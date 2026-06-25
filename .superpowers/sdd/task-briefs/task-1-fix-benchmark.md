# Task 1: Fix Benchmark Test Segfault

## Problem
- `pytest tests/benchmark/test_enhanced_benchmark.py` times out or segfaults on refresh impact tests
- Tests with longer durations (50,000ns) cause infinite loops or performance issues

## Root Cause Analysis Required
1. Check `run_refresh_impact_test` in `model/benchmark/enhanced_benchmark.py`
2. Check `controller.tick()` performance in long loops
3. Verify the while loops have proper exit conditions

## Tasks
1. Identify the specific test causing segfault/timeout
2. Fix the infinite loop or performance issue
3. Ensure test completes in reasonable time (<30s per test)
4. Run pytest to verify fix

## Success Criteria
- `pytest tests/benchmark/test_enhanced_benchmark.py -v --tb=short` completes in <120s
- All 31 tests pass
- No segfaults or hangs

## Test Files to Check
- `tests/benchmark/test_enhanced_benchmark.py` (lines 153-200 contain refresh tests)
- `model/benchmark/enhanced_benchmark.py` (line 785+ contains run_refresh_impact_test)

## Expected Resolution
Reduce test duration or optimize controller.tick() to ensure tests complete quickly
