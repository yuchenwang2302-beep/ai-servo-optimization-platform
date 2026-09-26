# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Validation and MAT-file reading shared by the existing two pages."""
from i18n import tr
import ast
import math
import numpy as np
from scipy.io import loadmat
from algorithm_catalog import IDENTIFICATION, SINGLE, MULTI, OBJECTIVES


class ParameterValidationError(ValueError):
    def __init__(self, errors):
        self.field_errors = errors
        super().__init__('\n'.join(errors.values()))


def parameter_rules(algorithm, optimization=False):
    multi = optimization and algorithm in MULTI
    rules = {'最大迭代次数 (T)': (1, 100000)}
    if multi:
        rules.update({'种群大小 (N)': (2, 10000), '存档大小 (ArchiveMaxSize)': (1, 10000),
                      '参数维度 (dim)': (11, 11), '目标函数数量 (obj_no)': (3, 3)})
    else:
        dimension = 11 if optimization else 10
        rules.update({'群体粒子个数 (N)': (4 if algorithm == 'DE' else 2, 10000),
                      '粒子维数 (D)': (dimension, dimension)})
    return rules


def validate_params(algorithm, values, optimization=False):
    params = dict(values)
    errors = {}
    multi = optimization and algorithm in MULTI
    if algorithm not in (tuple(SINGLE) + MULTI if optimization else IDENTIFICATION):
        raise ParameterValidationError({'algorithm': tr('请选择有效的算法。')})
    for name, (lower, upper) in parameter_rules(algorithm, optimization).items():
        try:
            raw = params[name]
            value = int(raw)
            if isinstance(raw, bool) or float(raw) != value or not lower <= value <= upper:
                raise ValueError()
            params[name] = value
        except (ValueError, TypeError, KeyError, OverflowError):
            if lower == upper:
                errors[name] = tr('{name} 由模型固定为 {value}，无需修改。', name=tr(name), value=lower)
            else:
                errors[name] = tr('{name} 请输入 {lower}–{upper} 的整数。', name=tr(name), lower=lower, upper=upper)
    population_key = '种群大小 (N)' if multi else '群体粒子个数 (N)'
    if population_key not in errors and algorithm == 'IA' and params[population_key] % 2:
        errors[population_key] = tr('IA 的种群数量必须为偶数，例如 40 或 100。')
    if optimization:
        if not multi and params.get('objective', 'ITSE') not in OBJECTIVES:
            errors['objective'] = tr('请选择 ITSE、ISE、IAE 或 ITAE。')
    else:
        try:
            raw = params['速度 (vref)']
            speed = float(raw)
            if isinstance(raw, bool) or not math.isfinite(speed) or speed <= 0:
                raise ValueError()
            params['速度 (vref)'] = speed
        except (ValueError, TypeError, KeyError, OverflowError):
            errors['速度 (vref)'] = tr('速度 (vref) 必须是大于零的有限数值。')
        bounds = []
        for index in range(1, 6):
            keys = [key for key in params if key.endswith(f'(t{index}L)')]
            if len(keys) != 1:
                errors[f't{index}L'] = tr('缺少第 {index} 组辨识范围。', index=index)
                continue
            name = keys[0]
            try:
                pair = ast.literal_eval(params[name]) if isinstance(params[name], str) else params[name]
                if not isinstance(pair, (list, tuple)) or len(pair) != 2 or any(isinstance(x, bool) for x in pair):
                    raise ValueError()
                low, high = map(float, pair)
                if not all(map(math.isfinite, (low, high))) or not 0 < low < high:
                    raise ValueError()
                bounds.append([low, high])
            except (ValueError, TypeError, SyntaxError, OverflowError):
                errors[name] = tr('{name} 请输入 [下限, 上限]，且 0 < 下限 < 上限；支持科学计数法。', name=tr(name))
        params['parameter_bounds'] = bounds
    if errors:
        raise ParameterValidationError(errors)
    return params


def read_curve(path):
    data = loadmat(str(path))
    values = np.asarray(data['gBV_record'], dtype=float).reshape(-1)
    count = max(0, min(int(np.asarray(data['iter']).item()), len(values)))
    return values[:count]


def validate_tracking(*values):
    arrays = tuple(np.asarray(value, dtype=float).reshape(-1) for value in values)
    if len(arrays) != 3 or not arrays[0].size or len({x.size for x in arrays}) != 1:
        raise ValueError(tr('时间、参考位置和实际位置的数据长度不一致或为空。'))
    if not all(np.isfinite(x).all() for x in arrays) or np.any(np.diff(arrays[0]) < 0):
        raise ValueError(tr('位置跟踪结果含无效数值或时间顺序异常。'))
    return arrays
