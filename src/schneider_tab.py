from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                             QHBoxLayout, QGroupBox, QGridLayout, QFrame,
                             QScrollArea, QSizePolicy)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize


class SchneiderTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化施耐德电气标签页界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        # 顶部标题栏
        top_bar = QFrame()
        top_bar.setFixedHeight(40)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("Canvas1")
        title_label.setFont(QFont("Microsoft YaHei", 12))

        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()

        # 添加右上角图标
        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon("refresh.png"))  # 假设存在刷新图标的文件
        refresh_btn.setIconSize(QSize(20, 20))
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.clicked.connect(self.on_refresh_clicked)

        help_btn = QPushButton()
        help_btn.setIcon(QIcon("help.png"))  # 假设存在帮助图标的文件
        help_btn.setIconSize(QSize(20, 20))
        help_btn.setObjectName("help_btn")
        help_btn.clicked.connect(self.on_help_clicked)

        user_btn = QPushButton()
        user_btn.setIcon(QIcon("user.png"))  # 假设存在用户图标的文件
        user_btn.setIconSize(QSize(20, 20))
        user_btn.setObjectName("user_btn")
        user_btn.clicked.connect(self.on_user_clicked)

        top_bar_layout.addWidget(refresh_btn)
        top_bar_layout.addWidget(help_btn)
        top_bar_layout.addWidget(user_btn)

        main_layout.addWidget(top_bar)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # 内容区域
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 左侧控制面板
        control_panel = QFrame()
        control_panel.setFixedWidth(200)
        control_panel_layout = QVBoxLayout(control_panel)
        control_panel_layout.setContentsMargins(10, 10, 10, 10)
        control_panel_layout.setSpacing(10)

        # 控制面板标题
        panel_title = QLabel("圆盘控制")
        panel_title.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        panel_title.setAlignment(Qt.AlignCenter)
        control_panel_layout.addWidget(panel_title)

        # 添加分隔线
        panel_separator = QFrame()
        panel_separator.setFrameShape(QFrame.HLine)
        panel_separator.setFrameShadow(QFrame.Sunken)
        control_panel_layout.addWidget(panel_separator)

        # 控制按钮
        start_btn = QPushButton("启动")
        start_btn.setObjectName("start_btn")
        stop_btn = QPushButton("停止")
        stop_btn.setObjectName("stop_btn")
        continuous_switch = QPushButton("连续 OFF")
        continuous_switch.setObjectName("continuous_switch")
        continuous_switch.setCheckable(True)

        # 绑定按钮功能
        start_btn.clicked.connect(self.on_start_clicked)
        stop_btn.clicked.connect(self.on_stop_clicked)
        continuous_switch.clicked.connect(self.on_continuous_switched)

        # 添加按钮到控制面板
        control_panel_layout.addWidget(start_btn)
        control_panel_layout.addWidget(stop_btn)
        control_panel_layout.addWidget(continuous_switch)
        control_panel_layout.addStretch()

        # 右侧显示区域
        display_area = QFrame()
        display_layout = QVBoxLayout(display_area)
        display_layout.setContentsMargins(10, 10, 10, 10)

        # 添加图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0;")
        display_layout.addWidget(self.image_label)

        # 将左右区域添加到内容布局
        content_layout.addWidget(control_panel)
        content_layout.addWidget(display_area)

        main_layout.addLayout(content_layout)

        # 设置样式
        self.setStyleSheet("""
            QFrame {
                border: none;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
            QPushButton#start_btn {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#stop_btn {
                background-color: #F44336;
                color: white;
            }
            QPushButton#continuous_switch {
                background-color: #9E9E9E;
                color: white;
            }
            QPushButton#continuous_switch:checked {
                background-color: #2196F3;
            }
            QPushButton#refresh_btn, QPushButton#help_btn, QPushButton#user_btn {
                background: none;
                border: none;
                padding: 0;
                margin: 0;
            }
        """)

    def on_start_clicked(self):
        """启动按钮点击事件"""
        print("启动按钮被点击")
        self.update_image("start.png")

    def on_stop_clicked(self):
        """停止按钮点击事件"""
        print("停止按钮被点击")
        self.update_image("stop.png")

    def on_continuous_switched(self, checked):
        """连续模式切换事件"""
        sender = self.sender()
        if checked:
            print("连续模式开启")
            sender.setText("连续 ON")
        else:
            print("连续模式关闭")
            sender.setText("连续 OFF")
        self.update_image("continuous_on.png" if checked else "continuous_off.png")

    def on_refresh_clicked(self):
        print("刷新按钮被点击")

    def on_help_clicked(self):
        print("帮助按钮被点击")

    def on_user_clicked(self):
        print("用户配置按钮被点击")

    def update_image(self, image_path):
        """更新图像显示"""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"无法加载图像: {image_path}")
        else:
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.width(), self.image_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))