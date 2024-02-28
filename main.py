import sys
from PyQt5.QtWidgets import QApplication
from PSWindow import PSWindow
import qdarktheme

if __name__ == '__main__':
    mainApp = QApplication(sys.argv)
    qdarktheme.setup_theme(custom_colors={"background": "#404040"})
    psWindow = PSWindow()
    psWindow.show()
    sys.exit(mainApp.exec_())