import SimulationManager as sm
import window
from typing import Optional
from PyQt5 import QtCore, QtGui, QtWidgets
from pathlib import Path


class _TaskRunner(QtCore.QRunnable):
    def __init__(self, task):
        super().__init__()
        self._task = task

    @QtCore.pyqtSlot()
    def run(self) -> None:
        self._task.do_work()


class _Task(QtCore.QObject):
    def do_work(self):
        pass

    def runner(self):
        return _TaskRunner(self)


class _ReadFileTask(_Task):
    read_done = QtCore.pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = Path(file_path).resolve()

    def do_work(self):
        with self.file_path.open('r') as f:
            text = f.read()
            self.read_done.emit(text)


class App:
    _PointRole = QtCore.Qt.UserRole + 0
    _TimelineRole = QtCore.Qt.UserRole + 1

    def __init__(self, argv):
        self._app = QtWidgets.QApplication(argv)
        self._main_window = QtWidgets.QMainWindow()
        ui = window.Ui_MainWindow()
        ui.setupUi(self._main_window)
        self._ui = ui

        ui.actionOpen_Project.triggered.connect(self._open_project)

        ui.timelinePointTree.currentItemChanged.connect(self._on_timeline_point_tree_current_item_changed)
        ui.timelinePointTree.itemActivated.connect(self._on_timeline_point_tree_item_activated)

        self._project: Optional[sm.TimelinesProject] = None
        self._current_timeline: Optional[sm.Timeline] = None

        self._thread_pool = QtCore.QThreadPool()

    def _open_project(self):
        from PyQt5.QtWidgets import QFileDialog
        project_dir = QFileDialog.getExistingDirectory(self._main_window, options=QFileDialog.ShowDirsOnly)

        self._project = sm.TimelinesProject.load_project(project_dir)
        self.set_current_timeline(None)

    def _on_timeline_point_tree_current_item_changed(self, current, previous):
        if current is None:
            self._ui.stateJsonTextEdit.setPlainText("")
            return

        point = current.data(0, App._PointRole)
        timeline = current.data(0, App._TimelineRole)

        def update_text(text):
            if self._ui.timelinePointTree.currentItem() == current:
                self._ui.stateJsonTextEdit.setPlainText(text)

        if point is not None:
            point_file_path = point.get_file_path()
            if point_file_path is not None:
                task = _ReadFileTask(point_file_path)
                self._ui.stateJsonTextEdit.setPlainText(f"loading point {point}")
                task.read_done.connect(update_text)
                self._thread_pool.start(task.runner())
            else:
                self._ui.stateJsonTextEdit.setPlainText(f"Selected point has no data.")
        elif timeline is not None:
            self._ui.stateJsonTextEdit.setPlainText(f"timeline {timeline}")
        else:
            raise RuntimeWarning("Selected timeline tree item with no attached data.")

    def _on_timeline_point_tree_item_activated(self, item, column):
        timeline = item.data(0, App._TimelineRole)
        if timeline is not None:
            self.set_current_timeline(timeline.timeline_id)

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
            item.setData(0, App._PointRole, cur_point)

            child = None
            child_items_to_add = []
            for d in cur_point.derivative_timelines:
                child = QtWidgets.QTreeWidgetItem(item, child)
                child.setText(0, f"T {d.timeline_id}")
                child.setData(0, App._TimelineRole, d)
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
