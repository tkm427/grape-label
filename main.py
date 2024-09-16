import csv
import sys

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
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

    def initUI(self):
        self.setWindowTitle("Image Labeling App")
        self.setGeometry(100, 100, 1200, 600)

        layout = QVBoxLayout()

        self.image_layout = QHBoxLayout()
        self.image1 = QLabel(self)
        self.image2 = QLabel(self)
        self.image_layout.addWidget(self.image1)
        self.image_layout.addWidget(self.image2)
        layout.addLayout(self.image_layout)

        self.next_button = QPushButton("Next Images", self)
        self.next_button.clicked.connect(self.next_images)
        layout.addWidget(self.next_button)

        self.setLayout(layout)

    def load_images(self):
        file_dialog = QFileDialog()
        image_files, _ = file_dialog.getOpenFileNames(
            self, "Select Images", "", "Image Files (*.png *.jpg *.bmp)"
        )
        self.images = image_files
        self.current_image_index = 0
        self.update_images()

    def load_coordinates(self):
        file_dialog = QFileDialog()
        csv_file, _ = file_dialog.getOpenFileName(
            self, "Select Coordinate CSV", "", "CSV Files (*.csv)"
        )
        with open(csv_file, "r") as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                frame, x, y = int(row[0]), float(row[1]), float(row[2])
                self.coordinates.append((frame, x, y))

    def update_images(self):
        if self.current_image_index < len(self.images) - 1:
            self.image1.setPixmap(QPixmap(self.images[self.current_image_index]))
            self.image2.setPixmap(QPixmap(self.images[self.current_image_index + 1]))
            self.draw_points()

    def draw_points(self):
        for i, image_label in enumerate([self.image1, self.image2]):
            pixmap = image_label.pixmap()
            painter = QPainter(pixmap)
            painter.setPen(QPen(Qt.red, 5))

            frame = self.current_image_index + i
            for coord in self.coordinates:
                if coord[0] == frame:
                    painter.drawPoint(QPointF(coord[1], coord[2]))

            painter.end()
            image_label.setPixmap(pixmap)

    def next_images(self):
        self.current_image_index += 1
        self.update_images()

    def mousePressEvent(self, event):
        for i, image_label in enumerate([self.image1, self.image2]):
            if image_label.geometry().contains(event.pos()):
                local_pos = image_label.mapFrom(self, event.pos())
                self.label_point(i, local_pos.x(), local_pos.y())

    def label_point(self, image_index, x, y):
        frame = self.current_image_index + image_index
        for i, coord in enumerate(self.coordinates):
            if coord[0] == frame and abs(coord[1] - x) < 5 and abs(coord[2] - y) < 5:
                if frame == 0:
                    self.labels[i] = self.next_label
                    self.next_label += 1
                else:
                    # TODO: Implement label selection logic for subsequent frames
                    pass
                self.update_images()
                break

    def save_labels(self):
        file_dialog = QFileDialog()
        output_file, _ = file_dialog.getSaveFileName(
            self, "Save Labeled Coordinates", "", "CSV Files (*.csv)"
        )
        with open(output_file, "w", newline="") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["Frame", "X", "Y", "Label"])
            for i, coord in enumerate(self.coordinates):
                label = self.labels.get(i, "")
                csv_writer.writerow([coord[0], coord[1], coord[2], label])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageLabelingApp()
    ex.show()
    ex.load_images()
    ex.load_coordinates()
    sys.exit(app.exec_())
