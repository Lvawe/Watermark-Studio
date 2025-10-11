import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QPushButton, QSizePolicy, QFrame, QFileDialog, QMessageBox,
    QComboBox, QRadioButton, QButtonGroup, QGroupBox
)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize


SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watermark Studio – 文件导入与导出增强版")
        self.resize(1150, 650)
        self.setAcceptDrops(True)

        self.image_paths = []
        self.current_image = None
        self.watermarked_pixmap = None
        self.output_format = "JPEG"

        self.init_ui()

    # -------------------- 界面布局 --------------------

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左侧：文件列表
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(64, 64))
        self.list_widget.setMinimumWidth(250)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        main_layout.addWidget(self.list_widget)

        # 中间：预览区
        center_frame = QFrame()
        center_layout = QVBoxLayout(center_frame)
        center_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel("拖拽图片或点击下方按钮导入")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.setMinimumSize(500, 400)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        center_layout.addWidget(self.preview_label)

        self.btn_import = QPushButton("导入图片 / 文件夹")
        self.btn_import.clicked.connect(self.import_images)
        center_layout.addWidget(self.btn_import)

        main_layout.addWidget(center_frame, stretch=1)

        # 右侧：导出控制区
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(10)

        # 水印文本输入（保留）
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("输入水印文本")
        right_layout.addWidget(self.text_input)

        self.btn_apply = QPushButton("应用水印")
        self.btn_apply.clicked.connect(self.apply_watermark)
        right_layout.addWidget(self.btn_apply)

        # ---------------- 导出设置 ----------------
        export_group = QGroupBox("导出设置")
        export_layout = QVBoxLayout(export_group)

        # 文件命名规则
        name_rule_layout = QVBoxLayout()
        name_rule_layout.addWidget(QLabel("命名规则:"))
        self.radio_original = QRadioButton("保留原文件名")
        self.radio_prefix = QRadioButton("添加前缀")
        self.radio_suffix = QRadioButton("添加后缀")
        self.radio_suffix.setChecked(True)
        name_rule_layout.addWidget(self.radio_original)
        name_rule_layout.addWidget(self.radio_prefix)
        name_rule_layout.addWidget(self.radio_suffix)
        export_layout.addLayout(name_rule_layout)

        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("例如：wm_ 或 _watermarked")
        export_layout.addWidget(self.prefix_input)

        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG"])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        export_layout.addLayout(format_layout)

        right_layout.addWidget(export_group)

        # 保存按钮
        self.btn_save = QPushButton("导出图片")
        self.btn_save.clicked.connect(self.save_images)
        right_layout.addWidget(self.btn_save)

        right_layout.addStretch(1)
        main_layout.addWidget(right_frame)

    # -------------------- 拖拽导入 --------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        image_files = []
        for f in files:
            if os.path.isdir(f):
                # 遍历文件夹
                for root, _, names in os.walk(f):
                    for n in names:
                        if n.lower().endswith(SUPPORTED_FORMATS):
                            image_files.append(os.path.join(root, n))
            elif f.lower().endswith(SUPPORTED_FORMATS):
                image_files.append(f)
        self.load_file_list(image_files)

    # -------------------- 文件导入 --------------------

    def import_images(self):
        """支持多选文件或整个文件夹导入"""
        choice = QMessageBox.question(
            self, "导入方式",
            "选择导入图片文件？（选择“否”可导入整个文件夹）",
            QMessageBox.Yes | QMessageBox.No
        )
        files = []
        if choice == QMessageBox.Yes:
            files, _ = QFileDialog.getOpenFileNames(
                self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)"
            )
        else:
            folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
            if folder:
                for root, _, names in os.walk(folder):
                    for n in names:
                        if n.lower().endswith(SUPPORTED_FORMATS):
                            files.append(os.path.join(root, n))

        self.load_file_list(files)

    def load_file_list(self, files):
        """刷新左侧文件列表"""
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

    # -------------------- 图片加载与水印 --------------------

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

    def apply_watermark(self):
        """简单文字水印（右下角）"""
        if not self.current_image:
            QMessageBox.warning(self, "提示", "请先导入图片！")
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
        painter.setPen(QColor(255, 255, 255, 180))
        tw = painter.fontMetrics().boundingRect(text).width()
        th = painter.fontMetrics().boundingRect(text).height()
        x = base_pixmap.width() - tw - 30
        y = base_pixmap.height() - th - 20
        painter.drawText(x, y, text)
        painter.end()
        self.watermarked_pixmap = base_pixmap
        self.preview_label.setPixmap(base_pixmap.scaled(
            self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    # -------------------- 图片导出 --------------------

    def on_format_changed(self, fmt):
        self.output_format = fmt

    def save_images(self):
        if not self.watermarked_pixmap or not self.current_image:
            QMessageBox.warning(self, "提示", "请先应用水印！")
            return

        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if not dir_path:
            return

        # 禁止保存到原文件夹
        src_dir = os.path.dirname(self.current_image)
        if os.path.abspath(dir_path) == os.path.abspath(src_dir):
            QMessageBox.warning(self, "错误", "不能导出到原文件夹！")
            return

        prefix = ""
        suffix = ""
        if self.radio_prefix.isChecked():
            prefix = self.prefix_input.text().strip()
        elif self.radio_suffix.isChecked():
            suffix = self.prefix_input.text().strip()

        # 遍历导出所有图片
        for path in self.image_paths:
            base_name = os.path.basename(path)
            name, ext = os.path.splitext(base_name)
            output_name = f"{prefix}{name}{suffix}.{self.output_format.lower()}"
            output_path = os.path.join(dir_path, output_name)
            self.watermarked_pixmap.save(output_path, self.output_format)

        QMessageBox.information(self, "完成", f"所有图片已导出到：\n{dir_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
