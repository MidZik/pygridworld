import SimulationManager as sm
import window
from typing import Optional
from PyQt5 import QtCore, QtGui, QtWidgets


class App:
    def __init__(self, argv):
        self._app = QtWidgets.QApplication(argv)
        self._main_window = QtWidgets.QMainWindow()
        ui = window.Ui_MainWindow()
        ui.setupUi(self._main_window)
        self._ui = ui

        ui.actionOpen_Project.triggered.connect(self._open_project)

        self._project: Optional[sm.TimelinesProject] = None
        self._current_timeline: Optional[sm.Timeline] = None

    def _open_project(self):
        from PyQt5.QtWidgets import QFileDialog
        project_dir = QFileDialog.getExistingDirectory(self._main_window, options=QFileDialog.ShowDirsOnly)

        self._project = sm.TimelinesProject.load_project(project_dir)
        self.set_current_timeline(None)

    def set_current_timeline(self, timeline_id):
        self._current_timeline = self._project.get_timeline(timeline_id)
        ui = self._ui

        ui.timelinePointTree.clear()
        items_to_add = []

        if self._current_timeline is not None:
            cur_point = self._current_timeline.head_point
        else:
            cur_point = self._project.root_point

        item = None
        while cur_point is not None:
            item = QtWidgets.QTreeWidgetItem(ui.timelinePointTree, item)
            item.setText(0, f"P {cur_point.tick}")

            child = None
            child_items_to_add = []
            for d in cur_point.derivative_timelines:
                child = QtWidgets.QTreeWidgetItem(item, child)
                child.setText(0, f"T {d.timeline_id}")
                child_items_to_add.append(child)
            item.addChildren(child_items_to_add)

            items_to_add.append(item)
            cur_point = cur_point.next_point

        ui.timelinePointTree.addTopLevelItems(items_to_add)

    def run(self):
        self._main_window.show()
        return self._app.exec()


if __name__ == "__main__":
    import sys
    app = App(sys.argv)
    app.run()
