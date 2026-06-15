# NVC 仿真器使用说明

## 简介

**NVC** 是一个完整的开源 SystemVerilog/UVM 仿真器，由 Nick Gibson 开发。
- 完整的 SystemVerilog 支持
- 完整的 UVM 支持
- 高性能 LLVM 后端

## 安装位置

```bash
/home/ic/JXTF/HBM/tools/nvc/
```

## 基本用法

### 环境设置

```bash
export PATH="/home/ic/JXTF/HBM/tools/nvc/bin:$PATH"
export NVC=/home/ic/JXTF/HBM/tools/nvc
```

### 编译 RTL

```bash
# 分析单个文件
nvc -a --work=work hbm_types.svh
nvc -a --work=work hbm_controller.sv
nvc -a --work=work dram_model.sv

# 分析整个设计
nvc -a --work=work --std=sv2017 rtl/*.sv

#Elaborate (连接)
nvc -e --work=work top_module
```

### 运行仿真

```bash
# 基本运行
nvc -r top_module

# 指定超时
nvc -r --stop=1ms top_module

# 生成波形
nvc -r --dump=wave.vcd top_module

# 指定 UVM 测试
nvc -r --stop=1ms top_module +UVM_TESTNAME=hbm_random_test
```

### UVM 支持

```bash
# 包含 UVM 库
nvc -a --std=uvm /path/to/uvm/src/uvm.sv

# 运行 UVM 测试
nvc -e --std=uvm hbm_tb
nvc -r --stop=1s hbm_tb +UVM_TESTNAME=hbm_random_test
```

## HBM 项目使用示例

```bash
cd /home/ic/JXTF/HBM

# 设置环境
export PATH="/home/ic/JXTF/HBM/tools/nvc/bin:$PATH"

# 创建 work 库
nvc --std=sv2017 -a rtl/hbm_types.svh
nvc --std=sv2017 -a rtl/hbm_controller.sv
nvc --std=sv2017 -a rtl/dram_model.sv
nvc --std=sv2017 -a verification/uvm/hbm_tb.sv

# Elaborate
nvc -e hbm_tb

# 运行测试
nvc -r hbm_tb +UVM_TESTNAME=hbm_random_test
```

## 常用选项

| 选项 | 说明 |
|------|------|
| `-a` | 分析 (Elaboration) |
| `-e` | Elaborate (连接) |
| `-r` | 运行仿真 |
| `--work=lib` | 指定工作库 |
| `--std=sv2017` | 使用 SystemVerilog 2017 标准 |
| `--stop=time` | 仿真停止时间 |
| `--dump=file` | 生成波形文件 |
| `--debug` | 调试模式 |
| `-g` | 生成覆盖率报告 |

## 波形查看

使用 GTKwave 查看生成的 VCD 文件：

```bash
gtkwave wave.vcd
```

## 已知限制

- 不支持 SystemVerilog 某些高级特性 (如特定的 DPI 调用)
- 覆盖率功能需要额外配置

## 参考资料

- 官方文档: https://nickg.me.uk/nvc/
- GitHub: https://github.com/nickg/nvc