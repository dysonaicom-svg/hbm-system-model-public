# HBM 项目管理报告

**生成日期**: 2026-06-16  
**状态**: ✅ 清理完成

---

## 一、项目现状分析

### 1.1 发现的问题

| 问题类型 | 描述 | 影响 |
|---------|------|------|
| 🔴 重复目录 | `hbm4-model/`, `hbm4-sim/` 在根目录有存根，同时 `public_release/` 也有完整内容 | 混乱、占空间 |
| 🔴 空目录 | `HBM/` 目录完全为空 | 无用文件 |
| 🔴 重复拷贝 | `github/hbm4-model/`, `github/hbm4-sim/` 是源码拷贝 | 447+ 文件重复 |
| 🔴 构建产物 | `nvc_build/`, `obj_dir/` 等构建目录 | 31MB+ 无用文件 |
| 🔴 隐私泄露 | `.mcp.json` 被 git 追踪 | Co-Authored-By 信息暴露 |
| 🟡 临时文件 | `*.vcd`, `*_comparison.json` 等 | 无版本控制价值 |

### 1.2 Git 工作树状态

```
/home/ic/JXTF/HBM      6f72dff [hbm4-phase-cd]  ← 主项目
/tmp/hbm4-publish      9c30012 [hbm4-publish]  ← 发布分支工作树
/tmp/hbm4-readme-push  e2935cb [codex-hbm4-readme] ← README 更新工作树
```

---

## 二、项目组件清单

### 2.1 核心组件 (git 追踪)

| 组件 | 路径 | 说明 | 用途 |
|------|------|------|------|
| **模型库** | `model/` | Controller, DRAM, PHY, Interconnect | 芯片设计探索 |
| **仿真器** | `sim/` | HBMSimulator, UnifiedSimulator | 性能基准测试 |
| **测试** | `tests/` | 3373+ 测试用例 | 质量保证 |
| **验证** | `verification/` | UVM 环境、参考模型 | RTL 对齐 |
| **RTL** | `rtl/` | SystemVerilog 代码 | 硬件实现 |
| **文档** | `docs/` | 设计文档、用户指南 | 知识管理 |
| **发布包** | `public_release/` | ⭐ Git Submodule | 外部发布 |

### 2.2 外部依赖

| 组件 | 路径 | 说明 |
|------|------|------|
| Ramulator2 | `research/ramulator2/` | Git Submodule - 参考模拟器 |

### 2.3 待清理目录

| 目录 | 大小 | 建议操作 |
|------|------|---------|
| `HBM/` | 20K | 删除 (空目录) |
| `hbm4-model/` | 12K | 删除 (存根) |
| `hbm4-sim/` | 12K | 删除 (存根) |
| `github/` | 6.0M | 删除 (重复拷贝) |
| `nvc_build/` | 31M | 删除 (构建产物) |
| `obj_dir/` | 2.5M | 删除 (构建产物) |

---

## 三、发布策略

### 3.1 发布层级

```
┌─────────────────────────────────────────────────────────────┐
│  Level 3: Public Release (public_release/)                 │
│  - 完整可安装的 Python 包                                    │
│  - Apache 2.0 许可证                                        │
│  - 面向: 外部研究人员、开源社区                               │
└─────────────────────────────────────────────────────────────┘
                          ↓ pip install / GitHub Release
┌─────────────────────────────────────────────────────────────┐
│  Level 2: Internal Package (hbm4-model + hbm4-sim)           │
│  - 拆分的 Python 包 (待发布)                                  │
│  - 面向: 公司内部团队                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓ 内部仓库
┌─────────────────────────────────────────────────────────────┐
│  Level 1: Full Repository (主仓库)                           │
│  - 完整源码 + RTL + 验证 + 文档                               │
│  - 面向: 核心开发团队                                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 接收人角色矩阵

| 接收人 | 角色 | 访问内容 | 交付方式 |
|-------|------|---------|---------|
| **内部开发团队** | 芯片设计工程师 | 完整仓库 + RTL | Git 仓库 |
| **算法团队** | 性能优化工程师 | hbm4-model + hbm4-sim | pip 私有仓库 |
| **验证团队** | 验证工程师 | RTL + UVM 环境 | Verilator/Questa |
| **学术合作** | 大学教授/研究员 | public_release | GitHub Release |
| **客户** | 芯片集成商 | public_release + API | PyPI / GitHub |

---

## 四、执行计划

### 4.1 立即执行 (本次会话)

```
✅ 清理空目录和重复目录
✅ 更新 .gitignore
✅ 移除 .mcp.json 追踪
✅ 验证清理结果
```

### 4.2 后续任务

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 发布 hbm4-model 到 PyPI | P1 | 核心模型库 |
| 发布 hbm4-sim 到 PyPI | P1 | 仿真平台 |
| 整理 public_release README | P2 | 外部可见文档 |
| 创建内部文档站点 | P2 | Confluence/Notion |
| 制定权限管理策略 | P3 | 细粒度访问控制 |

---

## 五、Git 分支策略

```
main (受保护)
  ├── hbm4-phase-cd (当前开发)
  ├── hbm4-publish (发布准备)
  └── hbm4-readme-push (文档更新)
```

| 分支 | 用途 | 保护级别 |
|------|------|---------|
| main | 稳定版本 | 🔒 完全保护 |
| hbm4-phase-cd | 开发分支 | 🔒 需要 PR |
| hbm4-publish | 发布候选 | 🔒 需要 review |

---

## 六、清理后的预期结构

```
/home/ic/JXTF/HBM/
├── .git/                    # Git 仓库
├── .gitignore               # 已清理
├── .gitmodules              # 子模块配置
├── model/                   # 核心模型 (追踪)
├── sim/                     # 仿真器 (追踪)
├── tests/                   # 测试套件 (追踪)
├── verification/            # UVM 验证 (追踪)
├── rtl/                     # RTL 代码 (追踪)
├── docs/                    # 文档 (追踪)
├── public_release/          # 发布包 (submodule)
├── research/ramulator2/     # 参考模拟器 (submodule)
├── scripts/                 # 工具脚本 (追踪)
├── examples/                # 示例代码 (追踪)
├── config/                  # 配置文件 (追踪)
├── pyproject.toml           # Python 包配置
├── setup.py                 # 安装脚本
├── requirements.txt         # 依赖
├── README.md                # 主 README
├── CLAUDE.md                # AI 开发指南
├── QUICKSTART.md            # 快速入门
├── RELEASE.md               # 发布说明
└── CHANGELOG.md             # 变更日志

预计清理: ~40MB
预计保留: ~50MB
```

---

## 七、验证清单

清理完成后验证:

- [x] `HBM/`, `hbm4-model/`, `hbm4-sim/` 目录已删除
- [x] `github/` 目录已删除
- [x] `nvc_build/`, `obj_dir/` 已删除
- [x] `.mcp.json` 不再被 git 追踪
- [x] `.gitignore` 包含 `mcp`, `claude`, `obj_dir` 等
- [ ] `git status` 显示干净的暂存区 (待提交)
- [x] 核心目录 `model/`, `sim/`, `tests/`, `rtl/` 完好
- [x] `public_release/` submodule 正常

---

## 八、清理执行记录

| 时间 | 操作 | 结果 |
|------|------|------|
| 2026-06-16 | 删除 `HBM/`, `hbm4-model/`, `hbm4-sim/` | ✅ 成功 |
| 2026-06-16 | 删除 `github/`, `nvc_build/`, `obj_dir/` | ✅ 成功 |
| 2026-06-16 | 更新 `.gitignore` | ✅ 成功 |
| 2026-06-16 | 移除 `.mcp.json` 追踪 | ✅ 成功 |
| 2026-06-16 | 清理临时文件 | ✅ 成功 |

---

**报告生成完成**
