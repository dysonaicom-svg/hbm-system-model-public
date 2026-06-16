"""
RTL Simulation Tests

Tests RTL compilation and simulation setup.
Note: Full RTL simulation requires commercial simulators (Questa/VCS/Vivado).
These tests verify RTL file structure and provide simulation instructions.
"""

import pytest
import os
import subprocess


class TestRTLFilesExist:
    """Verify RTL files exist and are valid"""

    def test_rtl_directory_exists(self):
        """RTL directory should exist"""
        assert os.path.isdir("rtl")

    def test_hbm_types_exists(self):
        """hbm_types.svh should exist"""
        path = "rtl/hbm_types.svh"
        assert os.path.isfile(path)
        with open(path) as f:
            content = f.read()
            assert "hbm_types" in content.lower()

    def test_hbm_pkg_exists(self):
        """hbm_pkg.sv should exist"""
        path = "rtl/hbm_pkg.sv"
        assert os.path.isfile(path)

    def test_hbm_controller_exists(self):
        """hbm_controller.sv should exist"""
        path = "rtl/hbm_controller.sv"
        assert os.path.isfile(path)
        with open(path) as f:
            content = f.read()
            assert "module hbm_controller" in content

    def test_dram_model_exists(self):
        """dram_model.sv should exist"""
        path = "rtl/dram_model.sv"
        assert os.path.isfile(path)
        with open(path) as f:
            content = f.read()
            assert "module dram_model" in content

    def test_testbench_exists(self):
        """hbm_controller_tb.sv should exist"""
        path = "rtl/hbm_controller_tb.sv"
        assert os.path.isfile(path)


class TestRTLFileStructure:
    """Verify RTL file structure"""

    def test_hbm_controller_has_interface(self):
        """hbm_controller should have proper interface"""
        with open("rtl/hbm_controller.sv") as f:
            content = f.read()
            # Should have AXI-like or req/resp interface
            assert "req_" in content or "axi" in content.lower()
            assert "resp_" in content or "axi" in content.lower()

    def test_dram_model_has_dram_interface(self):
        """dram_model should have DRAM interface"""
        with open("rtl/dram_model.sv") as f:
            content = f.read()
            assert "dram_" in content or "mem_" in content.lower()

    def test_hbm_types_defines_constants(self):
        """hbm_types.svh should define constants"""
        with open("rtl/hbm_types.svh") as f:
            content = f.read()
            assert "NUM_STACKS" in content or "NUM_CHANNELS" in content

    def test_build_script_exists(self):
        """Build script should exist"""
        assert os.path.isfile("rtl/build_rtl.sh")
        assert os.access("rtl/build_rtl.sh", os.X_OK)


class TestSimulatorAvailability:
    """Check available simulators"""

    def test_verilator_available(self):
        """Check if Verilator is available"""
        result = subprocess.run(
            ["which", "verilator"],
            capture_output=True,
            text=True
        )
        # Just check if command exists, don't fail if not available
        if result.returncode == 0:
            assert "verilator" in result.stdout

    def test_iverilog_available(self):
        """Check if Icarus Verilog is available"""
        result = subprocess.run(
            ["which", "iverilog"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            assert "iverilog" in result.stdout

    def test_vivado_mcp_available(self):
        """Check if Vivado MCP is configured"""
        mcp_config = ".mcp.json"
        if os.path.isfile(mcp_config):
            with open(mcp_config) as f:
                content = f.read()
                assert "vivado" in content.lower() or "Vivado" in content


class TestRTLCompilation:
    """Test RTL compilation (using available tools)"""

    def test_verilator_compilation_check(self):
        """Try Verilator compilation check if available"""
        result = subprocess.run(
            ["which", "verilator"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.skip("Verilator not available")

        # Run verilator in lint-only mode
        result = subprocess.run(
            [
                "verilator", "--lint-only", "-sv",
                "-Irtl",
                "rtl/hbm_types.svh",
                "rtl/hbm_controller.sv",
                "rtl/dram_model.sv"
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        # Check for critical errors (allow warnings)
        if result.returncode != 0:
            # Extract just the error lines
            errors = [l for l in result.stdout.split('\n') if 'Error' in l]
            if errors:
                pytest.fail("Verilator errors: " + "; ".join(errors[:5]))


class TestUVMVerification:
    """Test UVM verification setup"""

    def test_uvm_directory_exists(self):
        """UVM verification directory should exist"""
        assert os.path.isdir("verification/uvm")

    def test_uvm_files_exist(self):
        """All UVM files should exist"""
        required_files = [
            "verification/uvm/hbm_env_pkg.sv",
            "verification/uvm/hbm_test_pkg.sv",
            "verification/uvm/hbm_tb.sv",
            "verification/uvm/Makefile",
        ]
        for path in required_files:
            assert os.path.isfile(path), f"Missing: {path}"

    def test_uvm_has_testcases(self):
        """UVM test package should have test cases"""
        with open("verification/uvm/hbm_test_pkg.sv") as f:
            content = f.read()
            assert "class" in content
            assert "test" in content.lower()

    def test_uvm_has_environment(self):
        """UVM environment should be properly defined"""
        with open("verification/uvm/hbm_env_pkg.sv") as f:
            content = f.read()
            assert "hbm_env" in content
            assert "uvm_env" in content.lower()


class TestRTLDocumentation:
    """Test RTL documentation"""

    def test_readme_exists(self):
        """README should exist"""
        assert os.path.isfile("README.md")

    def test_readme_has_rtl_section(self):
        """README should mention RTL"""
        with open("README.md") as f:
            content = f.read()
            assert "RTL" in content or "rtl" in content.lower()

    def test_build_script_is_documented(self):
        """Build script should provide usage instructions"""
        with open("rtl/build_rtl.sh") as f:
            content = f.read()
            assert "echo" in content  # Has output messages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])