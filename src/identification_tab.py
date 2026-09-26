# SPDX-FileCopyrightText: 2025-2026 Yuchen Wang
# SPDX-License-Identifier: GPL-3.0-only
"""Parameter identification page, retaining the original layout."""
from i18n import tr
import time
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFormLayout, QComboBox, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from algorithm_page import AlgorithmPage
from algorithm_catalog import IDENTIFICATION


class IdentificationTab(AlgorithmPage):
    def __init__(self, parent):
        super().__init__(parent)

        identification_layout = QHBoxLayout(self)
        identification_layout.setSpacing(15)
        identification_layout.setContentsMargins(15, 15, 15, 15)

        # 图像显示区域美化
        self.image_label = QWidget()
        self.image_label.setMinimumSize(400, 430)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        image_layout = QVBoxLayout(self.image_label)
        image_layout.setContentsMargins(5, 5, 5, 5)
        identification_layout.addWidget(self.image_label, 1)

        # 右侧布局美化
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        identification_layout.addLayout(right_layout, 1)

        # 算法选择和参数设置区域美化
        algorithm_param_widget = QWidget()
        algorithm_param_widget.setMinimumWidth(440)
        algorithm_param_widget.setFixedHeight(400)
        algorithm_param_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        algorithm_param_widget.setStyleSheet("""
            background-color: #f4f9ff;
            border: 1px solid #a3abbd;
            border-radius: 8px;
        """)

        algorithm_param_layout = QVBoxLayout(algorithm_param_widget)
        algorithm_param_layout.setSpacing(10)
        algorithm_param_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.addWidget(algorithm_param_widget)

        # 算法选择标签美化
        algorithm_label = QLabel(tr("选择算法："))
        algorithm_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        algorithm_label.setStyleSheet("color: #1e40af;")
        algorithm_param_layout.addWidget(algorithm_label)

        # 算法选择下拉菜单美化
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(list(IDENTIFICATION))
        self.algorithm_combo.setFont(QFont("Microsoft YaHei", 10))
        self.algorithm_combo.setStyleSheet("""
            QComboBox {
                background-color: #f9fafb;
                border: 1px solid #d1d5db;
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
        """)
        self.algorithm_combo.currentTextChanged.connect(self.algorithm_selected)
        algorithm_param_layout.addWidget(self.algorithm_combo)

        # 参数设置滚动区域美化
        self.param_scroll_area = QScrollArea()
        self.param_scroll_area.setWidgetResizable(True)
        self.param_scroll_area.setFixedHeight(300)
        self.param_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.param_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                width: 12px;
                background: #f3f4f6;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        algorithm_param_layout.addWidget(self.param_scroll_area)

        # 参数设置表单美化
        self.param_form_widget = QWidget()
        self.param_form_layout = QFormLayout(self.param_form_widget)
        self.param_form_layout.setSpacing(12)
        self.param_form_layout.setContentsMargins(10, 10, 10, 10)
        self.param_scroll_area.setWidget(self.param_form_widget)

        # 运行按钮美化
        run_identification_button = QPushButton(tr("运行算法"))
        run_identification_button.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        run_identification_button.setFixedSize(300, 70)
        run_identification_button.setStyleSheet("""
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
        self.run_button = run_identification_button
        run_identification_button.clicked.connect(self.run_identification)
        self.setup_run_controls(right_layout)

        # 信息统计区域美化
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

        # 信息统计表单
        self.info_scroll_area = QScrollArea()
        self.info_scroll_area.setWidgetResizable(True)
        self.info_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # 确保表单widget有合适的大小策略
        self.info_form_widget = QWidget()
        self.info_form_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.info_form_layout = QFormLayout(self.info_form_widget)
        self.info_form_layout.setSpacing(10)
        self.info_form_layout.setContentsMargins(5, 5, 5, 5)

        # 设置滚动区域的widget
        self.info_scroll_area.setWidget(self.info_form_widget)
        info_layout.addWidget(self.info_scroll_area)

        # 初始化
        self.algorithm_selected()
        self.init_dynamic_plot()

        self.apply_shadow_effects()

    def apply_shadow_effects(self):
        # 其他部件阴影
        widgets_to_shadow = [
            (self.image_label, 20, 7, QColor(0, 0, 0, 70)),
            (self.info_widget, 15, 5, QColor(0, 0, 0, 70)),
            (self.param_scroll_area, 15, 5, QColor(0, 0, 0, 70)),
        ]

        for widget, blur, offset, color in widgets_to_shadow:
            if widget is not None:
                effect = QGraphicsDropShadowEffect(widget)
                effect.setBlurRadius(blur)
                effect.setColor(color)
                effect.setOffset(offset, offset)
                widget.setGraphicsEffect(effect)
                widget.setAutoFillBackground(True)

    def init_dynamic_plot(self):
        """初始化动态绘图区域，设置中文显示"""
        # 创建Figure和Canvas
        self.figure = Figure(figsize=(6, 7), dpi=100, facecolor='#ffffff')
        self.canvas = FigureCanvas(self.figure)

        # 清除并设置布局
        if hasattr(self.image_label, 'layout'):
            for i in reversed(range(self.image_label.layout().count())):
                self.image_label.layout().itemAt(i).widget().setParent(None)
        else:
            self.image_label.setLayout(QVBoxLayout())

        self.image_label.layout().addWidget(self.canvas)

        # 设置图形样式
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#f9fafb')
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label=tr('全局最优值'))

        # 设置坐标轴样式（中文）
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 设置中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        self.ax.set_xlabel(tr('迭代次数'), fontsize=12)
        self.ax.set_ylabel(tr('适应度值'), fontsize=12)
        self.ax.set_title(tr('适应度进化图'), fontsize=14, fontweight='bold')

        # 设置图例和网格
        self.ax.legend(loc='upper right', fontsize=10)
        self.ax.grid(True, linestyle='--', alpha=0.6)


        # 设置初始坐标范围
        max_iter = 200  # 默认值，实际运行时会从参数获取
        self.ax.set_xlim(0, max_iter)
        self.ax.set_ylim(-5, 50)


        # 设置边框颜色
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#d1d5db')

        self.canvas.draw()


    def run_identification(self):
        self.start_run()

    def final_results_received(self, gb, g, gbest):
        """MATLAB运行完成后的回调函数"""
        # print(f"接收到MATLAB结果 - gb类型: {type(gb)}, 值: {gb}")
        # print(f"接收到MATLAB结果 - g类型: {type(g)}, 值: {g}")
        # print(f"接收到MATLAB结果 - gbest类型: {type(gbest)}, 值: {gbest}")

        # 停止数据监视定时器
        self.data_timer.stop()

        try:
            # 计算运行时间
            elapsed_time = time.time() - self.start_time
            minutes, seconds = divmod(elapsed_time, 60)
            time_str = tr('{minutes}分{seconds:.2f}秒', minutes=int(minutes), seconds=seconds)

            # 转换MATLAB数据格式
            gb = np.array(gb).flatten()
            self.gb_data = gb

            # 更新图表
            self.update_plot_from_data()

            # 显示结果 (添加运行时间)
            results = {
                "状态": "运行完成",
                "运行时间": time_str,  # 添加运行时间
                "目标函数": f"{float(gbest):.8g}",
                "最优个体": str([f"{x:.8g}" for x in np.array(g).flatten()])
            }
            self.update_info_labels(results)

        except Exception as e:
            self.parent_window.statusBar().showMessage(tr('结果处理错误: {error}', error=e))
