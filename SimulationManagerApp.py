import SimulationManager as sm
import window
from typing import Optional
from PySide2 import QtCore, QtGui, QtWidgets
from pathlib import Path
import json


class _TaskRunner(QtCore.QRunnable):
    def __init__(self, task):
        super().__init__()
        self._task = task

    @QtCore.Slot()
    def run(self) -> None:
        self._task.do_work()


class _Task(QtCore.QObject):
    def do_work(self):
        pass

    def runner(self):
        return _TaskRunner(self)


class _ReadFileTask(_Task):
    read_done = QtCore.Signal(str)

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
        self._app.setQuitOnLastWindowClosed(True)
        self._main_window = QtWidgets.QMainWindow()
        ui = window.Ui_MainWindow()
        ui.setupUi(self._main_window)
        self._ui = ui

        ui.actionOpen_Project.triggered.connect(self._open_project)

        # Timelines tab
        ui.timelinePointTree.currentItemChanged.connect(self._on_timeline_point_tree_current_item_changed)
        ui.timelinePointTree.itemActivated.connect(self._on_timeline_point_tree_item_activated)
        ui.start_sim_process_button.pressed.connect(self._start_selected_sim_process)

        # Simulations tab
        ui.simulationList.itemSelectionChanged.connect(self._on_selected_simulation_changed)
        ui.createEntityButton.pressed.connect(self._create_entity_on_selected_sim)
        ui.destroyEntityButton.pressed.connect(self._destroy_selected_entity)
        ui.entityList.itemSelectionChanged.connect(self._on_selected_entity_changed)
        assign_component_menu = QtWidgets.QMenu(ui.assignComponentButton)
        ui.assignComponentButton.setMenu(assign_component_menu)
        assign_component_menu.triggered.connect(self._on_assign_component_triggered)
        ui.removeComponentButton.pressed.connect(self._remove_selected_component)
        ui.entityComponentList.itemSelectionChanged.connect(self._on_selected_component_changed)

        self._project: Optional[sm.TimelinesProject] = None
        self._current_timeline: Optional[sm.Timeline] = None

        self._simulations = {}

        self._thread_pool = QtCore.QThreadPool()

    def get_selected_simulation(self):
        items = self._ui.simulationList.selectedItems()

        if len(items) != 1:
            return None
        else:
            item = items[0]

        simulation_id = int(self._ui.simulationList.currentItem().text())
        return self._simulations[simulation_id]

    def get_selected_eid(self):
        items = self._ui.entityList.selectedItems()

        if len(items) != 1:
            return None
        else:
            item = items[0]

        return int(item.text())

    def get_selected_component_name(self):
        items = self._ui.entityComponentList.selectedItems()

        if len(items) != 1:
            return None
        else:
            item = items[0]

        return item.text()

    def get_all_sim_tab_selections(self):
        """
        :return: (simulation, eid, component name)
        """
        return self.get_selected_simulation(), self.get_selected_eid(), self.get_selected_component_name()

    def _open_project(self):
        from PySide2.QtWidgets import QFileDialog
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
            if id(self._ui.timelinePointTree.currentItem()) == id(current):
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

    def _start_selected_sim_process(self):
        selected_item = self._ui.timelinePointTree.currentItem()
        point = selected_item.data(0, App._PointRole)
        timeline = selected_item.data(0, App._TimelineRole)
        timeline = point.timeline if point is not None else timeline

        self.start_simulation(timeline.timeline_id)

    def _create_entity_on_selected_sim(self):
        sim = self.get_selected_simulation()
        if sim is not None:
            sim.simulation_process.create_entity()

        # TODO: temp
        self._on_selected_simulation_changed()

    def _destroy_selected_entity(self):
        sim = self.get_selected_simulation()
        eid = self.get_selected_eid()
        if sim is not None and eid is not None:
            sim.simulation_process.destroy_entity(eid)

        # TODO: temp
        self._on_selected_simulation_changed()

    def start_simulation(self, timeline_id):
        if timeline_id in self._simulations:
            return

        timeline = self._project.get_timeline(timeline_id)

        if timeline is None:
            raise RuntimeError('No timeline found with given ID.')

        working_dir = timeline.get_dir() / 'working'
        new_sim = sm.TimelineSimulation(timeline, working_dir)
        new_sim.start_process()

        self._simulations[timeline_id] = new_sim
        item = QtWidgets.QListWidgetItem(f"{timeline_id}")
        self._ui.simulationList.addItem(item)

    def _on_selected_simulation_changed(self):
        ui = self._ui

        ui.entityList.clear()

        selected_sim = self.get_selected_simulation()

        if selected_sim is not None:
            sim_process: sm.SimulationRunnerProcess = selected_sim.simulation_process

            entities = sim_process.get_all_entities()
            for eid in entities:
                ui.entityList.addItem(str(eid))

    def _on_selected_entity_changed(self):
        ui = self._ui

        ui.entityComponentList.clear()
        assign_components_button_menu = ui.assignComponentButton.menu()
        assign_components_button_menu.clear()

        selected_eid = self.get_selected_eid()

        if selected_eid is not None:
            sim_process: sm.SimulationRunnerProcess = self.get_selected_simulation().simulation_process

            component_names = sim_process.get_component_names()
            entity_component_names = sim_process.get_entity_component_names(selected_eid)
            missing_component_names = [c for c in component_names if c not in entity_component_names]
            for c in missing_component_names:
                assign_components_button_menu.addAction(c)
            for c in entity_component_names:
                ui.entityComponentList.addItem(c)

    def _on_assign_component_triggered(self, action):
        ui = self._ui
        selected_eid = self.get_selected_eid()
        selected_simulation = self.get_selected_simulation()
        if selected_eid is not None and selected_simulation is not None:
            sim_process: sm.SimulationRunnerProcess = selected_simulation.simulation_process
            sim_process.assign_component(selected_eid, action.text())

            # TODO: temp
            self._on_selected_entity_changed()

    def _remove_selected_component(self):
        selections = self.get_all_sim_tab_selections()
        if all(s is not None for s in selections):
            sim, eid, com = selections
            sim_process: sm.SimulationRunnerProcess = sim.simulation_process
            sim_process.remove_component(eid, com)

            # TODO: temp
            self._on_selected_entity_changed()

    def _on_selected_component_changed(self):
        ui = self._ui
        ui.comStateTextEdit.clear()

        selected_sim = self.get_selected_simulation()
        selected_eid = self.get_selected_eid()
        selected_com = self.get_selected_component_name()

        if selected_sim is not None and selected_eid is not None and selected_com is not None:
            com_state_json = selected_sim.simulation_process.get_component_json(selected_eid, selected_com)
            com_state_json = json.dumps(json.loads(com_state_json), indent=2)  # pretty print
            ui.comStateTextEdit.setPlainText(com_state_json)

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
        return self._app.exec_()


if __name__ == "__main__":
    import sys
    app = App(sys.argv)
    app.run()
