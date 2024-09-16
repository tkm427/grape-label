import csv
import json
import os
import re
import sys

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ImageLabelingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.images = []
        self.coordinates = []
        self.current_image_index = 0
        self.labels = {}
        self.next_label = 1
        self.labeled_images = set()
        self.image_folder = ""
        self.coordinate_file = ""

    def initUI(self):
        self.setWindowTitle("Image Labeling App")
        self.setGeometry(100, 100, 1200, 600)

        layout = QVBoxLayout()

        self.image_layout = QHBoxLayout()

        # Left image layout
        left_layout = QVBoxLayout()
        self.image1 = QLabel(self)
        self.image1_combo = QComboBox(self)
        self.image1_combo.currentIndexChanged.connect(self.update_left_image)
        left_layout.addWidget(self.image1_combo)
        left_layout.addWidget(self.image1)

        # Right image layout
        right_layout = QVBoxLayout()
        self.image2 = QLabel(self)
        self.image2_label = QLabel(self)
        self.image2_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.image2_label)
        right_layout.addWidget(self.image2)

        self.image_layout.addLayout(left_layout)
        self.image_layout.addLayout(right_layout)
        layout.addLayout(self.image_layout)

        button_layout = QHBoxLayout()

        self.load_images_button = QPushButton("Load Images Folder", self)
        self.load_images_button.clicked.connect(self.load_images_folder)
        button_layout.addWidget(self.load_images_button)

        self.load_coordinates_button = QPushButton("Load Coordinates", self)
        self.load_coordinates_button.clicked.connect(self.load_coordinates)
        button_layout.addWidget(self.load_coordinates_button)

        self.next_button = QPushButton("Next Images", self)
        self.next_button.clicked.connect(self.next_images)
        button_layout.addWidget(self.next_button)

        self.save_button = QPushButton("Save Labels", self)
        self.save_button.clicked.connect(self.save_labels)
        button_layout.addWidget(self.save_button)

        self.save_state_button = QPushButton("Save State", self)
        self.save_state_button.clicked.connect(self.save_state)
        button_layout.addWidget(self.save_state_button)

        self.load_state_button = QPushButton("Load State", self)
        self.load_state_button.clicked.connect(self.load_state)
        button_layout.addWidget(self.load_state_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_images_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Images Folder")
        if folder_path:
            self.load_images_from_folder(folder_path)

    def load_images_from_folder(self, folder_path):
        self.image_folder = folder_path
        image_files = [
            f
            for f in os.listdir(folder_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
        ]

        # Sort image files based on the number in their filename
        image_files.sort(key=lambda x: int(re.search(r"\d+", x).group()))

        self.images = [os.path.join(folder_path, f) for f in image_files]
        self.current_image_index = 0
        self.update_image_combo()
        self.update_images()
        print(f"Loaded {len(self.images)} images from folder.")

    def load_coordinates(self):
        file_dialog = QFileDialog()
        csv_file, _ = file_dialog.getOpenFileName(
            self, "Select Coordinate CSV", "", "CSV Files (*.csv)"
        )
        if csv_file:
            self.load_coordinates_from_file(csv_file)

    def load_coordinates_from_file(self, csv_file):
        self.coordinate_file = csv_file
        self.coordinates = []
        with open(csv_file, "r") as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                frame, x, y = int(row[0]), float(row[1]), float(row[2])
                self.coordinates.append((frame, x, y))
        print(f"Loaded {len(self.coordinates)} coordinate points.")
        self.auto_label_first_image()
        self.update_images()

    def auto_label_first_image(self):
        first_frame_coords = [
            i for i, coord in enumerate(self.coordinates) if coord[0] == 0
        ]
        for i, coord_index in enumerate(first_frame_coords):
            self.labels[coord_index] = i + 1
        self.next_label = max(self.labels.values(), default=0) + 1
        self.labeled_images.add(0)
        self.update_image_combo()

    def update_image_combo(self):
        self.image1_combo.clear()
        for i in sorted(self.labeled_images):
            self.image1_combo.addItem(f"Image {i+1}")
        if self.image1_combo.count() == 0:
            self.image1_combo.addItem("No labeled images yet")
            self.image1_combo.setEnabled(False)
        else:
            self.image1_combo.setEnabled(True)

    def update_left_image(self, index):
        if (
            self.image1_combo.count() > 0
            and self.image1_combo.currentText() != "No labeled images yet"
        ):
            image_index = int(self.image1_combo.currentText().split()[1]) - 1
            self.image1.setPixmap(QPixmap(self.images[image_index]))
            self.draw_points(self.image1, image_index)

    def update_images(self):
        if self.current_image_index < len(self.images):
            self.update_image_combo()
            self.image1.setPixmap(QPixmap(self.images[self.current_image_index]))
            self.draw_points(self.image1, self.current_image_index)

            if self.current_image_index + 1 < len(self.images):
                self.image2.setPixmap(
                    QPixmap(self.images[self.current_image_index + 1])
                )
                self.draw_points(self.image2, self.current_image_index + 1)
                self.image2_label.setText(
                    f"Image {self.current_image_index + 2} / {len(self.images)}"
                )
            else:
                self.image2.clear()
                self.image2_label.setText("No more images")

    def draw_points(self, image_label, frame):
        pixmap = image_label.pixmap()
        if pixmap:
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            for i, coord in enumerate(self.coordinates):
                if coord[0] == frame:
                    if i in self.labels:
                        painter.setPen(
                            QPen(QColor(0, 255, 0), 5)
                        )  # Green for labeled points
                        painter.drawPoint(QPointF(coord[1], coord[2]))

                        # Draw label number in white
                        painter.setPen(QPen(Qt.white))
                        painter.setFont(QFont("Arial", 10, QFont.Bold))
                        painter.drawText(
                            QPointF(coord[1] + 5, coord[2] - 5), str(self.labels[i])
                        )
                    else:
                        painter.setPen(QPen(Qt.red, 5))
                        painter.drawPoint(QPointF(coord[1], coord[2]))

            painter.end()
            image_label.setPixmap(pixmap)

    def next_images(self):
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.update_images()
        else:
            print("No more images to display.")

    def mousePressEvent(self, event):
        for i, image_label in enumerate([self.image1, self.image2]):
            if image_label.geometry().contains(event.pos()):
                local_pos = image_label.mapFrom(self, event.pos())
                frame = (
                    self.current_image_index if i == 0 else self.current_image_index + 1
                )
                self.label_point(frame, local_pos.x(), local_pos.y())

    def label_point(self, frame, x, y):
        for i, coord in enumerate(self.coordinates):
            if coord[0] == frame and abs(coord[1] - x) < 5 and abs(coord[2] - y) < 5:
                if frame == 0:
                    # First image points are already labeled, do nothing
                    pass
                else:
                    existing_labels = sorted(set(self.labels.values()))
                    label, ok = QInputDialog.getItem(
                        self,
                        "Select Label",
                        "Choose a label or enter a new one:",
                        [str(label) for label in existing_labels] + ["New Label"],
                    )
                    if ok:
                        if label == "New Label":
                            new_label = max(self.labels.values(), default=0) + 1
                            self.labels[i] = new_label
                            self.next_label = new_label + 1
                        else:
                            self.labels[i] = int(label)

                self.labeled_images.add(frame)
                self.update_images()
                break

    def save_labels(self):
        file_dialog = QFileDialog()
        output_file, _ = file_dialog.getSaveFileName(
            self, "Save Labeled Coordinates", "", "CSV Files (*.csv)"
        )
        if output_file:
            with open(output_file, "w", newline="") as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(["Frame", "X", "Y", "Label"])
                for i, coord in enumerate(self.coordinates):
                    label = self.labels.get(i, "")
                    csv_writer.writerow([coord[0], coord[1], coord[2], label])
            print(f"Saved labeled coordinates to {output_file}")

    def save_state(self):
        file_dialog = QFileDialog()
        state_file, _ = file_dialog.getSaveFileName(
            self, "Save Current State", "", "JSON Files (*.json)"
        )
        if state_file:
            state = {
                "image_folder": self.image_folder,
                "coordinate_file": self.coordinate_file,
                "current_image_index": self.current_image_index,
                "labels": self.labels,
                "next_label": self.next_label,
                "labeled_images": list(self.labeled_images),
            }
            with open(state_file, "w") as f:
                json.dump(state, f)
            print(f"Saved current state to {state_file}")

    def load_state(self):
        file_dialog = QFileDialog()
        state_file, _ = file_dialog.getOpenFileName(
            self, "Load Saved State", "", "JSON Files (*.json)"
        )
        if state_file:
            with open(state_file, "r") as f:
                state = json.load(f)

            self.image_folder = state["image_folder"]
            self.coordinate_file = state["coordinate_file"]
            self.current_image_index = state["current_image_index"]
            self.labels = {int(k): v for k, v in state["labels"].items()}
            self.next_label = state["next_label"]
            self.labeled_images = set(state["labeled_images"])

            self.load_images_from_folder(self.image_folder)
            self.load_coordinates_from_file(self.coordinate_file)
            self.update_images()
            print(f"Loaded state from {state_file}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageLabelingApp()
    ex.show()
    sys.exit(app.exec_())
