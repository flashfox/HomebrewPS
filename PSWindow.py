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
from Utils import readBMP, cvtGrayscale, cvtOrderedDithering
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
        # self.menuFiles.addAction(QAction("&Ordered Dithering", self, shortcut="Alt+D", triggered=self.orderedDithering))
        ordDitMenu = self.menuFiles.addMenu("&Ordered Dithering")
        opts = [QAction("&2x2 matrix", self), QAction("&4x4 matrix", self), QAction("&8x8 matrix", self)]
        opts[0].triggered.connect(lambda x: self.orderedDithering(0))
        opts[1].triggered.connect(lambda x: self.orderedDithering(1))
        opts[2].triggered.connect(lambda x: self.orderedDithering(2))
        ordDitMenu.addActions(opts)

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
        self.grayData = None

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'BMP Files (*.png *.jpeg *.jpg *.bmp *.gif)')
        rawData, (width, height), errMsg = readBMP(fileName)
        if width <= 0 or height <= 0:
            if width < 0 or height < 0:
                QMessageBox.information(self, "Homebrew Photoshop", errMsg)
            return
        # init processed data
        if self.grayData is not None:
            self.grayData = None
        if self.postImgView is not None:
            self.postImgView = None
        # show opened file
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

        self.show()

    def close(self):
        if self.postImgView:
            self.postImgView = None
        super().close()

    def grayScale(self):
        if self.width <= 0 or self.height <= 0:
            return
        if self.postImgView is not None:
            if self.postImgView.windowTitle() == 'Grayscale':
                return
        data = cvtGrayscale(self.rawData)
        self.grayData = data
        self.postImgView = PostImageWindow(
            [QImage(self.rawData, self.width, self.height, self.width * 3,
                      QImage.Format_RGB888), QImage(data, self.width, self.height, QImage.Format_Grayscale8)],
            "Grayscale")
        self.postImgView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.show()

    def orderedDithering(self, ditType=0):
        if self.width <= 0 or self.height <= 0:
            return
        if self.grayData is None:
            self.grayData = cvtGrayscale(self.rawData)
        grayData = self.grayData
        ditherData = cvtOrderedDithering(grayData, ditType)
        self.postImgView = PostImageWindow(
        [QImage(grayData, self.width, self.height, QImage.Format_Grayscale8),
                  QImage(ditherData, self.width, self.height, QImage.Format_Grayscale8)],
                "Ordered Dithering")
        self.postImgView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.show()

    def autolevel(self):
        return

    def huffman(self):
        return


class PostImageWindow(QWidget):
    def __init__(self, imageList: [QImage], type: str):
        # Window init
        super().__init__()
        self.setWindowTitle(type)
        layout = QHBoxLayout()
        viewList = []
        for img in imageList:
            viewList.append(QLabel())
            viewList[-1].setPixmap(QPixmap(img))
            layout.addWidget(viewList[-1])
        self.setLayout(layout)

