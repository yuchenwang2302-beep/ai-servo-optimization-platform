# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""UI translations; internal parameter keys and MATLAB contracts stay unchanged."""
from PyQt5.QtCore import QSettings

APP_NAME = 'AI Servo Optimization Platform'
LANGUAGES = (('中文', 'zh'), ('English', 'en'))
_language = 'zh'

EN = {
    '语言': 'Language',
    '登录界面': 'Sign in',
    '登录': 'Sign in',
    '欢迎使用': 'Welcome',
    '参数辨识 · 控制优化': 'Parameter identification · Control optimization',
    '登录以进入伺服系统研究工作台。': 'Sign in to your servo-system research workspace.',
    '请输入账号': 'Enter your username',
    '请输入密码': 'Enter your password',
    '显示密码': 'Show password',
    '隐藏密码': 'Hide password',
    '演示账号与密码均为 111': 'Demo username and password: 111',
    '账号': 'Username',
    '密码': 'Password',
    '登录失败': 'Sign-in failed',
    '账号或密码错误，请检查后重试。': 'Incorrect username or password. Please try again.',
    '返回登录': 'Try again',
    '辨识算法': 'Identification',
    '优化算法': 'Optimization',
    '选择算法：': 'Select algorithm:',
    '辨识选项:': 'Mode:',
    '算法选择:': 'Algorithm:',
    '函数选项:': 'Objective:',
    '单目标': 'Single objective',
    '多目标': 'Multi-objective',
    '参数设置': 'Parameters',
    '算法运行统计': 'Run summary',
    '群体粒子个数 (N)': 'Population size (N)',
    '种群大小 (N)': 'Population size (N)',
    '粒子维数 (D)': 'Dimensions (D)',
    '最大迭代次数 (T)': 'Max. iterations (T)',
    '速度 (vref)': 'Speed (vref)',
    'Lq轴电感范围(t1L)': 'Lq range (t1L)',
    'Ld轴电感范围(t2L)': 'Ld range (t2L)',
    '电阻范围(t3L)': 'Resistance (t3L)',
    '磁链范围(t4L)': 'Flux linkage (t4L)',
    '机械参数范围(t5L)': 'Mechanical (t5L)',
    '存档大小 (ArchiveMaxSize)': 'Archive size',
    '参数维度 (dim)': 'Dimensions (dim)',
    '目标函数数量 (obj_no)': 'Objectives (obj_no)',
    '运行算法': 'Run algorithm',
    '重新运行': 'Run again',
    '停止计算': 'Stop',
    '最长计算': 'Time limit',
    ' 分钟': ' min',
    '查看日志': 'Open logs',
    '尚未运行': 'Not started',
    '%v / %m 次迭代': '%v / %m iterations',
    '已用时 {hours:02d}:{minutes:02d}:{seconds:02d}': 'Elapsed {hours:02d}:{minutes:02d}:{seconds:02d}',
    '从开始计算计时。达到时限后停止本次任务；MATLAB 启动与退出另设保护时限。':
        'Measured from the start of computation. Reaching the limit triggers a stop. MATLAB startup and shutdown have separate time limits.',
    '完成一次迭代后更新进度与曲线。': 'Progress and the curve update after completed iterations are saved.',
    '请修正红色标记的 {count} 项参数后再运行。': 'Correct the {count} highlighted field(s) before running.',
    '请检查输入参数': 'Check input parameters',
    '返回修改': 'Edit parameters',
    '模型固定参数，无需修改。': 'Fixed by the model; no editing is required.',
    '请输入 {lower}–{upper} 的整数。': 'Enter an integer from {lower} to {upper}.',
    ' IA 要求偶数。': ' IA requires an even population size.',
    '格式：[下限, 上限]，两者为正且下限小于上限；支持科学计数法。':
        'Use [lower, upper] with 0 < lower < upper. Scientific notation is supported.',
    '已有算法正在运行，请等待完成。': 'An algorithm is already running. Wait for it to finish.',
    '参数错误：{error}': 'Invalid parameters: {error}',
    '计算规模较大': 'Large computation',
    '当前种群、存档或迭代设置可能需要较长计算时间，并占用较多内存。建议先用较小设置验证。\n\n本次最长计算时间：{minutes} 分钟。是否继续？':
        'The selected population, archive or iteration count may require substantial time and memory. Consider testing with smaller values first.\n\nComputation time limit: {minutes} min. Continue?',
    '继续计算': 'Continue',
    '状态': 'Status',
    '已停止': 'Stopped',
    '完成迭代': 'Iterations saved',
    '说明': 'Details',
    '本次未生成完整结果，可调整参数后重新运行。': 'No complete result was produced. Adjust the parameters and run again.',
    '运行完成': 'Completed',
    '运行失败': 'Failed',
    '运行超时': 'Timed out',
    '运行时间': 'Elapsed time',
    '错误详情': 'Error details',
    '目标函数': 'Objective value',
    '最优个体': 'Best solution',
    '最优参数': 'Best parameters',
    '{minutes}分{seconds:.2f}秒': '{minutes} min {seconds:.2f} s',
    '{seconds:.2f}秒': '{seconds:.2f} s',
    '算法错误：{error}': 'Computation error: {error}',
    '结果处理错误: {error}': 'Could not display the result: {error}',
    '暂时无法读取曲线数据，计算仍在继续；可查看日志。': 'Curve data is temporarily unavailable. Computation continues; see the logs for details.',
    '曲线包含无效数值。': 'The curve contains invalid values.',
    '迭代次数': 'Iteration',
    '适应度值': 'Fitness',
    '适应度进化图': 'Fitness convergence',
    '{algorithm} 适应度进化图': '{algorithm} fitness convergence',
    '全局最优值': 'Global best',
    'HV（超体积）': 'HV (hypervolume)',
    '参考位置': 'Reference position',
    '实际位置': 'Actual position',
    '位置': 'Position',
    '位置跟踪效果': 'Position tracking',
    '超调': 'Overshoot',
    '稳态误差': 'Steady-state error',
    '调整时间': 'Settling time',
    '多目标同时优化稳态误差、超调和调整时间；此处不单独选择。':
        'Multi-objective mode optimizes steady-state error, overshoot and settling time together. No individual selection is needed.',
    '请等待本次计算退出。': 'Please wait for this computation to exit.',
    '计算尚未结束': 'Computation in progress',
    '停止本次计算并关闭窗口？未完成的任务不会生成最终结果。':
        'Stop this computation and close the window? An unfinished run will not produce a final result.',
    '停止并关闭': 'Stop and close',
    '继续运行': 'Keep running',
    '计算已结束，是否关闭窗口？': 'The computation has finished. Close the window?',
    '关闭窗口': 'Close window',
    '请选择有效的算法。': 'Select a valid algorithm.',
    '{name} 由模型固定为 {value}，无需修改。': '{name} is fixed at {value} by the model.',
    '{name} 请输入 {lower}–{upper} 的整数。': '{name}: enter an integer from {lower} to {upper}.',
    'IA 的种群数量必须为偶数，例如 40 或 100。': 'IA requires an even population size, such as 40 or 100.',
    '请选择 ITSE、ISE、IAE 或 ITAE。': 'Select ITSE, ISE, IAE or ITAE.',
    '速度 (vref) 必须是大于零的有限数值。': 'Speed (vref) must be a finite number greater than zero.',
    '缺少第 {index} 组辨识范围。': 'Identification range {index} is missing.',
    '{name} 请输入 [下限, 上限]，且 0 < 下限 < 上限；支持科学计数法。':
        '{name}: enter [lower, upper] with 0 < lower < upper. Scientific notation is supported.',
    '时间、参考位置和实际位置的数据长度不一致或为空。': 'Time, reference position and actual position arrays are empty or have different lengths.',
    '位置跟踪结果含无效数值或时间顺序异常。': 'Tracking data contains invalid values or unordered timestamps.',
    '正在启动 MATLAB…': 'Starting MATLAB…',
    '正在计算，完成迭代后更新曲线…': 'Computing; the curve updates after completed iterations are saved…',
    '正在停止本次计算并清理资源…': 'Stopping this computation and releasing resources…',
    '正在释放 MATLAB 资源…': 'Releasing MATLAB resources…',
    '计算结束，正在完成线程清理。': 'Computation finished; completing cleanup.',
    '计算完成。': 'Computation complete.',
    '计算已停止；未生成完整结果。': 'Computation stopped; no complete result was produced.',
    ' 已回收本次后台进程。': ' This run’s background processes have been closed.',
    '计算未完成。': 'Computation did not finish.',
    '运行时限必须为大于零的有限数值。': 'Time limits must be finite numbers greater than zero.',
    '计算结果包含无效数值。': 'The result contains invalid values.',
    '最终收敛数据缺失或不完整，请查看本次运行日志。': 'Final convergence data is missing or incomplete. See the run logs.',
    '辨识结果与最终曲线不一致。': 'The identification result does not match the final curve.',
    'MATLAB 未进入本次任务的进程保护范围，已中止启动。': 'MATLAB could not be contained in this run’s process group. Startup was aborted.',
    '计算进程异常退出（代码 {code}），请查看日志后重新运行。': 'The computation process exited unexpectedly (code {code}). Check the logs before running again.',
    '计算进程未返回完整结果，请查看日志后重新运行。': 'The computation process did not return a complete result. Check the logs before running again.',
    'MATLAB 启动': 'MATLAB startup',
    '计算': 'Computation',
    '资源清理': 'Cleanup',
    '任务': 'The task',
    '{stage}超过设定时限，已停止本次任务。可查看日志、调整时限后重新运行。': '{stage} exceeded its time limit. The run has stopped. Check the logs and adjust the limit before running again.',
    '资源清理失败：{error}': 'Cleanup failed: {error}',
    '后台进程未能按时退出，请查看日志。': 'The background process did not exit in time. See the logs.',
    'MATLAB 启动超过 3 分钟，请先打开 MATLAB 检查登录授权后重试。': 'MATLAB startup exceeded 3 minutes. Open MATLAB and check your sign-in and license before retrying.',
    'MATLAB 资源释放失败：{error}': 'Could not release MATLAB resources: {error}',
    'MATLAB Engine 不可用，请为当前 Python 安装与本机 MATLAB 匹配的 Engine。': 'MATLAB Engine is unavailable. Install an Engine version matching MATLAB for this Python environment.',
    'MATLAB 脚本目录不存在：{folder}': 'MATLAB script directory not found: {folder}',
    '缺少 MATLAB 函数或模型：{names}': 'Missing MATLAB functions or models: {names}',
    '算法没有返回有效的最优值或参数，请检查模型和搜索范围。': 'The algorithm returned an invalid best value or parameters. Check the model and search bounds.',
    '辨识收敛曲线不完整或含无效数值。': 'The identification curve is incomplete or contains invalid values.',
    '无法恢复本次计算进程的启动线程。': 'Could not resume this computation process.',
    '本次计算进程仍在退出，请查看运行日志。': 'This computation process is still exiting. See the run logs.',
    '本次计算的子进程未能按时退出。': 'A child process of this run did not exit in time.',
    '本次 MATLAB 后台进程未能退出。': 'This run’s MATLAB process did not exit.',
    '{stage}超过设定时限，正在停止本次计算并清理资源…': '{stage} exceeded its time limit. Stopping the computation and releasing resources…',
    '计算耗时 {calculation} / 总耗时 {total}': 'Compute {calculation} / Total {total}',
    '计算耗时': 'Compute time',
    '总耗时': 'Total time',
    '运行记录': 'Run history',
    '自动清理过期记录，额外保留最新 20 次；归档记录和未结束任务不会删除。7 天前已结束任务的仿真缓存可自动清理。': 'Expired runs are removed, with the latest 20 kept. Archived and unfinished runs are protected. Simulation caches from runs finished over 7 days ago can be cleared.',
    '自动清理': 'Automatic cleanup',
    '保留最近': 'Keep the last',
    ' 天': ' days',
    '保存设置': 'Save settings',
    '运行日期': 'Run date',
    '算法': 'Algorithm',
    '类型': 'Type',
    '归档': 'Archive',
    '已归档': 'Archived',
    '状态未知': 'Unknown',
    '正在计算': 'Computing',
    '正在停止': 'Stopping',
    '打开记录文件夹': 'Open run folder',
    '归档 / 取消归档': 'Archive / Unarchive',
    '刷新': 'Refresh',
    '按规则清理': 'Clean up by policy',
    '正在读取运行记录…': 'Loading run history…',
    '正在处理运行记录…': 'Processing run history…',
    '记录操作未完成：{error}': 'History operation did not finish: {error}',
    '已清理 {runs} 次旧运行、{caches} 项缓存，释放 {size:.1f} MiB。': 'Removed {runs} old runs and {caches} caches; freed {size:.1f} MiB.',
    ' {count} 项未能清理，已跳过。': ' Skipped {count} items that could not be cleaned.',
    '共 {count} 次运行。归档会保留整次运行的文件。': '{count} runs. Archiving protects all files in a run.',
    '结果文件不可读，请打开记录文件夹检查。': 'The result file could not be read. Check the run folder.',
    '清理设置已保存，下次自动检查时生效。': 'Retention settings saved for the next automatic check.',
}


def _settings():
    return QSettings(QSettings.IniFormat, QSettings.UserScope, 'AIServoOptimizationPlatform', 'Interface')


def language():
    return _language


def set_language(code, *, persist=False):
    global _language
    _language = code if code in ('zh', 'en') else 'zh'
    if persist:
        settings = _settings()
        settings.setValue('language', _language)
        settings.sync()


def load_language():
    set_language(_settings().value('language', 'zh'))
    return language()


def tr(source, **values):
    text = EN.get(source, source) if _language == 'en' else source
    return text.format(**values) if values else text
