import sys
import os
import zipfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QListWidget, QLabel, QMessageBox, QHBoxLayout, QAbstractItemView, QSpinBox, QFormLayout, QGroupBox
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PIL import Image
import tempfile
import subprocess

class ImageToPDF(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image → PDF Converter")
        self.setMinimumSize(900, 550)

        self.image_paths = []
        self.temp_dir = tempfile.mkdtemp()
        self.source_name = "output"

        # لیست تصاویر
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        # پیش‌نمایش
        self.preview_label = QLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedHeight(350)
        self.preview_label.setStyleSheet("background: #222; border: 1px solid #444; color: #aaa;")

        # دکمه‌ها
        load_folder_btn = QPushButton("📁 Load Folder")
        load_folder_btn.clicked.connect(self.load_folder)

        load_zip_btn = QPushButton("🗜 Load ZIP")
        load_zip_btn.clicked.connect(self.load_zip)

        up_btn = QPushButton("⬆ Move Up")
        up_btn.clicked.connect(self.move_up)

        down_btn = QPushButton("⬇ Move Down")
        down_btn.clicked.connect(self.move_down)

        convert_btn = QPushButton("📄 Convert to PDF")
        convert_btn.clicked.connect(self.convert_to_pdf)

        clear_btn = QPushButton("🧹 Clear List")
        clear_btn.clicked.connect(self.clear_list)

        # SpinBox کیفیت PDF
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(100)
        self.quality_spin.setSuffix("%")

        # فرم کیفیت PDF
        quality_layout = QFormLayout()
        quality_layout.addRow("PDF Quality:", self.quality_spin)

        # گروه دکمه‌ها و کنترل‌ها
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout()
        for b in [load_folder_btn, load_zip_btn, up_btn, down_btn, convert_btn, clear_btn]:
            b.setStyleSheet("padding: 8px; font-size: 14px;")
            control_layout.addWidget(b)
        control_layout.addLayout(quality_layout)
        control_group.setLayout(control_layout)

        # چیدمان چپ و راست
        left_layout = QVBoxLayout()
        left_layout.addWidget(control_group)
        left_layout.addWidget(self.list_widget)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.preview_label)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 35)
        main_layout.addLayout(right_layout, 65)

        self.setLayout(main_layout)

        self.list_widget.currentItemChanged.connect(self.update_preview)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Folder")
        if not folder:
            return

        self.source_name = os.path.basename(folder)
        self.image_paths.clear()
        self.list_widget.clear()

        for f in sorted(os.listdir(folder)):
            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                full = os.path.join(folder, f)
                self.image_paths.append(full)
                self.list_widget.addItem(f)

    def load_zip(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Choose ZIP File", "", "ZIP Files (*.zip)"
        )
        if not file:
            return

        self.source_name = os.path.basename(file)
        self.image_paths.clear()
        self.list_widget.clear()

        with zipfile.ZipFile(file, 'r') as z:
            for name in z.namelist():
                if name.lower().endswith((".png", ".jpg", ".jpeg")):
                    extracted = z.extract(name, self.temp_dir)
                    self.image_paths.append(extracted)
                    self.list_widget.addItem(os.path.basename(extracted))

    def update_preview(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return

        image = QImage(self.image_paths[row])
        if image.isNull():
            self.preview_label.setText("Cannot preview")
            return

        pix = QPixmap.fromImage(image)
        pix = pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio)
        self.preview_label.setPixmap(pix)

    def move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            self.image_paths[row], self.image_paths[row - 1] = \
                self.image_paths[row - 1], self.image_paths[row]

            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)

    def move_down(self):
        row = self.list_widget.currentRow()
        if row < len(self.image_paths) - 1:
            self.image_paths[row], self.image_paths[row + 1] = \
                self.image_paths[row + 1], self.image_paths[row]

            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)

    def clear_list(self):
        self.image_paths.clear()
        self.list_widget.clear()
        self.preview_label.clear()
        self.preview_label.setText("Preview")

    def convert_to_pdf(self):
        if not self.image_paths:
            QMessageBox.warning(self, "Error", "No images selected.")
            return

        pil_images = []
        for p in self.image_paths:
            img = Image.open(p)
            if img.mode != "RGB":
                img = img.convert("RGB")
            dpi = img.info.get("dpi", (300, 300))
            pil_images.append((img, dpi))

        output_dir = os.path.join(os.getcwd(), "output_pdfs")
        os.makedirs(output_dir, exist_ok=True)

        name = os.path.splitext(self.source_name)[0]
        output_pdf = os.path.join(output_dir, f"{name}.pdf")

        first, first_dpi = pil_images[0]
        others = [img for img, _ in pil_images[1:]]

        quality = self.quality_spin.value()

        first.save(
            output_pdf,
            save_all=True,
            append_images=others,
            resolution=first_dpi[0],
            quality=quality
        )

        QMessageBox.information(self, "Done", f"PDF created:\n{output_pdf}")

        try:
            if sys.platform.startswith("win"):
                os.startfile(output_pdf)
            elif sys.platform == "darwin":
                subprocess.call(["open", output_pdf])
            else:
                subprocess.call(["xdg-open", output_pdf])
        except:
            pass


app = QApplication(sys.argv)
w = ImageToPDF()
w.show()
sys.exit(app.exec())
