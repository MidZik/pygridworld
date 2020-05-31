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

        self._app.aboutToQuit.connect(self._on_application_quitting)

        ui.actionOpen_Project.triggered.connect(self._open_project)

        # Navigation
        ui.timelineTree.itemSelectionChanged.connect(self._on_timeline_tree_selected_item_changed)
        ui.timelinePointList.itemSelectionChanged.connect(self._on_timeline_point_list_selected_item_changed)

        # Simulation Tab
        ui.startSimProcessButton.clicked.connect(self._start_sim_process_for_current_timeline)
        ui.killSimProcessButton.clicked.connect(self._kill_sim_process_for_current_timeline)

        ui.startSimButton.clicked.connect(self._start_selected_simulation)
        ui.stopSimButton.clicked.connect(self._stop_selected_simulation)
        ui.startEditSimButton.clicked.connect(self._start_editing_selected_sim)
        ui.commitEditsSimButton.clicked.connect(self._commit_edits_to_selected_sim)
        ui.discardEditsSimButton.clicked.connect(self._discard_edits_to_selected_sim)

        ui.createEntityButton.clicked.connect(self._create_entity_on_selected_sim)
        ui.destroyEntityButton.clicked.connect(self._destroy_selected_entity)
        ui.entityList.itemSelectionChanged.connect(self._on_selected_entity_changed)

        assign_component_menu = QtWidgets.QMenu(ui.assignComponentButton)
        ui.assignComponentButton.setMenu(assign_component_menu)
        assign_component_menu.triggered.connect(self._on_assign_component_triggered)
        ui.removeComponentButton.clicked.connect(self._remove_selected_component)
        ui.entityComponentList.itemSelectionChanged.connect(self._on_selected_component_changed)

        ui.revertComStateButton.clicked.connect(self._revert_selected_com_state)
        ui.saveComStateButton.clicked.connect(self._save_selected_com_state)

        self._project: Optional[sm.TimelinesProject] = None

        self._simulations = {}

        self._thread_pool = QtCore.QThreadPool()

        # Refresh selection states
        # TODO: A better way to ensure all ui elements are in the proper state?
        self._on_timeline_tree_selected_item_changed()

    def get_selected_timeline(self) -> Optional[sm.Timeline]:
        items = self._ui.timelineTree.selectedItems()

        if items:
            item = items[0]
        else:
            item = None

        return None if item is None else item.data(0, App._TimelineRole)

    def get_selected_timeline_simulation(self) -> Optional[sm.TimelineSimulation]:
        timeline = self.get_selected_timeline()
        if timeline is None:
            return None
        else:
            return self._simulations.get(timeline.timeline_id, None)

    def get_selected_point(self) -> Optional[sm.TimelinePoint]:
        items = self._ui.timelinePointList.selectedItems()

        if items:
            item = items[0]
        else:
            item = None

        return None if item is None else item.data(App._PointRole)

    def get_selected_eid(self):
        items = self._ui.entityList.selectedItems()

        if len(items) != 1:
            return None
        else:
            item = items[0]

        return int(item.text())

    def get_selected_component_name(self) -> Optional[str]:
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
        return self.get_selected_timeline_simulation(), self.get_selected_eid(), self.get_selected_component_name()

    def _on_application_quitting(self):
        for sim in self._simulations.values():
            sim.stop_process()

    def _open_project(self):
        from PySide2.QtWidgets import QFileDialog
        project_dir = QFileDialog.getExistingDirectory(self._main_window, options=QFileDialog.ShowDirsOnly)

        self._project = sm.TimelinesProject.load_project(project_dir)

        ui = self._ui

        ui.timelineTree.clear()

        def make_timeline_item(timeline, derived_from_point, parent_item, preceding_item):
            result_item = QtWidgets.QTreeWidgetItem(parent_item, preceding_item)
            result_item.setText(0, f"[{derived_from_point.tick}] {timeline.timeline_id}")
            result_item.setData(0, App._TimelineRole, timeline)
            return result_item

        class ProcessingFrame:
            def __init__(self, parent_ui_item, cur_point, next_derived_timeline_index):
                self.parent_ui_item = parent_ui_item
                self.cur_point: sm.TimelinePoint = cur_point
                self.next_derived_timeline_index = next_derived_timeline_index

        # Stack that tracks tree traversal.
        processing_stack = [ProcessingFrame(ui.timelineTree, self._project.root_point, 0)]

        last_added_item = None
        while len(processing_stack) > 0:
            cur_frame = processing_stack[-1]

            if cur_frame.next_derived_timeline_index < len(cur_frame.cur_point.derivative_timelines):
                # make the UI item for this derived timeline index
                timeline = cur_frame.cur_point.derivative_timelines[cur_frame.next_derived_timeline_index]
                last_added_item = make_timeline_item(timeline, cur_frame.cur_point, cur_frame.parent_ui_item, last_added_item)
                cur_frame.next_derived_timeline_index += 1

                # process this timeline next, starting at the head point
                processing_stack.append(ProcessingFrame(last_added_item, timeline.head_point, 0))
            else:
                # All timelines at this point have been processed, fast forward to the next point with timelines
                cur_frame.next_derived_timeline_index = 0
                cur_frame.cur_point = cur_frame.cur_point.next_point
                while cur_frame.cur_point is not None:
                    if cur_frame.cur_point.derivative_timelines:
                        break
                    cur_frame.cur_point = cur_frame.cur_point.next_point

                if cur_frame.cur_point is None:
                    # No more points with derivative timelines have been found on this timeline,
                    # so we can stop processing it.
                    # Restore last added item to the previous frame as we exit
                    processing_stack.pop()
                    last_added_item = cur_frame.parent_ui_item

        # TODO: Temp?
        self._on_timeline_tree_selected_item_changed()

    def _on_timeline_tree_selected_item_changed(self):
        ui = self._ui

        ui.timelinePointList.clear()

        timeline = self.get_selected_timeline()

        if timeline is not None:
            cur_point = timeline.head_point
            while cur_point is not None:
                item = QtWidgets.QListWidgetItem(f"{cur_point.tick}")
                item.setData(App._PointRole, cur_point)
                ui.timelinePointList.addItem(item)
                cur_point = cur_point.next_point

        self._refresh_simulation_tab()

    def _refresh_simulation_tab(self):
        self._refresh_simulation_process_buttons()
        self._refresh_simulation_start_stop_buttons()
        self._refresh_simulation_edit_mode_buttons()
        self._refresh_simulation_edit_buttons()
        self._refresh_simulation_entity_list()

    def _refresh_simulation_process_buttons(self):
        ui = self._ui

        timeline = self.get_selected_timeline()
        simulation = self.get_selected_timeline_simulation()

        ui.startSimProcessButton.setEnabled(False)
        ui.killSimProcessButton.setEnabled(False)

        if timeline is not None:
            ui.startSimProcessButton.setEnabled(simulation is None)
            ui.killSimProcessButton.setEnabled(simulation is not None)

    def _refresh_simulation_start_stop_buttons(self):
        ui = self._ui

        simulation = self.get_selected_timeline_simulation()

        ui.startSimButton.setEnabled(False)
        ui.stopSimButton.setEnabled(False)

        if simulation is not None and not simulation.is_editing():
            is_running = simulation.is_running()
            ui.startSimButton.setEnabled(not is_running)
            ui.stopSimButton.setEnabled(is_running)

    def _refresh_simulation_edit_mode_buttons(self):
        ui = self._ui

        simulation = self.get_selected_timeline_simulation()

        ui.startEditSimButton.setEnabled(False)
        ui.commitEditsSimButton.setEnabled(False)
        ui.discardEditsSimButton.setEnabled(False)

        if simulation is not None:
            is_editing = simulation.is_editing()
            ui.startEditSimButton.setEnabled(simulation.can_start_editing())
            ui.commitEditsSimButton.setEnabled(is_editing)
            ui.discardEditsSimButton.setEnabled(is_editing)

    def _refresh_simulation_edit_buttons(self):
        ui = self._ui

        sim, eid, com = self.get_all_sim_tab_selections()

        ui.createEntityButton.setEnabled(False)
        ui.destroyEntityButton.setEnabled(False)
        ui.assignComponentButton.setEnabled(False)
        ui.removeComponentButton.setEnabled(False)
        ui.revertComStateButton.setEnabled(False)
        ui.saveComStateButton.setEnabled(False)

        if sim is not None and sim.is_editing():
            ui.createEntityButton.setEnabled(True)

            if eid is not None:
                ui.destroyEntityButton.setEnabled(True)
                ui.assignComponentButton.setEnabled(True)

                if com is not None:
                    ui.removeComponentButton.setEnabled(True)

                    com_state_json = sim.get_component_json(eid, com)
                    com_state = json.loads(com_state_json)

                    if com_state is not None:
                        ui.revertComStateButton.setEnabled(True)
                        ui.saveComStateButton.setEnabled(True)

    def _refresh_simulation_entity_list(self):
        ui = self._ui

        sim = self.get_selected_timeline_simulation()

        ui.entityList.clear()

        if sim is not None:
            entities = sim.get_all_entities()
            for eid in entities:
                ui.entityList.addItem(str(eid))

    def _on_timeline_point_list_selected_item_changed(self):
        point = self.get_selected_point()

        if point is None:
            self._ui.stateJsonTextEdit.setPlainText("")
            return

        def update_text(text):
            if id(self.get_selected_point()) == id(point):
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
        else:
            raise RuntimeWarning("Selected point item with no attached data.")

    def _start_sim_process_for_current_timeline(self):
        timeline = self.get_selected_timeline()
        point = self.get_selected_point()
        self.start_simulation_process(timeline.timeline_id, point)

    def _kill_sim_process_for_current_timeline(self):
        sim = self.get_selected_timeline_simulation()

        if sim is not None:
            sim.stop_process()
            del self._simulations[sim.timeline.timeline_id]
            self._refresh_simulation_tab()

    def _create_entity_on_selected_sim(self):
        sim = self.get_selected_timeline_simulation()
        if sim is not None:
            sim.create_entity()

        # TODO: temp
        self._refresh_simulation_entity_list()

    def _destroy_selected_entity(self):
        sim = self.get_selected_timeline_simulation()
        eid = self.get_selected_eid()
        if sim is not None and eid is not None:
            sim.destroy_entity(eid)

        # TODO: temp
        self._refresh_simulation_entity_list()

    def start_simulation_process(self, timeline_id, point=None):
        if timeline_id in self._simulations:
            return

        timeline = self._project.get_timeline(timeline_id)
        if timeline is None:
            raise RuntimeError('No timeline found with given ID.')

        if point is not None and point.timeline is not timeline:
            raise RuntimeError('Starting simulation process at invalid point.')

        working_dir = timeline.get_dir() / 'working'
        new_sim = sm.TimelineSimulation(timeline, working_dir)
        new_sim.start_process()

        if point is not None:
            new_sim.move_to_point(point)

        self._simulations[timeline_id] = new_sim
        self._refresh_simulation_tab()

    def _on_selected_entity_changed(self):
        ui = self._ui

        ui.entityComponentList.clear()
        assign_components_button_menu = ui.assignComponentButton.menu()
        assign_components_button_menu.clear()
        ui.destroyEntityButton.setEnabled(False)
        ui.assignComponentButton.setEnabled(False)

        selected_sim = self.get_selected_timeline_simulation()
        selected_eid = self.get_selected_eid()

        if selected_sim is not None and selected_eid is not None:
            component_names = selected_sim.get_component_names()
            entity_component_names = selected_sim.get_entity_component_names(selected_eid)
            missing_component_names = [c for c in component_names if c not in entity_component_names]
            for c in missing_component_names:
                assign_components_button_menu.addAction(c)
            for c in entity_component_names:
                ui.entityComponentList.addItem(c)

            ui.destroyEntityButton.setEnabled(True)
            ui.assignComponentButton.setEnabled(True)

    def _on_assign_component_triggered(self, action):
        ui = self._ui
        selected_simulation = self.get_selected_timeline_simulation()
        selected_eid = self.get_selected_eid()
        if selected_simulation is not None and selected_eid is not None:
            selected_simulation.assign_component(selected_eid, action.text())

            # TODO: temp
            self._on_selected_entity_changed()

    def _remove_selected_component(self):
        selections = self.get_all_sim_tab_selections()
        if all(s is not None for s in selections):
            sim, eid, com = selections
            sim.remove_component(eid, com)

            # TODO: temp
            self._on_selected_entity_changed()

    def _on_selected_component_changed(self):
        ui = self._ui
        ui.comStateTextEdit.clear()

        ui.removeComponentButton.setEnabled(False)
        ui.revertComStateButton.setEnabled(False)
        ui.saveComStateButton.setEnabled(False)

        selected_sim = self.get_selected_timeline_simulation()
        selected_eid = self.get_selected_eid()
        selected_com = self.get_selected_component_name()

        if selected_sim is not None and selected_eid is not None and selected_com is not None:
            com_state_json = selected_sim.get_component_json(selected_eid, selected_com)
            com_state = json.loads(com_state_json)
            com_state_json = json.dumps(com_state, indent=2)  # pretty print
            ui.comStateTextEdit.setPlainText(com_state_json)

            ui.removeComponentButton.setEnabled(True)

            if com_state is not None:
                ui.revertComStateButton.setEnabled(True)
                ui.saveComStateButton.setEnabled(True)

    def _start_selected_simulation(self):
        selected_sim = self.get_selected_timeline_simulation()

        if selected_sim is not None:
            selected_sim.start_simulation()

    def _stop_selected_simulation(self):
        selected_sim = self.get_selected_timeline_simulation()

        if selected_sim is not None:
            selected_sim.stop_simulation()

    def _start_editing_selected_sim(self):
        selected_sim = self.get_selected_timeline_simulation()

        if selected_sim is not None and selected_sim.can_start_editing():
            selected_sim.start_editing()

        self._refresh_simulation_tab()

    def _commit_edits_to_selected_sim(self):
        selected_sim = self.get_selected_timeline_simulation()

        if selected_sim is not None and selected_sim.is_editing():
            selected_sim.commit_edits()

        self._refresh_simulation_tab()

    def _discard_edits_to_selected_sim(self):
        selected_sim = self.get_selected_timeline_simulation()

        if selected_sim is not None and selected_sim.is_editing():
            selected_sim.discard_edits()

        self._refresh_simulation_tab()

    def _revert_selected_com_state(self):
        # act as if the selected com was just re-selected
        self._on_selected_component_changed()

    def _save_selected_com_state(self):
        sim, eid, com = self.get_all_sim_tab_selections()

        if sim is not None and eid is not None and com is not None:
            com_state_json = self._ui.comStateTextEdit.toPlainText()
            sim.replace_component(eid, com, com_state_json)

    def run(self):
        self._main_window.show()
        return self._app.exec_()


if __name__ == "__main__":
    import sys
    app = App(sys.argv)
    app.run()
