# matlab_worker.py
import matlab.engine
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import traceback
import os
import time


class MatlabWorker(QThread):
    # 信号定义
    finished = pyqtSignal(object, object, object)  # 辨识算法使用 (gb, g, gbest)
    optimization_finished = pyqtSignal(bool, float, list, np.ndarray, np.ndarray, np.ndarray)  # 优化算法使用
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current_iter, total_iter

    def __init__(self, algorithm, params, is_optimization=False):
        super().__init__()
        self.algorithm = algorithm
        self.params = params
        self.running = True
        self.is_optimization = is_optimization

    #     # 参数验证
    #     self._validate_parameters()

    # def _validate_parameters(self):
    #     """验证算法类型和参数"""
    #     expected_algorithms = ["PSO", "GA", "DE", "IA", "FA", "HPSO"]
    #     if self.algorithm not in expected_algorithms:
    #         raise ValueError(f"未知的算法类型: {self.algorithm}. 预期的算法类型为: {expected_algorithms}")

    #     required_params = {
    #         "群体粒子个数 (N)": int,
    #         "粒子维数 (D)": int,
    #         "最大迭代次数 (T)": int,
    #         "速度 (vref)": float
    #     }

    #     for param, dtype in required_params.items():
    #         if param not in self.params:
    #             raise KeyError(f"缺少必要的参数: {param}")
    #         try:
    #             self.params[param] = dtype(self.params[param])
    #         except (ValueError, TypeError) as e:
    #             raise TypeError(f"参数 {param} 类型错误: {str(e)}")

    def run(self):
        """执行MATLAB算法的核心方法"""
        try:
            eng = matlab.engine.start_matlab()
            self._setup_matlab_path(eng)

            if self.is_optimization:
                self._run_optimization(eng)
            else:
                self._run_identification(eng)

        except Exception as e:
            self.error.emit(str(e))
            traceback.print_exc()
        finally:
            if 'eng' in locals():
                eng.quit()

    def _setup_matlab_path(self, eng):
        """设置MATLAB路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))  # src目录
        project_root = os.path.dirname(current_dir)  # 项目目录
        base_path = os.path.join(project_root, "matlab_scripts")

        if not os.path.isdir(base_path):
            raise FileNotFoundError(f"MATLAB脚本目录不存在: {base_path}")

        if self.is_optimization:
            if self.algorithm in ["MOGOA", "NONMOGOA", "LVMOGOA", "MDF_MOGOA"]:
                multi_path = os.path.join(base_path, 'optimization', 'multi_objectives')
                if not os.path.isdir(multi_path):
                    raise FileNotFoundError(f"MOGOA路径不存在: {multi_path}")
                eng.addpath(multi_path, nargout=0)
            else:
                single_path = os.path.join(base_path, 'optimization', 'single_objective')
                if not os.path.isdir(single_path):
                    raise FileNotFoundError(f"优化算法路径不存在: {single_path}")
                eng.addpath(single_path, nargout=0)
        else:
            identi_path = os.path.join(base_path, 'identification')
            if not os.path.isdir(identi_path):
                raise FileNotFoundError(f"优化算法路径不存在: {identi_path}")
            eng.addpath(identi_path, nargout=0)

    def _validate_optimization_params(self):
        """优化算法参数校验"""
        if self.algorithm == "DE" and self.params["群体粒子个数 (N)"] <= 3:
            raise ValueError("当选择DE优化算法时，群体粒子个数必须大于3")

        if self.algorithm == "IA" and self.params["群体粒子个数 (N)"] % 2 != 0:
            raise ValueError("当选择IA优化算法时，群体粒子个数必须为偶数")

    def _emit_optimization_result(self, gBV, gBpos, time_data, reference0, position):
        try:
            best_value = float(gBV)
            best_pos = [float(x) for x in (gBpos._data if hasattr(gBpos, "_data") else gBpos)]

            time_array = np.array(time_data).flatten()
            ref_array = np.array(reference0).flatten()
            pos_array = np.array(position).flatten()

            self.optimization_finished.emit(
                True, best_value, best_pos, time_array, ref_array, pos_array
            )
        except Exception as e:
            self.error.emit(f"数据转换错误: {str(e)}")
            traceback.print_exc()

    def _emit_multiobjective_result(self, time_data, reference0, position):
        try:
            time_array = np.array(time_data).flatten()
            ref_array = np.array(reference0).flatten()
            pos_array = np.array(position).flatten()

            if len(time_array) == 0 or len(ref_array) == 0 or len(pos_array) == 0:
                raise ValueError("从MATLAB返回的数据为空")

            self.optimization_finished.emit(
                True, 0.0, [], time_array, ref_array, pos_array
            )
        except Exception as e:
            self.error.emit(f"数据转换错误: {str(e)}")
            traceback.print_exc()

    def _run_optimization(self, eng):
        """执行优化算法"""
        self._validate_optimization_params()

        single_objective_map = {
            "GA": "GA_optimization",
            "PSO": "pso_optimization",
            "DE": "DE_optimization",
            "IA": "ia_optimization",
            "FA": "FA_optimization",
            "HPSO": "HPSO_optimization",
        }

        multi_objective_map = {
            "MOGOA": "MOGOA",
            "NONMOGOA": "NONMOGOA",
            "LVMOGOA": "LVMOGOA",
            "MDF_MOGOA": "MDF_MOGOA",
        }

        if self.algorithm in single_objective_map:
            func_name = single_objective_map[self.algorithm]
            matlab_func = getattr(eng, func_name)

            gBV, gBpos, time_data, reference0, position = matlab_func(
                self.params["群体粒子个数 (N)"],
                self.params["粒子维数 (D)"],
                self.params["最大迭代次数 (T)"],
                nargout=5
            )

            self._emit_optimization_result(gBV, gBpos, time_data, reference0, position)

        elif self.algorithm in multi_objective_map:
            func_name = multi_objective_map[self.algorithm]
            matlab_func = getattr(eng, func_name)

            time_data, reference0, position = matlab_func(
                self.params["种群大小 (N)"],
                self.params["存档大小 (ArchiveMaxSize)"],
                self.params["最大迭代次数 (T)"],
                self.params["参数维度 (dim)"],
                self.params["目标函数数量 (obj_no)"],
                nargout=3
            )

            self._emit_multiobjective_result(time_data, reference0, position)

        else:
            raise ValueError(f"未知优化算法: {self.algorithm}")

    def _run_identification(self, eng):
        """执行辨识算法（后台异步调用版）"""
        algorithm_map = {
            "PSO": "pso2",
            "GA": "GA",
            "DE": "de",
            "IA": "ia",
            "FA": "FA",
            "HPSO": "HPSO",
        }

        if self.algorithm not in algorithm_map:
            raise ValueError(f"未知辨识算法: {self.algorithm}")

        matlab_func = getattr(eng, algorithm_map[self.algorithm])

        future = matlab_func(
            self.params["群体粒子个数 (N)"],
            self.params["粒子维数 (D)"],
            self.params["最大迭代次数 (T)"],
            self.params["速度 (vref)"],
            nargout=3,
            background=True
        )

        while not future.done():
            if not self.running:
                return
            time.sleep(0.05)

        gb, g, gbest = future.result()
        self.finished.emit(gb, g, gbest)

    def stop(self):
        """安全停止线程"""
        self.running = False
        self.quit()