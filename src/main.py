import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QPushButton, QSizePolicy, QFrame, QFileDialog, QMessageBox,
    QFontComboBox, QSpinBox, QColorDialog, QSlider, QHBoxLayout
)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watermark Studio – 阶段 2 高级水印")
        self.resize(1100, 650)
        self.image_paths = []
        self.current_image = None
        self.watermarked_pixmap = None

        # 默认水印参数
        self.font_family = "Arial"
        self.font_size = 36
        self.font_color = QColor(255, 255, 255)
        self.opacity = 180  # 0–255 scale

        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左侧：文件列表
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(64, 64))
        self.list_widget.setMinimumWidth(220)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        main_layout.addWidget(self.list_widget)

        # 中间：预览区
        center_frame = QFrame()
        center_layout = QVBoxLayout(center_frame)
        center_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel("请导入图片以开始")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.setMinimumSize(500, 400)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        center_layout.addWidget(self.preview_label)

        self.btn_import = QPushButton("导入图片")
        self.btn_import.clicked.connect(self.import_images)
        center_layout.addWidget(self.btn_import)

        main_layout.addWidget(center_frame, stretch=1)

        # 右侧控制区
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(10)

        # 水印文本输入
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("输入水印文本")
        self.text_input.textChanged.connect(self.update_preview)
        right_layout.addWidget(self.text_input)

        # 字体选择
        font_layout = QHBoxLayout()
        self.font_box = QFontComboBox()
        self.font_box.setCurrentFont(QFont("Arial"))
        self.font_box.currentFontChanged.connect(self.on_font_changed)
        font_layout.addWidget(QLabel("字体:"))
        font_layout.addWidget(self.font_box)
        right_layout.addLayout(font_layout)

        # 字号
        size_layout = QHBoxLayout()
        self.font_size_box = QSpinBox()
        self.font_size_box.setRange(8, 120)
        self.font_size_box.setValue(36)
        self.font_size_box.valueChanged.connect(self.on_font_size_changed)
        size_layout.addWidget(QLabel("字号:"))
        size_layout.addWidget(self.font_size_box)
        right_layout.addLayout(size_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton("选择颜色")
        self.btn_color.clicked.connect(self.choose_color)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        color_layout.addWidget(QLabel("颜色:"))
        color_layout.addWidget(self.btn_color)
        color_layout.addWidget(self.color_preview)
        right_layout.addLayout(color_layout)

        # 透明度
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(QLabel("透明度:"))
        opacity_layout.addWidget(self.opacity_slider)
        right_layout.addLayout(opacity_layout)

        # 操作按钮
        self.btn_apply = QPushButton("应用水印")
        self.btn_apply.clicked.connect(self.apply_watermark)
        right_layout.addWidget(self.btn_apply)

        self.btn_save = QPushButton("保存图片")
        self.btn_save.clicked.connect(self.save_image)
        right_layout.addWidget(self.btn_save)

        right_layout.addStretch(1)
        main_layout.addWidget(right_frame)

    # -------------------- 功能函数 --------------------

    def import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)"
        )
        if not files:
            return
        self.image_paths = files
        self.list_widget.clear()

        for path in files:
            pixmap = QPixmap(path)
            icon = QIcon(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            item = QListWidgetItem(icon, os.path.basename(path))
            self.list_widget.addItem(item)

        self.load_image(self.image_paths[0])
        self.list_widget.setCurrentRow(0)

    def load_image(self, path):
        self.current_image = path
        pixmap = QPixmap(path)
        self.preview_label.setPixmap(pixmap.scaled(
            self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def on_item_clicked(self, item):
        index = self.list_widget.row(item)
        if 0 <= index < len(self.image_paths):
            self.load_image(self.image_paths[index])
            self.update_preview()

    def choose_color(self):
        color = QColorDialog.getColor(self.font_color, self, "选择水印颜色")
        if color.isValid():
            self.font_color = color
            self.color_preview.setStyleSheet(f"background-color: {color.name()};")
            self.update_preview()

    def on_font_changed(self, font):
        self.font_family = font.family()
        self.update_preview()

    def on_font_size_changed(self, size):
        self.font_size = size
        self.update_preview()

    def on_opacity_changed(self, value):
        self.opacity = int(value * 2.55)  # 转换为 0-255
        self.update_preview()

    def apply_watermark(self):
        """点击按钮正式应用"""
        self.update_preview(final=True)

    def update_preview(self, final=False):
        """实时更新预览"""
        if not self.current_image:
            return

        text = self.text_input.text().strip()
        base_pixmap = QPixmap(self.current_image)
        painter = QPainter(base_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont(self.font_family, self.font_size)
        painter.setFont(font)
        painter.setPen(QColor(self.font_color.red(), self.font_color.green(),
                              self.font_color.blue(), self.opacity))

        text_width = painter.fontMetrics().boundingRect(text).width()
        text_height = painter.fontMetrics().boundingRect(text).height()
        x = base_pixmap.width() - text_width - 30
        y = base_pixmap.height() - text_height - 20

        if text:
            painter.drawText(x, y, text)

        painter.end()
        self.preview_label.setPixmap(base_pixmap.scaled(
            self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

        if final:
            self.watermarked_pixmap = base_pixmap

    def save_image(self):
        if not self.watermarked_pixmap or not self.current_image:
            QMessageBox.warning(self, "提示", "请先应用水印！")
            return

        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if not dir_path:
            return

        base_name = os.path.basename(self.current_image)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_path, f"{name}_watermarked{ext}")
        self.watermarked_pixmap.save(output_path)
        QMessageBox.information(self, "成功", f"图片已保存至：\n{output_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
