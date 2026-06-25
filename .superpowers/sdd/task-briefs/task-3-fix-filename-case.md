# Task 3: Fix Filename Case Sensitivity Issues

## Problem
- Git showing files as deleted/modified due to case sensitivity issues
- e.g., `test_hbm4_performance.py` vs `test_HBM4_performance.py`

## Tasks
1. Check git status for case-related changes
2. Identify files with conflicting names (different case)
3. Resolve conflicts by keeping correct/canonical names
4. Update any imports referencing these files

## Success Criteria
- Git status shows clean for case-related issues
- No duplicate files with different cases

## Commands to Run
```bash
git status | grep -i "deleted\|modified"
git ls-files | sort -f | uniq -di  # Find case conflicts
```

## Expected Resolution
- Remove duplicates, keep consistent naming (prefer snake_case)
