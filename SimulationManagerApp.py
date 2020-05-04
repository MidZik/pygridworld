import SimulationManager as sm
import window
from PyQt5 import QtCore, QtGui, QtWidgets


class App:
    def __init__(self, argv):
        self._app = QtWidgets.QApplication(argv)
        self._main_window = QtWidgets.QMainWindow()
        ui = window.Ui_MainWindow()
        ui.setupUi(self._main_window)
        self._ui = ui

        ui.actionOpen_Project.triggered.connect(self._open_project)

        self._project = None

    def _open_project(self):
        from PyQt5.QtWidgets import QFileDialog
        project_dir = QFileDialog.getExistingDirectory(self._main_window, options=QFileDialog.ShowDirsOnly)

        self._project = sm.TimelinesProject.load_project(project_dir)

        print("test")

    def run(self):
        self._main_window.show()
        return self._app.exec()


if __name__ == "__main__":
    import sys
    app = App(sys.argv)
    app.run()
