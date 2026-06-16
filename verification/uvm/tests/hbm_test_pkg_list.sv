# ------------------------------------------------------------
# hbm_test_pkg_list.sv - Test Package Index
# Lists all available test packages
# ------------------------------------------------------------
// This file serves as an index for all test packages.
// Include the appropriate test package for each test scenario.

// Base Test Package
+incdir+${REF_DIR}
${REF_DIR}/hbm_test_pkg.sv

# QoS Priority Tests
+incdir+${TEST_DIR}
${TEST_DIR}/hbm_qos_test_pkg.sv

# Refresh Conflict Tests
${TEST_DIR}/hbm_refresh_test_pkg.sv

# Bank Contention Tests
${TEST_DIR}/hbm_bank_contention_test_pkg.sv

# Boundary Condition Tests
${TEST_DIR}/hbm_boundary_test_pkg.sv

# Coverage Collection
${TEST_DIR}/hbm_coverage_pkg.sv
