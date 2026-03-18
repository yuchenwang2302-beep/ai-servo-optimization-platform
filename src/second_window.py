
import sys
import matlab.engine
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QFormLayout, QLineEdit, QComboBox, QScrollArea, QTextEdit, QFrame, QSizePolicy
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import json
import numpy as np
import time
from PyQt5.QtWidgets import QSizePolicy, QGraphicsDropShadowEffect
import subprocess
import scipy.io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import traceback
from optimization_tab import OptimizationTab
import os
from PyQt5.QtCore import QThread, pyqtSignal
from schneider_tab import SchneiderTab
from matlab_worker import MatlabWorker
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

class SecondWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # 设置主窗口样式
        self.setWindowTitle("AI伺服驱动系统 V2.0")
        self.setGeometry(330, 150, 1200, 800)
        self.setWindowIcon(QIcon("app_icon.png"))

        # 设置全局样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QWidget {
                font: 10pt "Microsoft YaHei";
            }
            QLabel {
                color: #333333;
            }
        """)

        # 创建主窗口的中心部件
        central_widget = QWidget(self)
        central_widget.setStyleSheet("background-color: #ffffff; border-radius: 10px; padding: 5px;  # 添加内边距")
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 顶部标签页样式改进
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 5px;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #e5e7eb;
                color: #4b5563;
                padding: 8px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid #d1d5db;
                margin-right: 4px;
                font: bold 10pt "Microsoft YaHei";
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
                border-bottom: 2px solid #2563eb;
            }
            QTabBar::tab:hover {
                background: #dbeafe;
            }
        """)
        main_layout.addWidget(tab_widget)

        # 创建标签页
        self.tab_identification = QWidget()
        self.tab_optimization = OptimizationTab(self)  # 传入self作为父窗口引用
        self.tab_schneider = SchneiderTab(self)

        tab_widget.addTab(self.tab_identification, "辨识算法")
        tab_widget.addTab(self.tab_optimization, "优化算法")
        tab_widget.addTab(self.tab_schneider, "施耐德电气")

        # 辨识算法页面布局
        identification_layout = QHBoxLayout(self.tab_identification)
        identification_layout.setSpacing(15)
        identification_layout.setContentsMargins(15, 15, 15, 15)

        # 图像显示区域美化
        self.image_label = QWidget()
        self.image_label.setFixedSize(600, 700)
        self.image_label.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 8px;
        """)

        image_layout = QVBoxLayout(self.image_label)
        image_layout.setContentsMargins(5, 5, 5, 5)
        identification_layout.addWidget(self.image_label)

        # 右侧布局美化
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        identification_layout.addLayout(right_layout)

        # 算法选择和参数设置区域美化
        algorithm_param_widget = QWidget()
        algorithm_param_widget.setFixedSize(580, 400)
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
        algorithm_label = QLabel("选择算法：")
        algorithm_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        algorithm_label.setStyleSheet("color: #1e40af;")
        algorithm_param_layout.addWidget(algorithm_label)

        # 算法选择下拉菜单美化
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["PSO", "GA", "DE", "IA", "FA", "HPSO"])
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
        self.param_scroll_area.setFixedSize(550, 300)
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
        run_identification_button = QPushButton("运行算法")
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
        run_identification_button.clicked.connect(self.run_identification)
        right_layout.addWidget(run_identification_button, 0, Qt.AlignHCenter)

        # 信息统计区域美化
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

        # 添加数据监视相关变量
        self.data_files = {
            "PSO": "pso_temp_data.mat",
            "GA": "GA_temp_data.mat",
            "DE": "de_temp_data.mat",
            "IA": "ia_temp_data.mat",
            "FA": "FA_temp_data.mat",
            "HPSO": "HPSO_temp_data.mat"
        }

        # 创建定时器用于检查数据更新
        self.data_timer = QTimer(self)
        # self.data_timer.timeout.connect(self.check_data_update)
        # self.data_timer.start(1000)  # 每1000ms检查一次

        # 应用阴影效果
        self.apply_shadow_effects()


    def apply_shadow_effects(self):
        """为所有需要阴影的部件应用阴影效果"""
        # 主窗口阴影
        # self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)  # 移除默认边框
        # self.setAttribute(Qt.WA_TranslucentBackground)  # 设置透明背景

        # 中央部件阴影
        shadow = QGraphicsDropShadowEffect(self.centralWidget())
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(5, 5)
        self.centralWidget().setGraphicsEffect(shadow)

        # 其他部件阴影
        widgets_to_shadow = [
            (self.image_label, 20, 7, QColor(0, 0, 0, 70)),
            (self.info_widget, 15, 5, QColor(0, 0, 0, 70)),
            (self.param_scroll_area, 15, 5, QColor(0, 0, 0, 70)),
            (self.findChild(QPushButton, "运行算法"), 8, 2, QColor(0, 0, 0, 70))
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
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='全局最优值')

        # 设置坐标轴样式（中文）
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 设置中文字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        self.ax.set_xlabel('迭代次数', fontsize=12)
        self.ax.set_ylabel('适应度值', fontsize=12)
        self.ax.set_title('适应度进化图', fontsize=14, fontweight='bold')

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

    def algorithm_selected(self):
        # 清空之前的参数设置
        while self.param_form_layout.count():
            child = self.param_form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 获取选中的算法
        algorithm = self.algorithm_combo.currentText()
        self.current_algorithm = algorithm

        # 根据算法设置不同的参数
        if algorithm == "PSO":
            self.setup_pso_params()
        elif algorithm == "GA":
            self.setup_ga_params()
        elif algorithm == "DE":
            self.setup_de_params()
        elif algorithm == "IA":
            self.setup_ia_params()
        elif algorithm == "FA":
            self.setup_FA_params()
        elif algorithm == "HPSO":
            self.setup_HPSO_params()

    def setup_pso_params(self):
        # 设置PSO算法的参数
        self.params = {
            "群体粒子个数 (N)": QLineEdit("100"),
            "粒子维数 (D)": QLineEdit("10"),
            "最大迭代次数 (T)": QLineEdit("200"),
            "速度 (vref)": QLineEdit("200"),
            "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),

        }
        self.add_params_to_form()

    def setup_ga_params(self):
        # 设置GA算法的参数
        self.params = {
            "群体粒子个数 (N)": QLineEdit("40"),
            "粒子维数 (D)": QLineEdit("10"),
            "最大迭代次数 (T)": QLineEdit("200"),
            "速度 (vref)": QLineEdit("3200"),
            "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),
        }
        # self.params["选择方法"].addItems(["轮盘赌选择", "锦标赛选择", "排名选择"])
        self.add_params_to_form()

    def setup_de_params(self):
        # 设置DE算法的参数
        self.params = {
            "群体粒子个数 (N)": QLineEdit("100"),
            "粒子维数 (D)": QLineEdit("10"),
            "最大迭代次数 (T)": QLineEdit("200"),
            "速度 (vref)": QLineEdit("200"),
            "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),
        }
        self.add_params_to_form()

    def setup_ia_params(self):
        # 设置IA算法的参数
        self.params = {
            "群体粒子个数 (N)": QLineEdit("100"),
            "粒子维数 (D)": QLineEdit("10"),
            "最大迭代次数 (T)": QLineEdit("200"),
            "速度 (vref)": QLineEdit("200"),
            "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),
        }
        self.add_params_to_form()

    def setup_FA_params(self):
        # 设置算法FA的参数
        self.params = {
            "群体粒子个数 (N)": QLineEdit("50"),
            "粒子维数 (D)": QLineEdit("10"),
            "最大迭代次数 (T)": QLineEdit("200"),
            "速度 (vref)": QLineEdit("3200"),
            "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),
        }
        self.add_params_to_form()

    def setup_HPSO_params(self):
        # 设置算法HPSO的参数
        self.params = {
            "群体粒子个数 (N)": QLineEdit("50"),
            "粒子维数 (D)": QLineEdit("10"),
            "最大迭代次数 (T)": QLineEdit("200"),
            "速度 (vref)": QLineEdit("200"),
            "Lq轴电感范围(t1L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "Ld轴电感范围(t2L)": QLineEdit("[1.5e-4, 2.5e-4]"),
            "电阻范围(t3L)": QLineEdit("[0.3, 0.4]"),
            "磁链范围(t4L)": QLineEdit("[0.006, 0.007]"),
            "转动惯量范围(t5L)": QLineEdit("[5e-5,1e-4]"),
        }
        self.add_params_to_form()


    def add_params_to_form(self):
        # 将参数添加到表单布局中
        for key, value in self.params.items():
            label = QLabel(key)
            label.setFont(QFont("Microsoft YaHei", 12))
            label.setStyleSheet("font: 12pt 'Microsoft YaHei'; color: #24898f;")
            self.param_form_layout.addRow(label, value)

    def run_identification(self):
        """运行辨识算法的核心方法（完整线程安全版）"""
        try:
            # ==================== 1. 初始化状态 ====================
            self.last_update_iter = 0
            self.gb_data = np.array([])
            self.start_time = time.time()  # 添加计时开始点

            # 清除当前算法对应的旧数据文件
            current_data_file = self.data_files.get(self.current_algorithm)
            if current_data_file and os.path.exists(current_data_file):
                try:
                    os.remove(current_data_file)
                except Exception as e:
                    self.statusBar().showMessage(f"删除旧数据文件失败: {str(e)}")
                    return

            # ==================== 2. 获取并验证参数 ====================
            params = {}
            try:
                for key, widget in self.params.items():
                    if isinstance(widget, QLineEdit):
                        params[key] = widget.text()
                    elif isinstance(widget, QComboBox):
                        params[key] = widget.currentText()

                # 强制转换关键参数类型
                required_params = {
                    "群体粒子个数 (N)": int,
                    "粒子维数 (D)": int,
                    "最大迭代次数 (T)": int,
                    "速度 (vref)": float
                }

                for param, dtype in required_params.items():
                    params[param] = dtype(params[param])

            except ValueError as e:
                self.statusBar().showMessage(f"参数错误: 请检查数值格式 ({str(e)})")
                return
            except Exception as e:
                self.statusBar().showMessage(f"参数获取失败: {str(e)}")
                return

            # ==================== 3. 重置UI状态 ====================
            # 清除旧图表
            self.ax.clear()
            self.ax.set_xlabel('迭代次数', fontsize=12)
            self.ax.set_ylabel('适应度值', fontsize=12)
            self.ax.set_title(f'{self.current_algorithm} 适应度进化图', fontsize=14, fontweight='bold')
            self.ax.grid(True)
            self.ax.set_xlim(0, params["最大迭代次数 (T)"])
            self.canvas.draw()

            # 清空信息面板
            self.clear_info_labels()
            self.add_info_label("状态", "算法运行中...")

            # ==================== 4. 启动MATLAB工作线程 ====================
            # 检查已有线程
            if hasattr(self, 'worker') and self.worker.isRunning():
                self.worker.stop()  # 使用安全的stop方法

            # 创建新线程（不再传递data_file参数）
            self.worker = MatlabWorker(
                algorithm=self.current_algorithm,
                params=params
            )


            # 连接信号槽
            self.worker.finished.connect(self.final_results_received)
            self.worker.error.connect(self.handle_worker_error)

            # 启动线程
            self.worker.start()

            # ==================== 5. 启动数据监视定时器 ====================
            self.data_timer.timeout.connect(self.check_data_update)
            self.data_timer.start(1000)  # 每1000ms检查一次

            # 更新状态栏
            self.statusBar().showMessage(f"正在运行 {self.current_algorithm} 算法")

        except Exception as e:
            error_msg = f"运行失败: {str(e)}\n{traceback.format_exc()}"
            self.statusBar().showMessage(error_msg)
            print(error_msg)

    def handle_worker_error(self, error_msg):
        """处理工作线程发出的错误信号"""
        self.data_timer.stop()
        self.statusBar().showMessage(f"算法错误: {error_msg}")

        # 计算运行时间
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(elapsed_time, 60)
        time_str = f"{int(minutes)}分{seconds:.2f}秒"

        self.add_info_label("状态", "运行失败")
        self.add_info_label("运行时间", time_str)  # 添加运行时间
        print(f"Worker error: {error_msg}")

    def closeEvent(self, event):
        """窗口关闭时清理资源"""
        if hasattr(self, 'worker'):
            self.worker.stop()  # 使用改进的stop方法
        if self.data_timer.isActive():
            self.data_timer.stop()
        event.accept()

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
            time_str = f"{int(minutes)}分{seconds:.2f}秒"

            # 转换MATLAB数据格式
            gb = np.array(gb).flatten()
            self.gb_data = gb

            # 更新图表
            self.update_plot_from_data()

            # 显示结果 (添加运行时间)
            results = {
                "状态": "运行完成",
                "运行时间": time_str,  # 添加运行时间
                "目标函数": f"{float(gbest):.4f}",
                "最优个体": str([f"{x:.4f}" for x in np.array(g).flatten()])
            }
            self.update_info_labels(results)

        except Exception as e:
            self.statusBar().showMessage(f"结果处理错误: {str(e)}")

    def check_data_update(self):
        """检查MATLAB数据文件是否有更新"""
        try:
            # 添加属性检查
            if not hasattr(self, 'last_update_iter') or not hasattr(self, 'gb_data'):
                return

            current_data_file = self.data_files.get(self.current_algorithm)
            if not current_data_file or not os.path.exists(current_data_file):
                return

            current_data_file = self.data_files.get(self.current_algorithm)
            if not current_data_file or not os.path.exists(current_data_file):
                return

            # 加载MATLAB数据
            data = scipy.io.loadmat(current_data_file)
            gb_record = data['gBV_record'].flatten()
            current_iter = data['iter'][0 ,0]

            # 如果数据有更新
            if current_iter > self.last_update_iter:
                self.last_update_iter = current_iter
                # 只保留实际计算过的数据点
                self.gb_data = gb_record[:current_iter +1]  # +1因为MATLAB索引从1开始
                self.update_plot_from_data()

        except Exception as e:
            print(f"数据检查错误: {e}")

    def closeEvent(self, event):
        """窗口关闭时清理资源"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        if self.data_timer.isActive():
            self.data_timer.stop()
        event.accept()

    def update_plot_from_data(self):
        """根据最新数据更新图表"""
        if len(self.gb_data) == 0:
            return

        try:
            # 清除图形但保留坐标设置
            self.ax.clear()

            # 重新设置图形属性
            self.ax.set_xlabel('迭代次数', fontsize=12)
            self.ax.set_ylabel('适应度值', fontsize=12)
            self.ax.set_title(f'{self.current_algorithm} 适应度进化图', fontsize=14, fontweight='bold')
            self.ax.grid(True, linestyle='--', alpha=0.6)

            # 只绘制实际发生的数据点
            valid_indices = ~np.isnan(self.gb_data)
            x_data = np.arange(len(self.gb_data))[valid_indices]
            y_data = self.gb_data[valid_indices]

            # 只绘制有数据的部分
            if len(x_data) > 0:
                self.line, = self.ax.plot(x_data, y_data, 'b-', linewidth=2, label='全局最优值')

                # 修改这里：固定x轴范围为0到最大迭代次数（从参数中获取）
                max_iter = int(self.params["最大迭代次数 (T)"].text())  # 从参数输入获取最大迭代次数
                self.ax.set_xlim(0, max_iter)  # 固定x轴范围

                # 自动调整y轴范围，留出10%的边距
                y_min, y_max = np.min(y_data), np.max(y_data)
                y_range = y_max - y_min
                if y_range == 0:  # 处理所有值相同的情况
                    y_range = 1
                    y_min -= 0.5
                    y_max += 0.5
                margin = y_range * 0.1
                self.ax.set_ylim(y_min - margin, y_max + margin)

            # 更新图例
            self.ax.legend(loc='upper right')

            # 强制重绘
            self.canvas.draw()

        except Exception as e:
            print(f"更新图表错误: {e}")

    def update_info_labels(self, results):
        try:
            self.clear_info_labels()

            # 添加各项信息
            self.add_info_label("状态", results.get("状态", "N/A"))
            self.add_info_label("运行时间", results.get("运行时间", "N/A"))  # 添加运行时间
            self.add_info_label("目标函数", results.get("目标函数", "N/A"))

            # # 处理"最优个体"
            # global_optimal = results.get("最优个体", "N/A")

            # if global_optimal != "N/A":
            #     try:
            #         # 尝试解析字符串形式的列表
            #         if isinstance(global_optimal, str) and global_optimal.startswith('['):
            #             # 去除方括号并分割成单独的数字
            #             numbers = [float(x) for x in global_optimal.strip('[]').split(',')]
            #             # 格式化所有数值为4位小数
            #             formatted_numbers = [f"{num:.4f}" for num in numbers]
            #             # 将格式化后的数值列表转换为字符串
            #             formatted = "[" + ", ".join(formatted_numbers) + "]"
            #         else:
            #             # 如果是单个值直接格式化
            #             formatted = f"{float(global_optimal):.4f}"
            #     except (ValueError, TypeError, AttributeError) as e:
            #         print(f"格式化失败: {e}")
            #         formatted = str(global_optimal)
            # else:
            #     formatted = "N/A"

            # self.add_info_label("最优个体", formatted)
            self.add_info_label("最优个体", results.get("最优个体", "N/A"))

            # # 如果是DE算法，添加额外信息
            # if hasattr(self, 'de_additional_info'):
            #     for key, value in self.de_additional_info.items():
            #         self.add_info_label(key, value)

        except Exception as e:
            print(f"更新标签错误: {e}")
            self.clear_info_labels()
            self.add_info_label("信息更新错误", str(e))

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SecondWindow()
    window.show()
    sys.exit(app.exec_())