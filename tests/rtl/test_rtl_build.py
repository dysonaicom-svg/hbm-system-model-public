"""Tests for RTL build automation"""

import pytest
from pathlib import Path


class TestRtlBuildArgs:
    def test_default_sources(self):
        from sim.rtl.rtl_build import DEFAULT_SOURCES
        assert "hbm_controller.sv" in DEFAULT_SOURCES
        assert "hbm_types.svh" in DEFAULT_SOURCES
        assert "hbm_pkg.sv" in DEFAULT_SOURCES
        assert "hbm_controller_tb.sv" in DEFAULT_SOURCES

    def test_default_rtl_dir(self):
        from sim.rtl.rtl_build import DEFAULT_RTL_DIR
        assert DEFAULT_RTL_DIR.name == "rtl"


class TestBuildArgsParser:
    def test_default_args(self):
        from sim.rtl.rtl_build import build_args
        parser = build_args()
        args = parser.parse_args([])
        assert args.top_module == "hbm_controller_tb"
        assert args.trace is False
        assert args.threads == 4

    def test_trace_flag(self):
        from sim.rtl.rtl_build import build_args
        parser = build_args()
        args = parser.parse_args(["--trace"])
        assert args.trace is True

    def test_custom_top_module(self):
        from sim.rtl.rtl_build import build_args
        parser = build_args()
        args = parser.parse_args(["--top-module", "hbm_controller"])
        assert args.top_module == "hbm_controller"

    def test_custom_threads(self):
        from sim.rtl.rtl_build import build_args
        parser = build_args()
        args = parser.parse_args(["--threads", "8"])
        assert args.threads == 8

    def test_custom_build_dir(self, tmp_path):
        from sim.rtl.rtl_build import build_args
        parser = build_args()
        custom_dir = tmp_path / "custom_build"
        args = parser.parse_args(["--build-dir", str(custom_dir)])
        assert args.build_dir == custom_dir

    def test_custom_rtl_dir(self, tmp_path):
        from sim.rtl.rtl_build import build_args
        parser = build_args()
        custom_rtl = tmp_path / "rtl"
        args = parser.parse_args(["--rtl-dir", str(custom_rtl)])
        assert args.rtl_dir == custom_rtl

    def test_custom_sources(self):
        from sim.rtl.rtl_build import build_args
        parser = build_args()
        args = parser.parse_args(["--sources", "a.sv", "b.sv"])
        assert args.sources == ["a.sv", "b.sv"]
