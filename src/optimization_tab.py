# d:\Users\Desktop\PyQTproject3\src\optimization_tab.py

import sys
import matlab.engine
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFormLayout, QLineEdit, QComboBox, \
    QScrollArea, QTextEdit, QFrame, QGridLayout, QApplication
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
import json
import numpy as np
import time
import subprocess
import scipy.io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import traceback
import os
from matlab_worker import MatlabWorker
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor


class OptimizationTab(QWidget):
    data_ready = pyqtSignal(int, np.ndarray)  # 迭代次数, 适应度记录
    finished = pyqtSignal(bool, float, list, np.ndarray, np.ndarray,
                          np.ndarray)  # 成功标志, 最优值, 最优参数, time, reference0, position

    def __init__(self, parent=None, data_folder=r"D:\Coding_Projects\python\PyQTproject3\temp_data"):
        super().__init__(parent)
        self.parent_window = parent
        self.data_folder = data_folder
        self.setup_ui()
        self.data_files = {
            "PSO": "pso_temp_data.mat",
            "GA": "ga_temp_data.mat",
            "DE": "DE_temp_data.mat",
            "IA": "ia_temp_data.mat",
            "FA": "FA_temp_data.mat",
            "HPSO": "HPSO_temp_data.mat",
            "MOGOA": "MOGOA_temp_data.mat",
            "NONMOGOA": "NONMOGOA_temp_data.mat",
            "LVMOGOA": "LVMOGOA_temp_data.mat",
            "MDF_MOGOA": "MDF_MOGOA_temp_data.mat",
            # "NSGA-II": "NSGA-II_temp_data.mat",
        }
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.check_data_update)
        self.last_update_iter = 0
        self.gb_data = np.array([])

        # 添加阴影效果
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
            (self.findChild(QWidget, "top_control_widget"), 15, 5, QColor(0, 0, 0, 70)),
            (self.findChild(QWidget, "param_widget"), 15, 5, QColor(0, 0, 0, 70)),
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
        self.image_label.setFixedSize(700, 700)
        self.image_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        image_layout = QVBoxLayout(self.image_label)
        image_layout.setContentsMargins(5, 5, 5, 5)

        # 适应度进化图
        self.convergence_label = QWidget()
        self.convergence_label.setFixedSize(690, 354)
        self.convergence_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        convergence_layout = QVBoxLayout(self.convergence_label)
        convergence_layout.setContentsMargins(5, 5, 5, 5)
        image_layout.addWidget(self.convergence_label)

        # 位置跟踪图
        self.tracking_label = QWidget()
        self.tracking_label.setFixedSize(690, 330)
        self.tracking_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        tracking_layout = QVBoxLayout(self.tracking_label)
        tracking_layout.setContentsMargins(5, 5, 5, 5)
        image_layout.addWidget(self.tracking_label)

        # 初始化两个子图
        self.init_dynamic_plot()
        self.init_tracking_plot()

        main_layout.addWidget(self.image_label)

        # 右侧布局
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        main_layout.addLayout(right_layout)

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
        identification_label = QLabel("辨识选项:")
        identification_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        top_control_layout.addWidget(identification_label, 0, 0)

        self.identification_combo = QComboBox()
        self.identification_combo.addItems(["单目标", "多目标"])
        self.identification_combo.setFont(QFont("Microsoft YaHei", 10))
        self.identification_combo.setStyleSheet(self.get_combo_style())
        self.identification_combo.currentTextChanged.connect(self.identification_selected)
        top_control_layout.addWidget(self.identification_combo, 0, 1)

        # 第二行：算法选择
        algorithm_label = QLabel("算法选择:")
        algorithm_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        top_control_layout.addWidget(algorithm_label, 1, 0)

        self.algorithm_combo = QComboBox()
        self.algorithm_combo.setFont(QFont("Microsoft YaHei", 10))
        self.algorithm_combo.setStyleSheet(self.get_combo_style())
        self.algorithm_combo.currentTextChanged.connect(self.algorithm_selected)
        top_control_layout.addWidget(self.algorithm_combo, 1, 1)

        # 第三行：函数选项
        function_label = QLabel("函数选项:")
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
        param_title = QLabel("参数设置")
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
        run_button = QPushButton("运行算法")
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
        right_layout.addWidget(run_button, 0, Qt.AlignHCenter)  # 水平居中
        self.run_button = run_button  # 保存对运行按钮的引用

        # ================== 信息统计区域 ==================
        self.info_widget = QWidget()
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
        info_title = QLabel("算法运行统计")
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
        self.convergence_line, = self.convergence_ax.plot([], [], 'b-', linewidth=2, label='全局最优值')

        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

        # self.convergence_ax.set_xlabel('迭代次数', fontsize=12)
        self.convergence_ax.set_ylabel('适应度值', fontsize=12)
        self.convergence_ax.set_title('适应度进化图', fontsize=14, fontweight='bold')

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

        # # 初始化位置跟踪图（初始为空）
        # self.init_tracking_plot()

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
        self.ref_line, = self.tracking_ax.plot([], [], 'r-', label='参考位置')
        self.pos_line, = self.tracking_ax.plot([], [], 'g-', label='实际位置')
        # self.tracking_ax.set_xlabel('(时间)(s)', fontsize=12)
        self.tracking_ax.set_ylabel('位置', fontsize=12)
        self.tracking_ax.set_title('位置跟踪效果', fontsize=14, fontweight='bold')
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
        identification_type = self.identification_combo.currentText()

        # 先清空算法选择下拉框
        self.algorithm_combo.clear()

        # 清空函数选择下拉框
        self.function_combo.clear()

        if identification_type == "单目标":
            # 单目标优化时，添加性能指标选项
            self.function_combo.addItems(["ITSE", "ISE", "IAE", "ITAE"])
            # 添加单目标优化算法
            self.algorithm_combo.addItems(["PSO", "GA", "DE", "IA", "FA", "HPSO"])
        else:  # 多目标
            # 多目标优化时，添加性能指标选项
            self.function_combo.addItems(["超调", "稳态误差", "调整时间"])
            # 添加多目标优化算法
            self.algorithm_combo.addItems(["MOGOA", "NONMOGOA", "LVMOGOA", "MDF_MOGOA"])

        # 触发算法参数更新
        self.algorithm_selected()

    def algorithm_selected(self):
        while self.param_form_layout.count():
            child = self.param_form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        algorithm = self.algorithm_combo.currentText()
        self.current_algorithm = algorithm

        identification_type = self.identification_combo.currentText()

        if identification_type == "单目标":
            if algorithm == "PSO":
                self.setup_pso_params()
            elif algorithm == "GA":
                self.setup_ga_params()
            elif algorithm == "DE":
                self.setup_de_params()
            elif algorithm == "IA":
                self.setup_ia_params()
            elif algorithm == "FA":
                self.setup_fa_params()
            elif algorithm == "HPSO":
                self.setup_hpso_params()
        else:  # 多目标
            if algorithm == "MOGOA":
                self.setup_multi_obj_MOGOA_params()
            elif algorithm == "NONMOGOA":
                self.setup_multi_obj_NONMOGOA_params()
            elif algorithm == "LVMOGOA":
                self.setup_multi_obj_LVMOGOA_params()
            elif algorithm == "MDF_MOGOA":
                self.setup_multi_obj_MDF_MOGOA_params()

    def setup_pso_params(self):
        self.params = {
            "群体粒子个数 (N)": QLineEdit("50"),
            "粒子维数 (D)": QLineEdit("11"),
            "最大迭代次数 (T)": QLineEdit("50"),
        }
        self.add_params_to_form()

    def setup_ga_params(self):
        self.params = {
            "群体粒子个数 (N)": QLineEdit("50"),
            "粒子维数 (D)": QLineEdit("11"),
            "最大迭代次数 (T)": QLineEdit("50"),
        }
        self.add_params_to_form()

    def setup_de_params(self):
        self.params = {
            "群体粒子个数 (N)": QLineEdit("50"),
            "粒子维数 (D)": QLineEdit("11"),
            "最大迭代次数 (T)": QLineEdit("50"),
            # "速度 (vref)": QLineEdit("200"),
            # "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            # "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            # "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            # "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            # "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),
        }
        self.add_params_to_form()

    def setup_ia_params(self):
        self.params = {
            "群体粒子个数 (N)": QLineEdit("50"),
            "粒子维数 (D)": QLineEdit("11"),
            "最大迭代次数 (T)": QLineEdit("50"),
        }
        self.add_params_to_form()

    def setup_fa_params(self):
        self.params = {
            "群体粒子个数 (N)": QLineEdit("20"),
            "粒子维数 (D)": QLineEdit("11"),
            "最大迭代次数 (T)": QLineEdit("50"),
            # "速度 (vref)": QLineEdit("3200"),
            # "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            # "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            # "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            # "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            # "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),
        }
        self.add_params_to_form()

    def setup_hpso_params(self):
        self.params = {
            "群体粒子个数 (N)": QLineEdit("50"),
            "粒子维数 (D)": QLineEdit("11"),
            "最大迭代次数 (T)": QLineEdit("50"),
            # "速度 (vref)": QLineEdit("200"),
            # "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            # "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            # "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            # "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            # "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),
        }
        self.add_params_to_form()

    def setup_multi_obj_MOGOA_params(self):
        self.params = {
            "种群大小 (N)": QLineEdit("50"),
            "存档大小 (ArchiveMaxSize)": QLineEdit("150"),
            "最大迭代次数 (T)": QLineEdit("20"),
            "参数维度 (dim)": QLineEdit("11"),
            "目标函数数量 (obj_no)": QLineEdit("3"),
        }
        self.add_params_to_form()

    def setup_multi_obj_NONMOGOA_params(self):
        self.params = {
            "种群大小 (N)": QLineEdit("50"),
            "存档大小 (ArchiveMaxSize)": QLineEdit("150"),
            "最大迭代次数 (T)": QLineEdit("20"),
            "参数维度 (dim)": QLineEdit("11"),
            "目标函数数量 (obj_no)": QLineEdit("3"),
        }
        self.add_params_to_form()

    def setup_multi_obj_LVMOGOA_params(self):
        self.params = {
            "种群大小 (N)": QLineEdit("50"),
            "存档大小 (ArchiveMaxSize)": QLineEdit("150"),
            "最大迭代次数 (T)": QLineEdit("20"),
            "参数维度 (dim)": QLineEdit("11"),
            "目标函数数量 (obj_no)": QLineEdit("3"),
        }
        self.add_params_to_form()

    def setup_multi_obj_MDF_MOGOA_params(self):
        self.params = {
            "种群大小 (N)": QLineEdit("100"),
            "存档大小 (ArchiveMaxSize)": QLineEdit("150"),
            "最大迭代次数 (T)": QLineEdit("20"),
            "参数维度 (dim)": QLineEdit("11"),
            "目标函数数量 (obj_no)": QLineEdit("3"),
        }
        self.add_params_to_form()

    def add_params_to_form(self):
        for key, value in self.params.items():
            label = QLabel(key)
            label.setFont(QFont("Microsoft YaHei", 12))
            label.setStyleSheet("font: 12pt 'Microsoft YaHei'; color: #24898f;")
            self.param_form_layout.addRow(label, value)

    def run_optimization(self):
        try:
            # 1. 初始化状态
            self.last_update_iter = 0
            self.gb_data = np.array([])
            self.start_time = time.time()

            # 清除当前算法对应的旧数据文件
            current_data_file = self.data_files.get(self.current_algorithm)
            if current_data_file and os.path.exists(current_data_file):
                try:
                    os.remove(current_data_file)
                except Exception as e:
                    self.parent_window.statusBar().showMessage(f"删除旧数据文件失败: {str(e)}")
                    return

            # 2. 获取并验证参数
            params = {}
            try:
                # 获取所有参数值
                for key, widget in self.params.items():
                    if isinstance(widget, QLineEdit):
                        params[key] = widget.text()
                    elif isinstance(widget, QComboBox):
                        params[key] = widget.currentText()

                # 根据算法类型设置不同的强制转换参数
                identification_type = self.identification_combo.currentText()

                if identification_type == "单目标":
                    # 单目标算法的参数转换
                    required_params = {
                        "群体粒子个数 (N)": int,
                        "粒子维数 (D)": int,
                        "最大迭代次数 (T)": int
                    }
                else:
                    # 多目标算法的参数转换
                    if identification_type == "多目标":
                        required_params = {
                            "种群大小 (N)": int,
                            "存档大小 (ArchiveMaxSize)": int,
                            "最大迭代次数 (T)": int,
                            "参数维度 (dim)": int,
                            "目标函数数量 (obj_no)": int
                        }

                # 强制转换关键参数类型
                for param, dtype in required_params.items():
                    if param in params:  # 确保参数存在
                        params[param] = dtype(params[param])
                    else:
                        raise ValueError(f"缺少必要参数: {param}")

            except ValueError as e:
                self.parent_window.statusBar().showMessage(f"参数错误: 请检查数值格式 ({str(e)})")
                return
            except Exception as e:
                self.parent_window.statusBar().showMessage(f"参数获取失败: {str(e)}")
                return

            # 3. 重置UI状态
            # 清空收敛图
            self.convergence_ax.clear()
            # self.convergence_ax.set_xlabel('迭代次数', fontsize=12)
            self.convergence_ax.set_ylabel('适应度值', fontsize=12)
            self.convergence_ax.set_title(f'{self.current_algorithm} 适应度进化图', fontsize=14, fontweight='bold')
            self.convergence_ax.grid(True)
            self.convergence_ax.set_xlim(0, params["最大迭代次数 (T)"])
            self.convergence_canvas.draw()

            # 清空位置跟踪图
            self.tracking_ax.clear()
            # self.tracking_ax.set_xlabel('时间(s)', fontsize=12)
            self.tracking_ax.set_ylabel('位置', fontsize=12)
            self.tracking_ax.set_title('位置跟踪效果', fontsize=14, fontweight='bold')
            self.tracking_ax.grid(True)
            self.tracking_ax.set_xlim(0, 1)
            self.tracking_ax.set_ylim(0, 1)
            # 重新初始化曲线对象
            self.ref_line, = self.tracking_ax.plot([], [], 'r-', label='参考位置')
            self.pos_line, = self.tracking_ax.plot([], [], 'g-', label='实际位置')
            self.tracking_ax.legend(loc='upper right')

            self.tracking_canvas.draw()

            # 清空信息面板
            self.clear_info_labels()
            self.add_info_label("状态", "算法运行中...")

            # 4. 启动MATLAB工作线程
            if hasattr(self, 'worker') and self.worker.isRunning():
                self.worker.stop()

            # 优化算法调用
            self.worker = MatlabWorker(
                algorithm=self.current_algorithm,
                params=params,
                is_optimization=True  # 设置标志位
            )
            self.worker.optimization_finished.connect(self.final_results_received)
            self.worker.error.connect(self.handle_worker_error)
            self.worker.start()

            # 5. 启动数据监视定时器
            self.data_timer.start(1000)  # 每1000ms检查一次

            # 禁用运行按钮
            self.run_button.setEnabled(False)

            # 更新状态栏
            self.parent_window.statusBar().showMessage(f"正在运行 {self.current_algorithm} 算法")

        except Exception as e:
            error_msg = f"运行失败: {str(e)}\n{traceback.format_exc()}"
            self.parent_window.statusBar().showMessage(error_msg)
            print(error_msg)

    def update_convergence_plot(self):
        """根据最新数据更新适应度进化图"""
        if len(self.gb_data) == 0:
            return

        try:
            # 清除图形但保留坐标设置
            self.convergence_ax.clear()

            # 重新设置图形属性
            # self.convergence_ax.set_xlabel('迭代次数', fontsize=12)
            self.convergence_ax.set_ylabel('适应度值', fontsize=12)
            self.convergence_ax.set_title(f'{self.current_algorithm} 适应度进化图', fontsize=14, fontweight='bold')
            self.convergence_ax.grid(True, linestyle='--', alpha=0.6)

            # 只绘制实际发生的数据点
            valid_indices = ~np.isnan(self.gb_data)
            x_data = np.arange(len(self.gb_data))[valid_indices]
            y_data = self.gb_data[valid_indices]

            # 只绘制有数据的部分
            if len(x_data) > 0:
                self.convergence_line, = self.convergence_ax.plot(x_data, y_data, 'b-', linewidth=2, label='全局最优值')

                # 固定x轴范围为0到最大迭代次数（从参数中获取）
                max_iter = int(self.params["最大迭代次数 (T)"].text())
                self.convergence_ax.set_xlim(0, max_iter)

                # 自动调整y轴范围，留出10%的边距
                y_min, y_max = np.min(y_data), np.max(y_data)
                y_range = y_max - y_min
                if y_range == 0:  # 处理所有值相同的情况
                    y_range = 1
                    y_min -= 0.5
                    y_max += 0.5
                margin = y_range * 0.1
                self.convergence_ax.set_ylim(y_min - margin, y_max + margin)

            # 更新图例
            self.convergence_ax.legend(loc='upper right')

            # 强制重绘
            self.convergence_canvas.draw()

        except Exception as e:
            print(f"更新适应度进化图错误: {e}")

    def check_data_update(self):
        """检查MATLAB数据文件是否有更新"""
        try:
            if not hasattr(self, 'last_update_iter') or not hasattr(self, 'gb_data'):
                return

            current_data_file = self.data_files.get(self.current_algorithm)
            if not current_data_file or not os.path.exists(current_data_file):
                return

            # 加载MATLAB数据
            data = scipy.io.loadmat(current_data_file)
            gb_record = data['gBV_record'].flatten()
            current_iter = data['iter'][0, 0]

            # 确保current_iter不超过数组长度
            current_iter = min(current_iter, len(gb_record) - 1)

            # 如果数据有更新
            if current_iter > self.last_update_iter:
                self.last_update_iter = current_iter
                # 只保留实际计算过的数据点
                self.gb_data = gb_record[:current_iter + 1]  # +1因为MATLAB索引从1开始

                # 过滤掉零值（假设适应度值不会真正为零）
                # 或者更好的方法是使用MATLAB中的NaN来填充未计算的部分
                self.gb_data = np.where(self.gb_data == 0, np.nan, self.gb_data)

                self.update_convergence_plot()

        except Exception as e:
            print(f"数据检查错误: {e}")

    def clear_info_labels(self):
        # 清空信息统计区域的所有内容
        while self.info_form_layout.count():
            child = self.info_form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add_info_label(self, key, value):
        """确保标签能够正确显示"""
        try:
            label_key = QLabel(key)
            label_key.setFont(QFont("Microsoft YaHei", 12))
            label_key.setStyleSheet("""
                font: 12pt 'Microsoft YaHei'; 
                color: #24898f;
                padding: 5px;
            """)

            label_value = QLabel(value)
            label_value.setFont(QFont("Microsoft YaHei", 12))
            label_value.setStyleSheet("""
                font: 12pt 'Microsoft YaHei'; 
                color: #5d98f5;
                padding: 5px;
            """)
            label_value.setWordWrap(True)  # 允许文本换行

            # 添加到布局
            self.info_form_layout.addRow(label_key, label_value)

            # 强制更新UI
            self.info_form_widget.update()
            self.info_scroll_area.update()

        except Exception as e:
            print(f"添加信息标签错误: {e}")

    def update_info_labels(self, results):
        try:
            self.clear_info_labels()

            # 添加各项信息
            for key, value in results.items():
                self.add_info_label(key, value)

        except Exception as e:
            print(f"更新标签错误: {e}")
            self.clear_info_labels()
            self.add_info_label("信息更新错误", str(e))

    def final_results_received(self, success, gBV, gBpos, time_array, reference0, position):
        """优化完成后的处理"""
        self.data_timer.stop()

        try:
            import time as time_module  # 明确导入time模块并重命名

            # 计算运行时间
            elapsed_time = time_module.time() - self.start_time
            minutes, seconds = divmod(elapsed_time, 60)
            time_str = f"{int(minutes)}分{seconds:.2f}秒"

            # 更新图表
            self.update_convergence_plot()

            # 根据算法类型显示不同结果
            identification_type = self.identification_combo.currentText()

            if identification_type == "单目标":
                results = {
                    "状态": "运行完成",
                    "运行时间": time_str,
                    "目标函数": f"{gBV:.6f}",
                    "最优参数": str([f"{x:.4f}" for x in gBpos])
                }
            elif identification_type == "多目标":
                # 多目标算法（如MOGOA）只显示状态和运行时间
                results = {
                    "状态": "运行完成",
                    "运行时间": time_str
                }

            self.update_info_labels(results)

            # 打印调试信息
            print(f"Time array received: {time_array[:5]}... (len={len(time_array)})")
            print(f"Reference array received: {reference0[:5]}... (len={len(reference0)})")
            print(f"Position array received: {position[:5]}... (len={len(position)})")

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
                self.tracking_ax.set_ylabel('位置', fontsize=12)
                self.tracking_ax.set_title('位置跟踪效果', fontsize=14, fontweight='bold')
                self.tracking_ax.legend(['参考位置', '实际位置'], loc='upper right')
                self.tracking_ax.grid(True, linestyle='--', alpha=0.6)

                # 强制重绘
                self.tracking_canvas.draw()

        except Exception as e:
            error_msg = f"结果处理错误: {str(e)}\n{traceback.format_exc()}"
            self.parent_window.statusBar().showMessage(error_msg)
            print(error_msg)
        finally:
            # 重新启用运行按钮
            self.run_button.setEnabled(True)

    def handle_worker_error(self, error_msg):
        """处理工作线程发出的错误信号"""
        self.data_timer.stop()
        self.parent_window.statusBar().showMessage(f"算法错误: {error_msg}")

        # 计算运行时间
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(elapsed_time, 60)
        time_str = f"{int(minutes)}分{seconds:.2f}秒"

        self.add_info_label("状态", "运行失败")
        self.add_info_label("运行时间", time_str)

        # 重新启用运行按钮
        self.run_button.setEnabled(True)
        print(f"Worker error: {error_msg}")