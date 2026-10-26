# PSO / ISE example

[中文](#中文) · [English](#english)

## 中文

这是用于验证计算流程的小规模示例：PSO、2 个粒子、11 维参数、3 次迭代，目标函数为 ISE。搜索开始时设置 `rng(42, 'twister')`。参数维数、模型和搜索边界与单目标优化页面一致；种群和迭代次数较小，不用于评价算法性能。

安装 MATLAB R2024b、Simulink、Motor Control Blockset 并完成授权后，在 MATLAB 中将当前目录切换到仓库根目录，执行：

```matlab
addpath(fullfile(pwd, 'examples', 'pso_ise'));
output_dir = run_example;
```

每次结果保存到独立的 `runtime/examples/pso_ise/` 子目录。脚本验证迭代完整性、最优值不增，以及返回的 ISE 与对完整位置序列重新积分的结果一致；结束后恢复原工作目录、搜索路径和随机数状态。

仓库中的 `reference/summary.json` 和 `reference/tracking.csv` 是一次实际运行的参考输出。CSV 每 10 个采样点取 1 个点，仅用于画图；目标值由完整序列计算。仿真调用会改变 MATLAB 全局随机数状态，因此相同初始种子下的结果可能不同（同机两次运行分别得到 0.0147707788 和 0.0146859044）。

要单独核对参考结果，完成上面的路径设置后执行 `verify_reference`。它跳过随机搜索，将记录的 11 个参数重新输入相同模型，检查 ISE 与参考值、独立积分一致（相对容差 `1e-6`，绝对容差下限 `1e-10`）。

## English

This small integration example uses PSO with 2 particles, 11 parameters, 3 iterations and an ISE objective. It sets the initial random state with `rng(42, 'twister')`. The model, dimensions and search bounds match the single-objective page. The small population and iteration count are intended to verify the computation path, not to benchmark optimization performance.

Install and authorize MATLAB R2024b, Simulink and Motor Control Blockset. Set MATLAB's current directory to the repository root, then run the commands above.

Each invocation creates a separate folder under `runtime/examples/pso_ise/`. The script checks complete iterations, non-increasing best-so-far fitness and agreement between the reported ISE and independent integration of the full tracking series. It restores the working directory, search path and random state afterward.

The files in `reference/` are recorded outputs from a real run. `tracking.csv` keeps every tenth sample for plotting; the objective uses the full series. Simulation calls change MATLAB's global random state, so runs with the same initial seed can differ (two runs on the same computer gave 0.0147707788 and 0.0146859044).

To check the recorded result separately, run `verify_reference` after adding the example directory to the path. It bypasses the search, evaluates the 11 saved parameters with the same model, and compares ISE with the reference and independent integration (relative tolerance `1e-6`, absolute floor `1e-10`).
