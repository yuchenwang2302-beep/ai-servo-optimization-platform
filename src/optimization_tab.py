# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Single- and multi-objective optimization page with the original layout."""
from i18n import tr
import traceback
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFormLayout, QComboBox, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from algorithm_page import AlgorithmPage
from algorithm_catalog import SINGLE, MULTI, OBJECTIVES


class OptimizationTab(AlgorithmPage):
    def __init__(self, parent=None, data_folder=None):
        super().__init__(parent, optimization=True, data_folder=data_folder)
        self.setup_ui()
        self.apply_shadow_effects()

    def apply_shadow_effects(self):
        """为所有需要阴影的部件应用阴影效果"""
        # 主窗口阴影
        # self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)

        # 图像显示区域阴影
        widgets_to_shadow = [
            (self.image_label, 20, 7, QColor(0, 0, 0, 70)),
            (self.convergence_label, 15, 5, QColor(0, 0, 0, 70)),
            (self.tracking_label, 15, 5, QColor(0, 0, 0, 70)),
            (self.info_widget, 15, 5, QColor(0, 0, 0, 70)),
            (self.run_button, 8, 2, QColor(0, 0, 0, 70))
        ]

        for widget, blur, offset, color in widgets_to_shadow:
            if widget is not None:
                effect = QGraphicsDropShadowEffect(widget)
                effect.setBlurRadius(blur)
                effect.setColor(color)
                effect.setOffset(offset, offset)
                widget.setGraphicsEffect(effect)
                widget.setAutoFillBackground(True)

    def setup_ui(self):
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 图像显示区域拆分成两个子图
        self.image_label = QWidget()
        self.image_label.setMinimumSize(400, 500)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        image_layout = QVBoxLayout(self.image_label)
        image_layout.setContentsMargins(5, 5, 5, 5)

        # 适应度进化图
        self.convergence_label = QWidget()
        self.convergence_label.setMinimumSize(390, 245)
        self.convergence_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.convergence_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        convergence_layout = QVBoxLayout(self.convergence_label)
        convergence_layout.setContentsMargins(5, 5, 5, 5)
        image_layout.addWidget(self.convergence_label, 354)

        # 位置跟踪图
        self.tracking_label = QWidget()
        self.tracking_label.setMinimumSize(390, 245)
        self.tracking_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tracking_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        tracking_layout = QVBoxLayout(self.tracking_label)
        tracking_layout.setContentsMargins(5, 5, 5, 5)
        image_layout.addWidget(self.tracking_label, 330)

        # 初始化两个子图
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
        self.init_tracking_plot()

        main_layout.addWidget(self.image_label, 3)

        # 右侧布局
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        main_layout.addLayout(right_layout, 2)

        # ================== 优化后的顶部控制区域 ==================
        top_control_widget = QWidget()
        top_control_widget.setStyleSheet("""
            background-color: #f4f9ff;
            border: 1px solid #a3abbd;
            border-radius: 8px;
        """)

        # 使用网格布局替代垂直布局，更紧凑
        top_control_layout = QGridLayout(top_control_widget)
        top_control_layout.setSpacing(10)
        top_control_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.addWidget(top_control_widget)

        # 第一行：辨识选项
        identification_label = QLabel(tr("辨识选项:"))
        identification_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        top_control_layout.addWidget(identification_label, 0, 0)

        self.identification_combo = QComboBox()
        self.identification_combo.addItem(tr('单目标'), 'single')
        self.identification_combo.addItem(tr('多目标'), 'multi')
        self.identification_combo.setFont(QFont("Microsoft YaHei", 10))
        self.identification_combo.setStyleSheet(self.get_combo_style())
        self.identification_combo.currentTextChanged.connect(self.identification_selected)
        top_control_layout.addWidget(self.identification_combo, 0, 1)

        # 第二行：算法选择
        algorithm_label = QLabel(tr("算法选择:"))
        algorithm_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        top_control_layout.addWidget(algorithm_label, 1, 0)

        self.algorithm_combo = QComboBox()
        self.algorithm_combo.setFont(QFont("Microsoft YaHei", 10))
        self.algorithm_combo.setStyleSheet(self.get_combo_style())
        self.algorithm_combo.currentTextChanged.connect(self.algorithm_selected)
        top_control_layout.addWidget(self.algorithm_combo, 1, 1)

        # 第三行：函数选项
        function_label = QLabel(tr("函数选项:"))
        function_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        top_control_layout.addWidget(function_label, 2, 0)

        self.function_combo = QComboBox()
        # self.function_combo.addItems(["ITSE", "ISE", "IAE", "ITAE"])
        self.function_combo.setFont(QFont("Microsoft YaHei", 10))
        self.function_combo.setStyleSheet(self.get_combo_style())
        top_control_layout.addWidget(self.function_combo, 2, 1)

        # 设置列宽度比例，使标签和下拉框更紧凑
        top_control_layout.setColumnStretch(0, 1)  # 标签列
        top_control_layout.setColumnStretch(1, 2)  # 下拉框列

        # ================== 参数设置区域 ==================
        param_widget = QWidget()
        param_widget.setFixedHeight(220)  # 增加高度
        param_widget.setStyleSheet("""
            background-color: #f4f9ff;
            border: 1px solid #a3abbd;
            border-radius: 8px;
        """)

        param_layout = QVBoxLayout(param_widget)
        param_layout.setSpacing(10)
        param_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.addWidget(param_widget)

        # 参数区域标题
        param_title = QLabel(tr("参数设置"))
        param_title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        param_title.setStyleSheet("color: #1e40af;")
        param_layout.addWidget(param_title)

        # 参数设置滚动区域（增大高度）
        self.param_scroll_area = QScrollArea()
        self.param_scroll_area.setWidgetResizable(True)
        self.param_scroll_area.setFixedHeight(140)  # 增加高度
        self.param_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: #ffffff;
            }
        """)
        param_layout.addWidget(self.param_scroll_area)

        # 参数设置表单
        self.param_form_widget = QWidget()
        self.param_form_layout = QFormLayout(self.param_form_widget)
        self.param_form_layout.setSpacing(10)  # 减小间距
        self.param_form_layout.setContentsMargins(10, 10, 10, 10)
        self.param_scroll_area.setWidget(self.param_form_widget)

        # ================== 运行按钮 ==================
        run_button = QPushButton(tr("运行算法"))
        run_button.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        run_button.setFixedSize(300, 70)
        run_button.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
            """)
        run_button.clicked.connect(self.run_optimization)
        self.run_button = run_button  # 保存对运行按钮的引用
        self.setup_run_controls(right_layout)

        # ================== 信息统计区域 ==================
        self.info_widget = QWidget()
        self.info_widget.setMinimumHeight(170)
        self.info_widget.setStyleSheet("""
            background-color: #dcf3f0;
            border: 1px solid #a3abbd;
            border-radius: 8px;
        """)

        info_layout = QVBoxLayout(self.info_widget)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.addWidget(self.info_widget)

        # 信息统计标题
        info_title = QLabel(tr("算法运行统计"))
        info_title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        info_title.setStyleSheet("color: #1e40af; margin-bottom: 10px;")
        info_layout.addWidget(info_title)

        # 信息统计滚动区域
        self.info_scroll_area = QScrollArea()
        self.info_scroll_area.setWidgetResizable(True)
        self.info_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        info_layout.addWidget(self.info_scroll_area)

        # 信息统计表单
        self.info_form_widget = QWidget()
        self.info_form_layout = QFormLayout(self.info_form_widget)
        self.info_form_layout.setSpacing(8)  # 减小间距
        self.info_form_layout.setContentsMargins(5, 5, 5, 5)
        self.info_scroll_area.setWidget(self.info_form_widget)

        # 设置右侧布局的比例
        right_layout.setStretch(0, 1)  # 顶部控制区域
        right_layout.setStretch(1, 3)  # 参数设置区域
        right_layout.setStretch(2, 1)  # 运行按钮
        right_layout.setStretch(3, 2)  # 信息统计区域

        # 初始化
        self.identification_selected()  # 先根据辨识选项初始化算法选择
        self.init_dynamic_plot()

    def get_combo_style(self):
        """返回统一的ComboBox样式"""
        return """
            QComboBox {
                background-color: #f9fafb;
                border: 1px solid #d1d5db;
                color: #1e40af;
                border-radius: 6px;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #93c5fd;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #d1d5db;
            }
        """

    def init_dynamic_plot(self):
        """初始化动态绘图区域 - 现在分为上下两个子图"""
        # 创建Figure和Canvas for convergence plot
        self.convergence_figure = Figure(figsize=(6.8, 3.2), dpi=100, facecolor='#ffffff')
        self.convergence_canvas = FigureCanvas(self.convergence_figure)

        # 清除并设置布局
        if hasattr(self.convergence_label, 'layout'):
            for i in reversed(range(self.convergence_label.layout().count())):
                self.convergence_label.layout().itemAt(i).widget().setParent(None)
        else:
            self.convergence_label.setLayout(QVBoxLayout())

        self.convergence_label.layout().addWidget(self.convergence_canvas)

        # 设置图形样式 for convergence plot
        self.convergence_ax = self.convergence_figure.add_subplot(111)
        self.convergence_ax.set_facecolor('#f9fafb')
        self.convergence_line, = self.convergence_ax.plot([], [], 'b-', linewidth=2, label=tr('全局最优值'))

        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

        # self.convergence_ax.set_xlabel('迭代次数', fontsize=12)
        self.convergence_ax.set_ylabel(tr('HV（超体积）' if getattr(self, '_run_algorithm', getattr(self, 'current_algorithm', 'PSO')) in MULTI else '适应度值'), fontsize=12)
        self.convergence_ax.set_title(tr('适应度进化图'), fontsize=14, fontweight='bold')

        # 设置图例和网格
        self.convergence_ax.legend(loc='upper right', fontsize=10)
        self.convergence_ax.grid(True, linestyle='--', alpha=0.6)

        # 设置初始坐标范围
        max_iter = 200  # 默认值，实际运行时会从参数获取
        self.convergence_ax.set_xlim(0, max_iter)
        self.convergence_ax.set_ylim(-5, 50)

        # 设置边框颜色
        for spine in self.convergence_ax.spines.values():
            spine.set_edgecolor('#d1d5db')

        self.convergence_canvas.draw()

    def init_tracking_plot(self):
        """初始化位置跟踪图（初始为空）"""
        # 创建Figure和Canvas for tracking plot
        self.tracking_figure = Figure(figsize=(6.8, 3.2), dpi=100, facecolor='#ffffff')
        self.tracking_canvas = FigureCanvas(self.tracking_figure)

        # 清除并设置布局
        if hasattr(self.tracking_label, 'layout'):
            for i in reversed(range(self.tracking_label.layout().count())):
                self.tracking_label.layout().itemAt(i).widget().setParent(None)
        else:
            self.tracking_label.setLayout(QVBoxLayout())

        self.tracking_label.layout().addWidget(self.tracking_canvas)

        # 设置图形样式 for tracking plot
        self.tracking_ax = self.tracking_figure.add_subplot(111)
        self.tracking_ax.set_facecolor('#f9fafb')
        self.ref_line, = self.tracking_ax.plot([], [], 'r-', label=tr('参考位置'))
        self.pos_line, = self.tracking_ax.plot([], [], 'g-', label=tr('实际位置'))
        # self.tracking_ax.set_xlabel('(时间)(s)', fontsize=12)
        self.tracking_ax.set_ylabel(tr('位置'), fontsize=12)
        self.tracking_ax.set_title(tr('位置跟踪效果'), fontsize=14, fontweight='bold')
        self.tracking_ax.legend(loc='upper right', fontsize=10)
        self.tracking_ax.grid(True, linestyle='--', alpha=0.6)
        self.tracking_ax.set_xlim(0, 1)
        self.tracking_ax.set_ylim(0, 1)

        # 设置边框颜色
        for spine in self.tracking_ax.spines.values():
            spine.set_edgecolor('#d1d5db')

        self.tracking_canvas.draw()

    def identification_selected(self):
        """根据选择的辨识选项(单目标/多目标)更新算法选择和函数选项"""
        # 获取当前选择的辨识类型
        identification_type = self.identification_combo.currentData()

        # 先清空算法选择下拉框
        self.algorithm_combo.clear()

        # 清空函数选择下拉框
        self.function_combo.clear()

        if identification_type == 'single':
            # 单目标优化时，添加性能指标选项
            self.function_combo.addItems(list(OBJECTIVES))
            # 添加单目标优化算法
            self.algorithm_combo.addItems(list(SINGLE))
        else:  # 多目标
            # 多目标优化时，添加性能指标选项
            self.function_combo.addItems([tr('超调'), tr('稳态误差'), tr('调整时间')])
            # 添加多目标优化算法
            self.algorithm_combo.addItems(list(MULTI))

        self.function_combo.setEnabled(identification_type == 'single')
        self.function_combo.setToolTip(tr('多目标同时优化稳态误差、超调和调整时间；此处不单独选择。') if identification_type == 'multi' else '')
        # 触发算法参数更新
        self.algorithm_selected()


    def run_optimization(self):
        self.start_run()

    def final_results_received(self, success, gBV, gBpos, time_array, reference0, position):
        """优化完成后的处理"""
        self.data_timer.stop()

        try:
            import time as time_module  # 明确导入time模块并重命名

            # 计算运行时间
            elapsed_time = time_module.time() - self.start_time
            minutes, seconds = divmod(elapsed_time, 60)
            time_str = tr('{minutes}分{seconds:.2f}秒', minutes=int(minutes), seconds=seconds)

            # Read the final save even when the run completes before the next timer tick.
            self.check_data_update()
            self.update_convergence_plot()

            # 根据算法类型显示不同结果
            identification_type = self.identification_combo.currentData()

            if identification_type == 'single':
                results = {
                    "状态": "运行完成",
                    "运行时间": time_str,
                    "目标函数": f"{gBV:.8g}",
                    "最优参数": str([f"{x:.8g}" for x in gBpos])
                }
            elif identification_type == 'multi':
                # 多目标算法（如MOGOA）只显示状态和运行时间
                results = {
                    "状态": "运行完成",
                    "运行时间": time_str
                }

            self.update_info_labels(results)

            # 打印调试信息

            # 更新位置跟踪图
            self.ref_line.set_data(time_array, reference0)
            self.pos_line.set_data(time_array, position)

            # 调整坐标轴范围
            if len(time_array) > 0:
                x_min, x_max = min(time_array), max(time_array)
                y_min = min(min(reference0), min(position))
                y_max = max(max(reference0), max(position))
                y_range = y_max - y_min if y_max != y_min else 1.0

                self.tracking_ax.set_xlim(x_min, x_max)
                self.tracking_ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)

                # 添加标签和标题
                # self.tracking_ax.set_xlabel('时间(s)', fontsize=12)
                self.tracking_ax.set_ylabel(tr('位置'), fontsize=12)
                self.tracking_ax.set_title(tr('位置跟踪效果'), fontsize=14, fontweight='bold')
                self.tracking_ax.legend([tr('参考位置'), tr('实际位置')], loc='upper right')
                self.tracking_ax.grid(True, linestyle='--', alpha=0.6)

                # 强制重绘
                self.tracking_canvas.draw()

            self.parent_window.statusBar().showMessage(tr('计算完成。'))

        except Exception as e:
            error_msg = tr('结果处理错误: {error}', error=e) + '\n' + traceback.format_exc()
            self.parent_window.statusBar().showMessage(error_msg)
            print(error_msg)
