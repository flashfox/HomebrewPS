import sys
from PyQt5.QtWidgets import QApplication
from PSWindow import PSWindow
try:
    CUSTOMTHEME = True
    import qdarktheme
except ModuleNotFoundError:
    CUSTOMTHEME = False

if __name__ == '__main__':
    mainApp = QApplication(sys.argv)
    if CUSTOMTHEME and len(sys.argv[1:]) == 0:
        qdarktheme.setup_theme(custom_colors={"background": "#404040"})
    psWindow = PSWindow()
    psWindow.show()
    sys.exit(mainApp.exec_())