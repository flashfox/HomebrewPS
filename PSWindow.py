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
    QTabWidget
)
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt
from superqt import QLabeledRangeSlider, QLabeledDoubleSlider

from Utils import readBMP, cvtGrayscale, cvtAlignedData, cvtOrderedDithering, colorAdjustment, normalize, calEntropy
from Utils import histogram, calHuffman
import numpy as np

# Global consts
DEF_WIDTH = 300
DEF_HEIGHT = 100
INIT_WINDOW_WIDTH = 1024
INIT_WINDOW_HEIGHT = 768
ICON = 'icon.png'
QSS = """
    QRangeSlider{
        background-color: none;
    }
"""

class PSWindow(QMainWindow):
    def __init__(self):
        # Window init
        super().__init__()
        self.setWindowTitle("Homebrew Photoshop")
        # self.setStyleSheet("background-color:  #808080;")
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
        self.menuOptOps.addAction(QAction("&Color Adjustment", self, shortcut="Alt+L", triggered=self.levelAdjustment))

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
        self.popupView = None
        self.grayData = None

        # Pixmap caches
        self.rawPix = None
        self.grayPix = None

    def openFile(self):
        # Reset previous Pixmap caches if present
        self.rawPix = None
        self.grayPix = None
        # Open new file
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'BMP Files (*.bmp)')
        rawData, (width, height), errMsg = readBMP(fileName)
        if width <= 0 or height <= 0:
            if width < 0 or height < 0:
                QMessageBox.information(self, "Homebrew Photoshop", errMsg + ": %s"%fileName)
            return
        # reset processed data
        if self.grayData is not None:
            self.grayData = None
        if self.popupView is not None:
            self.popupView = None
        # show opened file
        self.rawData = rawData
        self.width = width
        self.height = height
        img = QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888)
        self.rawPix = QPixmap.fromImage(img)
        self.rawImgView.setPixmap(self.rawPix)
        if self.width > 0 and self.height > 0:
            self.setMinimumSize(max(self.width + 20, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
            self.resize(max(self.width + 20, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        else:
            self.setMinimumSize(INIT_WINDOW_WIDTH, INIT_WINDOW_HEIGHT)
        self.show()

    def close(self):
        if self.popupView:
            self.popupView = None
        super().close()

    def grayScale(self):
        if self.width <= 0 or self.height <= 0:
            return
        if self.popupView is not None:
            if self.popupView.windowTitle() == 'Grayscale':
                return
        if self.grayData is None:
            self.grayData = cvtGrayscale(self.rawData)
        # Grayscale needs to be 32-aligned as per required by Qt API
        alignedData = cvtAlignedData(self.grayData)
        if self.rawPix is None:
            self.rawPix = QPixmap(QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888))
        if self.grayPix is None:
            self.grayPix = QPixmap(QImage(alignedData, self.width, self.height, QImage.Format_Grayscale8))
        # Set up popup view
        preView, postView = QLabel(), QLabel()
        preView.setPixmap(self.rawPix)
        postView.setPixmap(self.grayPix)
        self.popupView = PopupWindow([preView, postView], "Grayscale", vertical=False)
        self.popupView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popupView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popupView.show()

    def orderedDithering(self, opt: int = 0, colored: bool = False):
        if self.width <= 0 or self.height <= 0:
            return
        title = ["Ordered Dithering: 2x2 matrix",
                 "Ordered Dithering: 4x4 matrix",
                 "Ordered Dithering: 8x8 matrix"][opt]
        if not colored:
            # Grayscale ordered dithering
            if self.grayData is None:
                self.grayData = cvtGrayscale(self.rawData)
            alignedData = cvtAlignedData(self.grayData)
            posData = cvtOrderedDithering(alignedData, opt)
            if self.grayPix is None:
                self.grayPix = QPixmap(QImage(alignedData, self.width, self.height, QImage.Format_Grayscale8))
            prePix = self.grayPix
            postPix = QPixmap(QImage(posData, self.width, self.height, QImage.Format_Grayscale8))
        else:
            # Colored ordered dithering
            posData = cvtOrderedDithering(self.rawData, opt)
            if self.rawPix is None:
                self.rawPix = QPixmap(QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888))
            prePix = self.rawPix
            postPix = QPixmap(QImage(posData, self.width, self.height, self.width * 3, QImage.Format_RGB888))
            title = "Colored " + title

        # Set up popup view
        preView, postView = QLabel(), QLabel()
        preView.setPixmap(prePix)
        postView.setPixmap(postPix)
        self.popupView = PopupWindow([preView, postView], title, vertical=False)
        self.popupView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popupView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popupView.show()

    '''
    Autolevel: approaching the effect of the algorithm "Enhance brightness and contrast" in Photoshop
    '''
    def autolevel(self):
        if self.width <= 0 or self.height <= 0:
            return
        if self.popupView is not None:
            if self.popupView.windowTitle() == 'Auto Level':
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
        med = (flattened[(len(flattened) - 1) // 2] + flattened[len(flattened) // 2]) / 2
        # Gamma is forced to fall in range (0.01, 9.99)
        gamma = min(max(np.emath.logn(0.5, max(med - low, 1) / max(high - low, 1)), 0.01), 9.99)
        # Apply adjustment on RGB channels respectively
        leveledData = self.rawData
        for channel in range(3):
            leveledData = colorAdjustment(leveledData, channel, inSlider=(low, gamma, high))
        # Set up popup view
        rawView, postView = QLabel(), QLabel()
        if self.rawPix is None:
            self.rawPix = QPixmap(QImage(self.rawData, self.width, self.height, self.width * 3, QImage.Format_RGB888))
        rawView.setPixmap(self.rawPix)
        postView.setPixmap((QPixmap(QImage(leveledData, self.width, self.height, self.width * 3, QImage.Format_RGB888))))
        self.popupView = PopupWindow([rawView, postView], "Auto Level", vertical=False)
        self.popupView.setMinimumSize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popupView.resize(max(self.width * 2 + 40, DEF_WIDTH), max(self.height + 48, DEF_HEIGHT))
        self.popupView.show()

    def huffman(self):
        if self.width <= 0 or self.height <= 0:
            return
        if self.popupView is not None:
            if self.popupView.windowTitle() == 'Huffman':
                return
        if self.grayData is None:
            self.grayData = cvtGrayscale(self.rawData)
        # text of entropy and Huffman code length
        hist = histogram(self.grayData)
        entropy = calEntropy(hist)[0, 0]
        avgLength = calHuffman(hist[0])
        # Set up popup view
        self.popupView = PopupWindow([QLabel("Entropy (bps): <b>%.3f</b>" % entropy),
                                      QLabel("Average Huffman Code Length (bps): <b>%.3f</b>" % avgLength)],
                                     "Huffman")
        self.popupView.setMinimumSize(DEF_WIDTH, DEF_HEIGHT)
        self.popupView.show()

    def levelAdjustment(self):
        if self.width <= 0 or self.height <= 0:
            return
        if self.popupView is not None:
            if self.popupView.windowTitle() == 'Color Adjustment':
                return
        self.popupView = LevelAdjWindow(self.rawData)
        self.popupView.show()


class PopupWindow(QWidget):
    def __init__(self, widgetList: [QWidget], type: str, vertical: bool = True):
        # Window init
        super().__init__()
        self.setWindowTitle(type)
        # self.setStyleSheet("background-color:  #808080;")
        self.setWindowIcon(QIcon(ICON))
        layout = QVBoxLayout() if vertical else QHBoxLayout()
        for wid in widgetList:
            layout.addWidget(wid)
        self.setLayout(layout)

class LevelAdjWindow(QWidget):

    class CustomSlider(QLabeledDoubleSlider):
        def __init__(self, channel: int = -1, sliderId: int = -1):
            super().__init__(Qt.Orientation.Horizontal)
            self.channel = channel
            self.sliderId = sliderId
        def setValue(self, *args):
            super().setValue(*args)
        def setRange(self, *args):
            super().setRange(*args)
        def connect(self, *args):
            super().valueChanged.connect(*args)
    class CustomRangeSlider(QLabeledRangeSlider):
        def __init__(self, channel: int = -1, sliderId: int = -1):
            super().__init__(Qt.Orientation.Horizontal)
            self.channel = channel
            self.sliderId = sliderId
        def setValue(self, *args):
            super().setValue(*args)
        def setRange(self, *args):
            super().setRange(*args)
        def connect(self, *args):
            super().valueChanged.connect(*args)

    def __init__(self, data: np.ndarray):
        super().__init__()
        self.setWindowTitle('Color Adjustment')
        self.setWindowIcon(QIcon(ICON))
        self.rawData = data
        # Image view
        pix = QPixmap(QImage(self.rawData, data.shape[1], data.shape[0], data.shape[1] * 3, QImage.Format_RGB888))
        self.imgView = QLabel()
        self.imgView.setPixmap(pix)

        # Adjustment parameters: [[gamma], [in Level], [out Level]]
        # gamma: [all, R, G, B]
        # in/out level: [all, R, G, B], each channel (all, R, G, B): (low, high)
        self.parameters = [[1.0, 1.0, 1.0, 1.0],
                           [(0, 255), (0, 255), (0, 255), (0, 255)],
                           [(0, 255), (0, 255), (0, 255), (0, 255)]]

        # Sliders: [all, R, G, B]
        self.sliders = []
        for channel in range(4):
            self.sliders.append([])
            # sliders[]: [in gamma, in level, out level]
            for sliderId in range(3):
                if sliderId == 0:
                    slider = self.CustomSlider(channel, sliderId)
                    slider.setRange(0.01, 9.99)
                    slider.setValue(self.parameters[0][channel])
                else:
                    slider = self.CustomRangeSlider(channel, sliderId)
                    slider.setRange(0, 255)
                    slider.setValue(self.parameters[sliderId][channel])

                slider.valueChanged.connect(self.sliderChanged)
                slider.setStyleSheet(QSS)
                slider.setTracking(True)
                self.sliders[-1].append(slider)

        # Tab control view
        self.tabViews = []
        tabNames = ['All Channels', 'Red', 'Green', 'Blue']
        sliderNames = ['<b>Input Gamma</b>', '<b>Input Level</b>', '<b>Output Level</b>']
        tabViews = QTabWidget()
        for channel in range(4):
            tabLayout = QVBoxLayout()
            for sliderId in range(3):
                tabLayout.addWidget(QLabel(sliderNames[sliderId]))
                tabLayout.addWidget(self.sliders[channel][sliderId])
            tabView = QWidget()
            tabView.setLayout(tabLayout)
            tabView.setFixedSize(300, 300)
            tabViews.addTab(tabView, tabNames[channel])

        # Set up popup view
        layout = QHBoxLayout()
        layout.addWidget(self.imgView)
        layout.addWidget(tabViews)
        self.setLayout(layout)


    # All-in-one handler for sliders
    def sliderChanged(self, data):
        channel, sliderId = self.sender().channel, self.sender().sliderId
        self.parameters[sliderId][channel] = data
        if channel == 0:
            for channelId in range(1, 4):
                self.sliders[channelId][sliderId].setValue(data)
        else:
            self.updateImage()

    def updateImage(self):
        data = self.rawData
        for channel in range(1, 4):
            data = colorAdjustment(data,
                                   channel - 1,
                                   (self.parameters[1][channel][0],
                                    self.parameters[0][channel],
                                    self.parameters[1][channel][1]),
                                   (self.parameters[2][channel][0],
                                    self.parameters[2][channel][1])
                                   )
        pix = QPixmap(QImage(data, data.shape[1], data.shape[0], data.shape[1] * 3, QImage.Format_RGB888))
        self.imgView.setPixmap(pix)

