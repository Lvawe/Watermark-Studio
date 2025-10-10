import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QFrame, QFileDialog, QMessageBox
)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watermark Studio")
        self.resize(1000, 600)
        self.image_paths = []   # 存储导入的图片路径
        self.current_image = None
        self.watermarked_pixmap = None
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

        # 导入按钮
        self.btn_import = QPushButton("导入图片")
        self.btn_import.clicked.connect(self.import_images)
        center_layout.addWidget(self.btn_import)

        main_layout.addWidget(center_frame, stretch=1)

        # 右侧：水印控制区
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("输入水印文本")
        right_layout.addWidget(self.text_input)

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

        # 默认显示第一张
        self.load_image(self.image_paths[0])
        self.list_widget.setCurrentRow(0)

    def load_image(self, path):
        """加载并显示图片"""
        self.current_image = path
        pixmap = QPixmap(path)
        self.preview_label.setPixmap(pixmap.scaled(
            self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def on_item_clicked(self, item):
        index = self.list_widget.row(item)
        if 0 <= index < len(self.image_paths):
            self.load_image(self.image_paths[index])

    def apply_watermark(self):
        """在当前图片上绘制文本水印"""
        if not self.current_image:
            QMessageBox.warning(self, "提示", "请先选择一张图片！")
            return

        text = self.text_input.text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入水印文本！")
            return

        base_pixmap = QPixmap(self.current_image)
        painter = QPainter(base_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont("Arial", 36)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 180))  # 白色半透明
        text_width = painter.fontMetrics().boundingRect(text).width()
        text_height = painter.fontMetrics().boundingRect(text).height()

        # 放右下角
        x = base_pixmap.width() - text_width - 30
        y = base_pixmap.height() - text_height - 20

        painter.drawText(x, y, text)
        painter.end()

        # 保存水印结果
        self.watermarked_pixmap = base_pixmap
        self.preview_label.setPixmap(base_pixmap.scaled(
            self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def save_image(self):
        """保存加水印图片"""
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
