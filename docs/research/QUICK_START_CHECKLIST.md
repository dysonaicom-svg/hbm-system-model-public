# HBM4 建模仿真 - 快速执行清单

## 立即可执行任务 (本周)

### 高优先级
- [ ] 阅读JEDEC JESD270-4标准文档
- [ ] 验证项目当前32通道实现
- [ ] 审查现有PAM3支持

### 中优先级
- [ ] 更新项目规格常量
- [ ] 确认DFI接口实现

---

## 文件变更清单

### 新增文件
```
model/dram/phy_signal.py       # PAM3信号模型
model/dram/logic_base_die.py   # Logic Base Die包装器
model/dram/channel_timing.py   # 独立通道时序
tests/hbm4/test_pam3.py        # PAM3测试
tests/hbm4/test_channel_async.py # 异步通道测试
```

### 修改文件
```
model/dram/hbm4_spec.py         # 更新规格常量
model/dram/dfi_interface.py     # DFI 5.0扩展
model/dram/phy_training.py      # 增强训练序列
rtl/hbm_types.svh              # 新增DFI信号
```

---

## 参考资料

- JEDEC JESD270-4: https://www.jedec.org/news/pressreleases/jedec-announces-hbm4-draft-10-and-update-hbm3e
- Cadence HBM4 VIP: https://www.cadence.com/hbm4-vip
- Rambus HBM4: https://www.rambus.com/blogs/hbm4-the-next-generation-of-high-bandwidth-memory