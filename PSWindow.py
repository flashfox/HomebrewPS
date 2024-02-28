from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QMenu,
    QAction,
    QFileDialog,
    QMessageBox,
    QLabel,
    QMdiSubWindow,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt5.QtGui import QIcon, QPixmap, QImage
from Utils import readBMP, cvtGrayscale
from PyQt5.QtCore import *

# Global consts
DEF_WIDTH = 300
DEF_HEIGHT = 100
INIT_WINDOW_WIDTH = 1024
INIT_WINDOW_HEIGHT = 768
class PSWindow(QMainWindow):
    def __init__(self):
        # Window init
        super().__init__()
        self.setWindowTitle("Homebrew Photoshop")
        self.setWindowIcon(QIcon('psIcon.png'))
        self.resize(INIT_WINDOW_WIDTH, INIT_WINDOW_HEIGHT)
        self.width = self.height = -1

        # Menu bar
        self.menuFiles = QMenu("&Core Operations", self)
        self.menuFiles.addAction(QAction("&Open File", self, shortcut="Ctrl+O", triggered=self.openFile))
        self.menuFiles.addAction(QAction("&Exit", self, shortcut="Ctrl+Q", triggered=self.close))
        self.menuFiles.addSeparator()
        self.menuFiles.addAction(QAction("&Grayscale", self, shortcut="Alt+G", triggered=self.grayScale))
        self.menuFiles.addAction(QAction("&Ordered Dithering", self, shortcut="Alt+D", triggered=self.orderedDithering))
        self.menuFiles.addAction(QAction("&Auto Level", self, shortcut="Alt+A", triggered=self.autolevel))
        self.menuFiles.addAction(QAction("&Huffman", self, shortcut="Alt+H", triggered=self.huffman))
        self.menuEdits = QMenu("&Optional Operations", self)

        self.menuBar().addMenu(self.menuFiles)
        self.menuBar().addMenu(self.menuEdits)

        # Image view
        self.rawImgView = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.rawImgView)
        mainView = QWidget()
        mainView.setLayout(layout)
        self.setCentralWidget(mainView)
        # post processing view (sub window)
        self.postImgView = None

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'BMP Files (*.png *.jpeg *.jpg *.bmp *.gif)')
        # self.rawData, (self.width, self.height), errMsg = readBMP(fileName)
        rawData, (width, height), errMsg = readBMP(fileName)
        if width <= 0 or height <= 0:
            if width < 0 or height < 0:
                QMessageBox.information(self, "Homebrew Photoshop", errMsg)
            return
        if self.postImgView:
            self.postImgView = None
        self.rawData = rawData
        self.width = width
        self.height = height
        img = QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        self.rawImgView.setPixmap(pixmap)
        if self.width > 0 and self.height > 0:
            self.setMinimumSize(max(self.width + 20, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
            self.resize(max(self.width + 20, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        else:
            self.setMinimumSize(INIT_WINDOW_WIDTH, INIT_WINDOW_HEIGHT)

        self.update()
        self.show()

    def close(self):
        if self.postImgView:
            self.postImgView = None
        super().close()

    def grayScale(self):
        if self.width <= 0 or self.height <= 0:
            return
        data = cvtGrayscale(self.rawData)
        self.postImgView = PostImageWindow(QImage(data, self.width, self.height, QImage.Format_Grayscale8), "Grayscale")
        self.postImgView.setMinimumSize(max(self.width + 25, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.resize(max(self.width + 25, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.show()

    def orderedDithering(self):
        return

    def autolevel(self):
        return

    def huffman(self):
        return


class PostImageWindow(QWidget):
    def __init__(self, image: QImage, type: str):
        # Window init
        super().__init__()
        self.setWindowTitle(type)
        imgView = QLabel()
        imgView.setPixmap(QPixmap.fromImage(image))
        layout = QHBoxLayout()
        layout.addWidget(imgView)
        self.setLayout(layout)

