# HBM4 测试覆盖率报告

生成时间: 2026-06-24

## 总体覆盖率

| 模块 | 语句覆盖率 | 状态 |
|------|-----------|------|
| Controller | 64% | 良好 |
| DRAM | 79% | 良好 |
| Interconnect | 80% | 良好 |
| SIM | 51% | 中等 |
| PHY | 需进一步测试 | - |

## 模块详细分析

### Controller 模块 (model/controller/)

| 文件 | 语句数 | 未覆盖 | 覆盖率 |
|------|--------|--------|--------|
| address_decoder.py | 237 | 80 | 66% |
| command_pipeline.py | 165 | 0 | 100% |
| command_sequencer.py | 187 | 34 | 82% |
| config.py | 155 | 0 | 100% |
| controller.py | 110 | 11 | 90% |
| dfi_encoder.py | 541 | 35 | 94% |
| exceptions.py | 10 | 0 | 100% |
| hbm4_address_decoder.py | 198 | 22 | 89% |
| hbm4_controller.py | 413 | 51 | 88% |
| hbm4_qos_scheduler.py | 424 | 48 | 89% |
| hbm4_refresh_scheduler.py | 270 | 8 | 97% |
| qos_scheduler.py | 76 | 1 | 99% |
| queue.py | 400 | 58 | 86% |
| refresh_scheduler.py | 85 | 9 | 89% |
| request.py | 149 | 0 | 100% |
| scheduler.py | 310 | 14 | 95% |

**总计**: 5265 语句, 1896 未覆盖, 64% 覆盖率

### DRAM 模块 (model/dram/)

| 文件 | 语句数 | 未覆盖 | 覆盖率 |
|------|--------|--------|--------|
| bank_state_machine.py | 392 | 106 | 73% |
| channel_model.py | 77 | 26 | 66% |
| channel_timing.py | 195 | 113 | 42% |
| dfi_interface.py | 1108 | 81 | 93% |
| dram_model.py | 282 | 62 | 78% |
| ecc_crc.py | 676 | 62 | 91% |
| hbm4_bank_state_machine.py | 430 | 40 | 91% |
| hbm4_channel_model.py | 1026 | 323 | 69% |
| hbm4_spec.py | 99 | 5 | 95% |
| lane_repair.py | 420 | 49 | 88% |
| logic_base_die.py | 1213 | 128 | 89% |
| loopback_controller.py | 409 | 15 | 96% |
| mbist_controller.py | 499 | 90 | 82% |
| phy_signal.py | 160 | 30 | 81% |
| phy_training.py | 928 | 214 | 77% |
| power_estimator.py | 508 | 36 | 93% |
| stack_model.py | 106 | 57 | 46% |
| thermal_controller.py | 226 | 28 | 88% |
| thermal_management.py | 260 | 59 | 77% |
| thermal_model.py | 280 | 48 | 83% |
| thermal_sensor.py | 237 | 29 | 88% |
| timing.py | 236 | 17 | 93% |

**总计**: 10334 语句, 2166 未覆盖, 79% 覆盖率

### Interconnect 模块 (model/interconnect/)

| 文件 | 语句数 | 未覆盖 | 覆盖率 |
|------|--------|--------|--------|
| __init__.py | 16 | 13 | 19% |
| axi4_bridge.py | 739 | 116 | 84% |
| axi4_converter.py | 279 | 99 | 65% |
| axi4_monitor.py | 343 | 115 | 66% |
| gem5_memory_port.py | 486 | 74 | 85% |
| interconnect.py | 483 | 58 | 88% |

**总计**: 2346 语句, 475 未覆盖, 80% 覆盖率

### SIM 模块 (sim/)

| 文件 | 语句数 | 未覆盖 | 覆盖率 |
|------|--------|--------|--------|
| benchmark.py | 473 | 144 | 70% |
| benchmark_suite.py | 394 | 327 | 17% |
| comparison_framework.py | 247 | 119 | 52% |
| hbm4_unified_simulator.py | 252 | 105 | 58% |
| result_comparison.py | 275 | 34 | 88% |
| rtl_interface.py | 253 | 58 | 77% |
| simulator.py | 596 | 108 | 82% |
| unified_simulator.py | 400 | 309 | 23% |
| visualization/* | 1047 | 779 | 26% |

**总计**: 7087 语句, 3507 未覆盖, 51% 覆盖率

## 测试状态

| 类别 | 测试数 | 通过 | 失败 |
|------|--------|------|------|
| Controller | 1230 | 1230 | 0 |
| DRAM | 1899 | 1899 | 0 |
| Interconnect/PHY | 506 | 504 | 2 |
| SIM | 264 | 264 | 0 |

### 已知失败测试

1. `tests/phy/test_signal_integrity.py::TestEyeDiagramAnalyzer::test_estimate_ber`
   - 原因: `numpy.math` 模块不存在，应使用 `math` 或 `numpy.lib.scimath`

2. `tests/phy/test_signal_integrity.py::TestEyeDiagramAnalyzer::test_margin_analysis`
   - 原因: 同上，依赖 `estimate_ber()` 方法

## 改进建议

### 高优先级

1. **PHY 模块 numpy 修复**: 修复 `model/phy/eye_analyzer.py` 中的 `np.math` 引用
2. **SIM 模块覆盖率提升**: 当前 51%，需要增加更多集成测试

### 中优先级

1. **address_decoder.py**: 增加边界条件测试
2. **channel_timing.py**: 增加时序边界测试
3. **visualization 模块**: 增加更多图表生成测试

### 低优先级

1. **__init__.py 文件**: 大部分未使用函数可标记为 `# pragma: no cover`

## 结论

- **总体覆盖率**: 约 65-70%
- **测试通过率**: 99.9% (仅 2 个已知失败)
- **建议**: 修复 numpy 错误后继续提升覆盖率
