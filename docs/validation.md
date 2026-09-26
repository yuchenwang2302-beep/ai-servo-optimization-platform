# Validation / 测试记录

Validated on Windows x64 with Python 3.12.14 and MATLAB R2024b.

| Check | Result |
| --- | --- |
| Automated tests | 66 passed |
| UI smoke checks | 2 passed |
| Fresh checkout and independent Python environment | Installation and startup checks passed |
| Real PSO/ISE UI run | Received iterations 1, 2 and 3; returned ISE matched independent integration |
| Saved-parameter replay | Reference ISE reproduced: 0.014770778797258894 |

The UI checks cover both languages, parameter validation, run states, cancellation, history and layouts at 800×600, 1366×720 and 1920×1000. The real UI run used 2 particles and 3 iterations; computation took 43.39 seconds and total time was 65.47 seconds on the test computer.

Earlier small-workload checks exercised all 16 algorithm entry points. The current release rechecked installation, UI behavior and the PSO/ISE computation path.

The [PSO/ISE example](../examples/pso_ise/README.md) includes recorded parameters and results. Simulation calls affect the global random state, so setting the initial seed alone does not guarantee an identical search trajectory. The separate saved-parameter check verifies the reference result directly.

Screenshots and the walkthrough include a recorded MATLAB result. The walkthrough presents interface views rather than elapsed computation time.

[Machine-readable record](validation-results.json)

## 中文

在 Windows x64、Python 3.12.14 与 MATLAB R2024b 环境下，66 项自动测试和 2 项界面检查通过。独立克隆目录重新安装环境后，启动检查与真实界面计算均通过；PSO/ISE 返回值与独立积分一致，保存参数的重算也与参考值一致。

检查覆盖双语、输入校验、停止与计时、运行记录和多种窗口尺寸。固定初始种子不保证整个随机搜索逐值一致，详细配置与重算方法见示例说明。
