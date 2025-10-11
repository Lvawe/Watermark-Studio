import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QPushButton, QSizePolicy, QFrame, QFileDialog, QMessageBox,
    QComboBox, QRadioButton, QButtonGroup, QGroupBox, QColorDialog, QSlider, QFontComboBox, QSpinBox, QCheckBox, QGridLayout
)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont, QMouseEvent, QTransform
from PySide6.QtCore import Qt, QSize, QPoint


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

        # 新增水印样式相关属性
        self.font_family = "Arial"
        self.font_size = 36
        self.font_bold = False
        self.font_italic = False
        self.font_color = QColor(255, 255, 255, 180)
        self.font_opacity = 180  # 0-255
        self.shadow_enabled = False
        self.outline_enabled = False

        # 新增水印布局相关属性
        self.watermark_pos_mode = "bottom_right"  # 九宫格预设，默认右下
        self.watermark_offset = QPoint(-30, -20)  # 偏移量（用于拖拽）
        self.watermark_dragging = False
        self.watermark_drag_start = QPoint(0, 0)
        self.watermark_custom_pos = None  # 手动拖拽的像素坐标
        self.watermark_angle = 0  # 旋转角度

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
        right_layout.setSpacing(18)  # 分组间距更大

        # ----------- 水印样式分组 -----------
        style_group = QGroupBox("水印样式")
        style_group.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        style_layout = QVBoxLayout(style_group)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("输入水印文本")
        style_layout.addWidget(self.text_input)

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.font_family))
        self.font_combo.currentFontChanged.connect(self.on_font_changed)
        font_layout.addWidget(self.font_combo)
        font_layout.addWidget(QLabel("字号:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 120)
        self.font_size_spin.setValue(self.font_size)
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)
        font_layout.addWidget(self.font_size_spin)
        style_layout.addLayout(font_layout)

        style2_layout = QHBoxLayout()
        self.bold_check = QCheckBox("粗体")
        self.bold_check.stateChanged.connect(self.on_bold_changed)
        style2_layout.addWidget(self.bold_check)
        self.italic_check = QCheckBox("斜体")
        self.italic_check.stateChanged.connect(self.on_italic_changed)
        style2_layout.addWidget(self.italic_check)
        style_layout.addLayout(style2_layout)

        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 20)
        self.color_btn.setStyleSheet(f"background: {self.font_color.name()};")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        style_layout.addLayout(color_layout)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.font_opacity)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        style_layout.addLayout(opacity_layout)

        effect_layout = QHBoxLayout()
        self.shadow_check = QCheckBox("阴影")
        self.shadow_check.stateChanged.connect(self.on_shadow_changed)
        effect_layout.addWidget(self.shadow_check)
        self.outline_check = QCheckBox("描边")
        self.outline_check.stateChanged.connect(self.on_outline_changed)
        effect_layout.addWidget(self.outline_check)
        style_layout.addLayout(effect_layout)

        self.btn_apply = QPushButton("应用水印")
        self.btn_apply.clicked.connect(self.apply_watermark)
        style_layout.addWidget(self.btn_apply)

        right_layout.addWidget(style_group)

        # ----------- 水印布局分组 -----------
        layout_group = QGroupBox("水印布局")
        layout_group.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        layout_grid = QGridLayout(layout_group)
        positions = [
            ("左上", "top_left"), ("上中", "top_center"), ("右上", "top_right"),
            ("左中", "center_left"), ("正中", "center"), ("右中", "center_right"),
            ("左下", "bottom_left"), ("下中", "bottom_center"), ("右下", "bottom_right")
        ]
        self.pos_buttons = {}
        for idx, (label, mode) in enumerate(positions):
            btn = QPushButton(label)
            btn.setCheckable(True)
            if mode == self.watermark_pos_mode:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, m=mode: self.set_watermark_pos_mode(m))
            layout_grid.addWidget(btn, idx // 3, idx % 3)
            self.pos_buttons[mode] = btn

        # 旋转滑块
        rotate_layout = QHBoxLayout()
        rotate_layout.addWidget(QLabel("旋转:"))
        self.rotate_slider = QSlider(Qt.Horizontal)
        self.rotate_slider.setRange(-180, 180)
        self.rotate_slider.setValue(self.watermark_angle)
        self.rotate_slider.valueChanged.connect(self.on_rotate_changed)
        rotate_layout.addWidget(self.rotate_slider)
        layout_grid.addLayout(rotate_layout, 3, 0, 1, 3)

        right_layout.addWidget(layout_group)

        # ---------------- 导出设置 ----------------
        export_group = QGroupBox("导出设置")
        export_group.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; }")
        export_layout = QVBoxLayout(export_group)

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

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG"])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        export_layout.addLayout(format_layout)

        # 保存按钮放到导出设置分组内
        self.btn_save = QPushButton("导出图片")
        self.btn_save.clicked.connect(self.save_images)
        export_layout.addWidget(self.btn_save)

        right_layout.addWidget(export_group)
        right_layout.addStretch(1)
        main_layout.addWidget(right_frame)

        # 恢复预览区鼠标事件支持
        self.preview_label.setMouseTracking(True)
        self.preview_label.mousePressEvent = self.preview_mouse_press
        self.preview_label.mouseMoveEvent = self.preview_mouse_move
        self.preview_label.mouseReleaseEvent = self.preview_mouse_release

    # ---------- 字体与样式相关槽函数 ----------
    def on_font_changed(self, font):
        self.font_family = font.family()
        self.apply_watermark()

    def on_font_size_changed(self, size):
        self.font_size = size
        self.apply_watermark()

    def on_bold_changed(self, state):
        self.font_bold = (state == Qt.Checked)
        self.apply_watermark()

    def on_italic_changed(self, state):
        self.font_italic = (state == Qt.Checked)
        self.apply_watermark()

    def choose_color(self):
        color = QColorDialog.getColor(self.font_color, self, "选择字体颜色")
        if color.isValid():
            self.font_color = color
            self.color_btn.setStyleSheet(f"background: {color.name()};")
            self.apply_watermark()

    def on_opacity_changed(self, value):
        self.font_opacity = value
        self.apply_watermark()

    def on_shadow_changed(self, state):
        self.shadow_enabled = (state == Qt.Checked)
        self.apply_watermark()

    def on_outline_changed(self, state):
        self.outline_enabled = (state == Qt.Checked)
        self.apply_watermark()

    # ----------- 九宫格位置选择 -----------
    def set_watermark_pos_mode(self, mode):
        self.watermark_pos_mode = mode
        self.watermark_custom_pos = None  # 切换预设时取消自定义
        for m, btn in self.pos_buttons.items():
            btn.setChecked(m == mode)
        self.apply_watermark()

    # ----------- 旋转 -----------
    def on_rotate_changed(self, value):
        self.watermark_angle = value
        self.apply_watermark()

    # ----------- 预览区鼠标拖拽 -----------
    def preview_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # 判断是否点在水印区域（简化：只要点在预览区就允许拖动）
            self.watermark_dragging = True
            self.watermark_drag_start = event.pos()
            if self.watermark_custom_pos is None:
                self.watermark_custom_pos = self.calc_watermark_pos(event.pos())
            event.accept()

    def preview_mouse_move(self, event: QMouseEvent):
        if self.watermark_dragging:
            # 计算偏移
            delta = event.pos() - self.watermark_drag_start
            if self.watermark_custom_pos is not None:
                self.watermark_custom_pos += delta
            else:
                self.watermark_custom_pos = self.calc_watermark_pos(event.pos())
            self.watermark_drag_start = event.pos()
            self.watermark_pos_mode = "custom"
            for m, btn in self.pos_buttons.items():
                btn.setChecked(False)
            self.apply_watermark()
            event.accept()

    def preview_mouse_release(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.watermark_dragging = False
            event.accept()

    def calc_watermark_pos(self, click_pos):
        # 将点击点作为水印中心
        return click_pos

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
        """高级文字水印（支持九宫格、拖拽、旋转）"""
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
        font = QFont(self.font_family, self.font_size)
        if self.font_bold:
            font.setWeight(QFont.Weight.Bold)
        else:
            font.setWeight(QFont.Weight.Normal)
        font.setItalic(self.font_italic)
        painter.setFont(font)
        color = QColor(self.font_color)
        color.setAlpha(self.font_opacity)
        painter.setPen(color)

        # 计算文本尺寸
        tw = painter.fontMetrics().boundingRect(text).width()
        th = painter.fontMetrics().boundingRect(text).height()

        # 计算水印位置
        if self.watermark_pos_mode == "custom" and self.watermark_custom_pos is not None:
            x = self.watermark_custom_pos.x() - tw // 2
            y = self.watermark_custom_pos.y() + th // 2
        else:
            w, h = base_pixmap.width(), base_pixmap.height()
            margin = 30
            pos_map = {
                "top_left": (margin, margin + th),
                "top_center": (w // 2 - tw // 2, margin + th),
                "top_right": (w - tw - margin, margin + th),
                "center_left": (margin, h // 2 + th // 2),
                "center": (w // 2 - tw // 2, h // 2 + th // 2),
                "center_right": (w - tw - margin, h // 2 + th // 2),
                "bottom_left": (margin, h - margin),
                "bottom_center": (w // 2 - tw // 2, h - margin),
                "bottom_right": (w - tw - margin, h - margin),
            }
            x, y = pos_map.get(self.watermark_pos_mode, (w - tw - margin, h - margin))

        # 旋转变换
        if self.watermark_angle != 0:
            painter.save()
            cx, cy = x + tw // 2, y - th // 2
            transform = QTransform()
            transform.translate(cx, cy)
            transform.rotate(self.watermark_angle)
            transform.translate(-cx, -cy)
            painter.setTransform(transform)

        # 阴影
        if self.shadow_enabled:
            shadow_color = QColor(0, 0, 0, int(self.font_opacity * 0.6))
            painter.setPen(shadow_color)
            painter.drawText(x+2, y+2, text)
            painter.setPen(color)

        # 描边
        if self.outline_enabled:
            outline_color = QColor(0, 0, 0, self.font_opacity)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        painter.setPen(outline_color)
                        painter.drawText(x + dx, y + dy, text)
            painter.setPen(color)

        # 正文
        painter.drawText(x, y, text)

        if self.watermark_angle != 0:
            painter.restore()

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
