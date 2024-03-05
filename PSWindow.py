from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QMenu,
    QAction,
    QFileDialog,
    QMessageBox,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
)
from PyQt5.QtGui import QIcon, QPixmap, QImage
# Core operations
from Utils import readBMP, cvtGrayscale, cvtAlignedData, cvtOrderedDithering, colorAdjustment, normalize, calEntropy
# Optional operations
from Utils import histogram
import numpy as np

# Global consts
DEF_WIDTH = 300
DEF_HEIGHT = 100
INIT_WINDOW_WIDTH = 1024
INIT_WINDOW_HEIGHT = 768
ICON = 'icon.png'

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
        self.menuCoreOps.addAction(QAction("&Open File ...", self, shortcut="Ctrl+O", triggered=self.openFile))
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
        coloredorderdOpts[0].triggered.connect(lambda: self.orderedDithering(0, True))
        coloredorderdOpts[1].triggered.connect(lambda: self.orderedDithering(1, True))
        coloredorderdOpts[2].triggered.connect(lambda: self.orderedDithering(2, True))
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
        self.popView = None
        self.grayData = None

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'BMP Files (*.png *.jpeg *.jpg *.bmp *.gif)')
        rawData, (width, height), errMsg = readBMP(fileName)
        if width <= 0 or height <= 0:
            if width < 0 or height < 0:
                QMessageBox.information(self, "Homebrew Photoshop", errMsg + ": %s"%fileName)
            return
        # reset processed data
        if self.grayData is not None:
            self.grayData = None
        if self.popView is not None:
            self.popView = None
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
        if self.popView:
            self.popView = None
        super().close()

    def grayScale(self):
        if self.width <= 0 or self.height <= 0:
            return
        if self.popView is not None:
            if self.popView.windowTitle() == 'Grayscale':
                return
        if self.grayData is None:
            self.grayData = cvtGrayscale(self.rawData)
        showData = cvtAlignedData(self.grayData)
        self.popView = PostImageWindow(
            [QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888),
             QImage(showData, self.width, self.height, QImage.Format_Grayscale8)],
            "Grayscale")
        self.popView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popView.show()

    def orderedDithering(self, opt: int = 0, colored: bool = False):
        if self.width <= 0 or self.height <= 0:
            return
        if not colored:
            if self.grayData is None:
                self.grayData = cvtGrayscale(self.rawData)
            data = cvtAlignedData(self.grayData)
        else:
            data = self.rawData
        title = ["Ordered Dithering: 2x2 matrix",
                 "Ordered Dithering: 4x4 matrix",
                 "Ordered Dithering: 8x8 matrix"]
        ditherData = cvtOrderedDithering(data, opt)
        if not colored:
            self.popView = PostImageWindow(
                [QImage(data, self.width, self.height, QImage.Format_Grayscale8),
                 QImage(ditherData, self.width, self.height, QImage.Format_Grayscale8)],
                 title[opt])
        else:
            self.popView = PostImageWindow(
                [QImage(data, self.width, self.height, self.width * 3, QImage.Format_RGB888),
                 QImage(ditherData, self.width, self.height, self.width * 3, QImage.Format_RGB888)],
                "Colored " + title[opt])
        self.popView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popView.show()

    '''
    Autolevel: approaching the effect of the algorithm "Enhance brightness and contrast" in Photoshop
    '''
    def autolevel(self):
        if self.width <= 0 or self.height <= 0:
            return
        if self.popView is not None:
            if self.popView.windowTitle() == 'Auto Level':
                return
        if self.grayData is None:
            self.grayData = cvtGrayscale(self.rawData)
        # Normalize grayscale to (0-255)
        grayData = normalize(self.grayData, (0, 255))
        flattened = np.sort(grayData[:, :, 0], axis=None)
        # Cut off lowest and highest values, by 0.1% of total number of values respectively
        cuttingRate = 0.001
        low, high = flattened[int(len(flattened) * cuttingRate)], flattened[-(1 + int(len(flattened) * cuttingRate))]
        # Gamma adjustment determined by median (half of cut range) against 128 (half of 255)
        # Gamma is forced to fall in range (0.01, 9.99)
        med = (flattened[(len(flattened) - 1) // 2] + flattened[len(flattened) // 2]) / 2
        gamma = min(max(np.emath.logn(0.5, max(med - low, 1) / max(high - low, 1)), 0.01), 9.99)
        # Apply adjustment on RGB channels respectively
        leveled = self.rawData
        for channel in range(3):
            leveled = colorAdjustment(leveled, channel, inSlider=(low, gamma, high))

        self.popView = PostImageWindow(
            [QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888),
             QImage(leveled, self.width, self.height, self.width * 3, QImage.Format_RGB888)],
            "Auto Level")
        self.popView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popView.show()

    def huffman(self):
        if self.width <= 0 or self.height <= 0:
            return
        if self.popView is not None:
            if self.popView.windowTitle() == 'Huffman':
                return
        if self.grayData is None:
            self.grayData = cvtGrayscale(self.rawData)
        showData = cvtAlignedData(self.grayData)
        # gray image
        grayWid = QLabel()
        grayWid.setPixmap(QPixmap(QImage(showData, self.width, self.height, QImage.Format_Grayscale8)))
        # text of entropy and Huffman code length
        hist = histogram(self.grayData)
        entropy = calEntropy(hist)[0]
        # Show gray image and entroy and Huffman code length
        self.popView = DynamicWindow([grayWid, QLabel("Entropy: %.3f"%entropy)], "Huffman")
        self.popView.setMinimumSize(max(self.width + 25, DEF_WIDTH), max(self.height + 68, DEF_HEIGHT))
        self.popView.resize(max(self.width + 25, DEF_WIDTH), max(self.height + 68, DEF_HEIGHT))
        self.popView.show()


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

class DynamicWindow(QWidget):
    def __init__(self, widgetList: [QWidget], type: str):
        # Window init
        super().__init__()
        self.setWindowTitle(type)
        self.setWindowIcon(QIcon(ICON))
        layout = QVBoxLayout()
        for wid in widgetList:
            layout.addWidget(wid)
        self.setLayout(layout)

