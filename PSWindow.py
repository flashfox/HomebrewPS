from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QMenu,
    QAction,
    QFileDialog,
    QMessageBox,
    QLabel,
    QHBoxLayout,
)
from PyQt5.QtGui import QIcon, QPixmap, QImage
from Utils import readBMP, cvtGrayscale, cvtOrderedDithering
from Utils import cvtColoredOrderedDithering
from PyQt5.QtCore import *

# Global consts
DEF_WIDTH = 300
DEF_HEIGHT = 100
INIT_WINDOW_WIDTH = 1024
INIT_WINDOW_HEIGHT = 768
ICON = 'psIcon.png'

class PSWindow(QMainWindow):
    def __init__(self):
        # Window init
        super().__init__()
        self.setWindowTitle("Homebrew Photoshop")
        self.setWindowIcon(QIcon(ICON))
        self.resize(INIT_WINDOW_WIDTH, INIT_WINDOW_HEIGHT)
        self.width = self.height = -1

        # Menu bar: core ops
        self.menuCoreOps = QMenu("&Core Operations", self)
        self.menuCoreOps.addAction(QAction("&Open File", self, shortcut="Ctrl+O", triggered=self.openFile))
        self.menuCoreOps.addAction(QAction("&Exit", self, shortcut="Ctrl+Q", triggered=self.close))
        self.menuCoreOps.addSeparator()
        self.menuCoreOps.addAction(QAction("&Grayscale", self, shortcut="Alt+G", triggered=self.grayScale))
        orderedOpts = [QAction("&2x2 matrix", self), QAction("&4x4 matrix", self), QAction("&8x8 matrix", self)]
        orderedOpts[0].triggered.connect(lambda: self.orderedDithering(0))
        orderedOpts[1].triggered.connect(lambda: self.orderedDithering(1))
        orderedOpts[2].triggered.connect(lambda: self.orderedDithering(2))
        ordDitMenu = self.menuCoreOps.addMenu("&Ordered Dithering")
        ordDitMenu.addActions(orderedOpts)
        self.menuCoreOps.addAction(QAction("&Auto Level", self, shortcut="Alt+A", triggered=self.autolevel))
        self.menuCoreOps.addAction(QAction("&Huffman", self, shortcut="Alt+H", triggered=self.huffman))

        # Menu bar: optional ops
        self.menuOptOps = QMenu("&Optional Operations", self)
        coloredorderdOpts = [QAction("&2x2 matrix", self), QAction("&4x4 matrix", self), QAction("&8x8 matrix", self)]
        coloredorderdOpts[0].triggered.connect(lambda: self.coloredOrderedDithering(0))
        coloredorderdOpts[1].triggered.connect(lambda: self.coloredOrderedDithering(1))
        coloredorderdOpts[2].triggered.connect(lambda: self.coloredOrderedDithering(2))
        coloredOrdDitMenu = self.menuOptOps.addMenu("&Colored Ordered Dithering")
        coloredOrdDitMenu.addActions(coloredorderdOpts)

        self.menuBar().addMenu(self.menuCoreOps)
        self.menuBar().addMenu(self.menuOptOps)

        # Image view
        self.rawImgView = QLabel()
        layout = QHBoxLayout()
        layout.addWidget(self.rawImgView)
        mainView = QWidget()
        mainView.setLayout(layout)
        self.setCentralWidget(mainView)

        # Post-processing view (sub window, unique)
        self.postImgView = None
        self.grayData = None

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'BMP Files (*.png *.jpeg *.jpg *.bmp *.gif)')
        rawData, (width, height), errMsg = readBMP(fileName)
        if width <= 0 or height <= 0:
            if width < 0 or height < 0:
                QMessageBox.information(self, "Homebrew Photoshop", errMsg)
            return
        # reset processed data
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
        if self.grayData is None:
            self.grayData = cvtGrayscale(self.rawData)
        self.postImgView = PostImageWindow(
            [QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888),
             QImage(self.grayData, self.width, self.height, QImage.Format_Grayscale8)],
            "Grayscale")
        self.postImgView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.show()

    def orderedDithering(self, ditType: int = 0):
        if self.width <= 0 or self.height <= 0:
            return
        if self.grayData is None:
            self.grayData = cvtGrayscale(self.rawData)
        grayData = self.grayData
        ditherData = cvtOrderedDithering(grayData, ditType)
        title = ["Ordered Dithering: 2x2 matrix", "Ordered Dithering: 4x4 matrix", "Ordered Dithering: 8x8 matrix"]
        self.postImgView = PostImageWindow(
            [QImage(grayData, self.width, self.height, QImage.Format_Grayscale8),
             QImage(ditherData, self.width, self.height, QImage.Format_Grayscale8)],
             title[ditType])
        self.postImgView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.show()

    def autolevel(self):
        return

    def huffman(self):
        return

    def coloredOrderedDithering(self, ditType: int = 0):
        if self.width <= 0 or self.height <= 0:
            return
        ditherData = cvtColoredOrderedDithering(self.rawData, ditType)
        title = ["Colored Ordered Dithering: 2x2 matrix",
                 "Colored Ordered Dithering: 4x4 matrix",
                 "Colored Ordered Dithering: 8x8 matrix"]
        self.postImgView = PostImageWindow(
            [QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888),
             QImage(ditherData, self.width, self.height, self.width * 3, QImage.Format_RGB888)],
             title[ditType])
        self.postImgView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.postImgView.show()


class PostImageWindow(QWidget):
    def __init__(self, imageList: [QImage], type: str):
        # Window init
        super().__init__()
        self.setWindowTitle(type)
        self.setWindowIcon(QIcon(ICON))
        layout = QHBoxLayout()
        viewList = []
        for img in imageList:
            viewList.append(QLabel())
            viewList[-1].setPixmap(QPixmap(img))
            layout.addWidget(viewList[-1])
        self.setLayout(layout)

