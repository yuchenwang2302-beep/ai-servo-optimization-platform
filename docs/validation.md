# Validation / 测试记录

Tested on Windows x64 with Python 3.12.14 and MATLAB R2024b.

| Check | Result |
| --- | --- |
| Automated tests | 66 passed |
| UI smoke checks | 2 passed |
| Fresh checkout with a new Python environment | Installation and startup passed |
| PSO/ISE run from the UI | Returned ISE matched independent integration |
| Saved-parameter replay | Reference ISE reproduced (0.014770778797258894) |
| MOGOA, NONMOGOA, LVMOGOA, MDF_MOGOA | Two-iteration runs completed; stored HV matched an independent box-union calculation |

The UI checks cover both languages, input validation, run states, cancellation, run history and window sizes from 800×600 to 1920×1000. Earlier small-workload tests exercised all ten optimization entry points.

See the [PSO/ISE example](../examples/pso_ise/README.md) for recorded parameters and results, and the [support README](../matlab_scripts/optimization/multi_objectives/support/README.md) for HV settings.

## 中文

在 Windows x64、Python 3.12.14 与 MATLAB R2024b 环境下，66 项自动测试和 2 项界面检查通过。独立克隆并重建环境后，安装、启动和界面计算均正常；PSO/ISE 返回值与独立积分一致，保存参数的重算与参考值一致。四种多目标算法的 HV 记录经过独立体积计算核对。
