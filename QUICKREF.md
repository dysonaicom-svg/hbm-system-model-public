# HBM 快速参考

## 运行测试

```bash
# 全部测试
pytest tests/ -v

# 仿真测试
pytest tests/sim/ -v

# 性能测试
pytest tests/regression/ -v

# RTL 测试
cd rtl && make lint && make sim
```

## 对比

```bash
# Model vs RTL
python scripts/auto_compare.py --mode quick

# 性能回归
python scripts/compare_rtl_model.py
```

## 覆盖率

```bash
python verification/uvm/scripts/gen_coverage_report.py
```
