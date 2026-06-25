# Task 2: Fix conftest.py Duplicate Fixtures

## Problem
- Duplicate fixture definitions causing test collection warnings/errors
- Some conftest.py files may have conflicting fixture names

## Tasks
1. Find all conftest.py files in tests/ directory
2. Identify duplicate fixture definitions
3. Merge or remove duplicate fixtures
4. Verify tests still pass after fix

## Success Criteria
- No pytest collection warnings about duplicate fixtures
- All tests pass

## Files to Check
- `tests/conftest.py`
- `tests/controller/conftest.py`
- `tests/dram/conftest.py`
- `tests/hbm4/conftest.py`
- Any other conftest.py files

## Expected Resolution
Consolidate duplicate fixtures into a single source
