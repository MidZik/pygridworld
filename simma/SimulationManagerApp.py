"""
@author: Matt Idzik (MidZik)
"""
import SimulationManager as sm
from GUI import create_gui_process
import window
import command_prompt_dock_widget as cmd
from typing import Optional, Dict
from PySide2 import QtCore, QtWidgets, QtGui
from pathlib import Path
import json
from collections import deque
from weakref import WeakKeyDictionary
from ts_server import Server
from PySide2.QtWidgets import QFileDialog
import shlex


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


class SimCommandPromptValidator(QtGui.QValidator):
    def validate(self, input, pos):
        if input.strip() != "":
            # any string that isn't only whitespace is valid
            return SimCommandPromptValidator.Acceptable
        return SimCommandPromptValidator.Intermediate


class Simulation:
    def __init__(self,
                 parent: QtWidgets.QMainWindow,
                 timeline_node: sm.TimelineNode,
                 timeline_simulation: sm.TimelineSimulation):
        self.timeline_node = timeline_node
        self.timeline_simulation: sm.TimelineSimulation = timeline_simulation
        self.client = timeline_simulation.make_client()

        self.dock = QtWidgets.QDockWidget(parent)
        self.ui = cmd.Ui_commandPromptDock()
        self.ui.setupUi(self.dock)

        self.ui.cmdPromptInput.returnPressed.connect(self._command_prompt_return_pressed)
        self.ui.cmdPromptInput.setValidator(SimCommandPromptValidator(self.ui.cmdPromptInput))

        self.dock.setWindowTitle(f"Command Prompt [{self.timeline_node.timeline_id}]")
        self.dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        parent.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.dock)

        self.dock.show()

    def remove_dock(self):
        self.dock.deleteLater()

    def token(self):
        return self.client.token

    def _command_prompt_return_pressed(self):
        ui = self.ui

        args = shlex.split(ui.cmdPromptInput.text())

        err, output = self.client.run_command(args)
        ui.cmdPromptOutput.appendPlainText(f"CMD[{self.timeline_node.timeline_id}]> " + ui.cmdPromptInput.text())
        if err:
            ui.cmdPromptOutput.appendPlainText("--- ERROR: " + err)
        else:
            ui.cmdPromptOutput.appendPlainText("+++ OK")
        if output:
            ui.cmdPromptOutput.appendPlainText(output)

        ui.cmdPromptInput.setText("")


class App(QtCore.QObject):
    _PointRole = QtCore.Qt.UserRole + 0
    _TimelineTreeNodeRole = QtCore.Qt.UserRole + 1
    _SimIdentifierRole = QtCore.Qt.UserRole + 2
    _SimulationRegistration = QtCore.Qt.UserRole + 0

    _SimulationBinaryProvider = QtCore.Qt.UserRole + 1

    simulation_started = QtCore.Signal(object, object)
    simulation_stopped = QtCore.Signal(object, object)
    timeline_created = QtCore.Signal(object)
    timeline_deleted = QtCore.Signal(object)

    simulation_runner_updated = QtCore.Signal(int)

    def __init__(self, argv):
        super().__init__(None)

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
        ui.showVisualizerButton.clicked.connect(self._show_visualizer_for_current_timeline)
        ui.killSimProcessButton.clicked.connect(self._kill_sim_process_for_current_timeline)

        ui.startSimButton.clicked.connect(self._start_selected_simulation)
        ui.stopSimButton.clicked.connect(self._stop_selected_simulation)
        ui.startEditSimButton.clicked.connect(self._start_editing_selected_sim)
        ui.commitEditsSimButton.clicked.connect(self._commit_edits_to_selected_sim)
        ui.discardEditsSimButton.clicked.connect(self._discard_edits_to_selected_sim)

        # Entities Subtab
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

        # Singletons Subtab
        ui.singletonList.itemSelectionChanged.connect(self._on_selected_singleton_changed)

        ui.revertSingletonStateButton.clicked.connect(self._revert_selected_singleton_state)
        ui.saveSingletonStateButton.clicked.connect(self._save_selected_singleton_state)

        # Timeline Tab
        ui.createTimelineAtSelectionButton.clicked.connect(self._create_timeline_at_selection)
        ui.createSiblingTimelineButton.clicked.connect(self._create_sibling_timeline)
        ui.deleteSelectedTimelineButton.clicked.connect(self._delete_selected_timeline)
        ui.convertToSimComboBox.currentIndexChanged.connect(self._on_convert_to_sim_combo_box_changed)
        ui.convertToSimButton.clicked.connect(self._convert_to_selected_sim)
        ui.saveTimelineTagsButton.clicked.connect(self._save_selected_timeline_tags)
        ui.revertTimelineTagsButton.clicked.connect(self._revert_selected_timeline_tags)

        # Simulation Registry Tab
        ui.addSimSourceButton.clicked.connect(self._add_sim_source)
        ui.simSourceList.itemSelectionChanged.connect(self._on_selected_sim_source_changed)

        ui.registerSimFromSourceButton.clicked.connect(self._register_from_selected_sim_source)
        ui.removeSimSourceButton.clicked.connect(self._delete_selected_sim_source)

        ui.registeredSimList.itemSelectionChanged.connect(self._on_selected_registered_sim_changed)

        ui.saveRegisteredSimDescButton.clicked.connect(self._save_registered_sim_description)
        ui.discardRegisteredSimDescButton.clicked.connect(self._discard_registered_sim_description)
        ui.unregisterSimButton.clicked.connect(self._unregister_selected_sim_registration)

        # connect to own signals
        self.simulation_started.connect(self._on_project_simulation_started)
        self.simulation_stopped.connect(self._on_project_simulation_stopped)
        self.timeline_created.connect(self._on_timeline_created)
        self.timeline_deleted.connect(self._on_timeline_deleted)

        self.simulation_runner_updated.connect(self._on_simulation_runner_updated)

        self._project: Optional[sm.TimelinesProject] = None
        self._server = None

        self._simulations: Dict[Simulation] = {}
        self._visualizations = {}

        self._sim_command_prompts = {}

        self._timeline_tree_widget_map = WeakKeyDictionary()

        self._thread_pool = QtCore.QThreadPool()

        self._last_entity_selected = None
        self._last_component_selected = None

        # Refresh selection states
        # TODO: A better way to ensure all ui elements are in the proper state?
        self._on_timeline_tree_selected_item_changed()

    def get_selected_timeline_node(self) -> Optional[sm.TimelineNode]:
        items = self._ui.timelineTree.selectedItems()

        if items:
            return items[0].data(0, App._TimelineTreeNodeRole)
        else:
            return None

    def get_selected_timeline(self) -> Optional[sm.Timeline]:
        timeline_node = self.get_selected_timeline_node()
        if timeline_node is not None:
            return timeline_node.timeline
        else:
            return None

    def get_selected_running_timeline_simulation(self) -> Optional[Simulation]:
        timeline_node = self.get_selected_timeline_node()

        if timeline_node is None:
            return None
        else:
            sim = self._simulations.get(timeline_node.timeline_id, None)
            if sim is not None and sim.timeline_simulation.is_process_running():
                return sim
            else:
                return None

    def get_selected_point(self) -> Optional[sm.TimelinePoint]:
        items = self._ui.timelinePointList.selectedItems()

        if items:
            return items[0].data(App._PointRole)
        else:
            return None

    def get_selected_eid(self):
        items = self._ui.entityList.selectedItems()

        if len(items) != 1:
            return None
        else:
            return int(items[0].text())

    def get_selected_component_name(self) -> Optional[str]:
        items = self._ui.entityComponentList.selectedItems()

        if len(items) != 1:
            return None
        else:
            return items[0].text()

    def get_all_sim_tab_selections(self):
        """
        :return: (simulation, eid, component name)
        """
        return self.get_selected_running_timeline_simulation(), self.get_selected_eid(), self.get_selected_component_name()

    def get_selected_singleton_name(self) -> Optional[str]:
        items = self._ui.singletonList.selectedItems()

        if items:
            return items[0].text()
        else:
            return None

    def get_selected_simulation_source(self) -> Optional[sm.SimulationSource]:
        items = self._ui.simSourceList.selectedItems()

        if items:
            return sm.SimulationSource(items[0].data(App._SimIdentifierRole))
        else:
            return None

    def get_selected_simulation_registration(self):
        items = self._ui.registeredSimList.selectedItems()

        if items:
            return items[0].data(App._SimulationRegistration)
        else:
            return None

    def get_selected_simulation_registration_list_item(self):
        items = self._ui.registeredSimList.selectedItems()

        if items:
            return items[0]
        else:
            return None

    def get_sim_bin_provider_to_convert_to(self):
        return self._ui.convertToSimComboBox.currentData(App._SimulationBinaryProvider)

    def _on_application_quitting(self):
        sims_to_close = [sim for sim in self._simulations.values()]
        self._simulations.clear()
        for sim in sims_to_close:
            sim.timeline_simulation.stop_process()

    def _make_timeline_item(self, timeline_node: sm.TimelineNode):
        if timeline_node in self._timeline_tree_widget_map:
            raise ValueError('Timeline node already has an item associated with it.')

        previous_sibling = timeline_node.previous_sibling()
        if previous_sibling is not None:
            preceding_item = self._timeline_tree_widget_map[previous_sibling]
        else:
            preceding_item = None

        parent_item = self._timeline_tree_widget_map[timeline_node.parent_node]
        result_item = QtWidgets.QTreeWidgetItem(parent_item, preceding_item)
        result_item.setText(0, f"[{timeline_node.timeline.head()}] {timeline_node.timeline_id}")
        result_item.setData(0, App._TimelineTreeNodeRole, timeline_node)
        self._timeline_tree_widget_map[timeline_node] = result_item
        return result_item

    def _open_project(self):
        project_dir = QFileDialog.getExistingDirectory(self._main_window, options=QFileDialog.ShowDirsOnly)

        if not project_dir:
            return

        self._project = sm.TimelinesProject.load_project(project_dir)
        if self._server is not None:
            self._server.stop()
        self._server = Server(self._project)
        self._server.start()

        self._timeline_tree_widget_map = WeakKeyDictionary()
        self._timeline_tree_widget_map[self._project.root_node] = self._ui.timelineTree.invisibleRootItem()

        ui = self._ui

        ui.timelineTree.clear()

        # node_deque contains (node, node_ui) pairs that have a ui element already created,
        # and their children need ui nodes still created
        node_deque = deque()
        node_deque.append(self._project.root_node)

        while node_deque:
            cur_node = node_deque.pop()
            for child_node in cur_node.child_nodes:
                self._make_timeline_item(child_node)
                node_deque.append(child_node)

        # TODO: Temp?
        self._on_timeline_tree_selected_item_changed()
        self._refresh_sim_registry_tab()

        combo_box = self._ui.convertToSimComboBox
        combo_box.clear()
        for config in self._project.get_all_simulation_providers():
            self._add_timeline_simulation_provider_to_combo_box(config)
        self._refresh_convert_to_selected_sim_button()

        self._project.simulation_started.connect(self.simulation_started.emit)
        self._project.simulation_stopped.connect(self.simulation_stopped.emit)
        self._project.timeline_created.connect(self.timeline_created.emit)
        self._project.timeline_deleted.connect(self.timeline_deleted.emit)

    def _on_timeline_tree_selected_item_changed(self):
        ui = self._ui

        ui.timelinePointList.clear()

        timeline_node = self.get_selected_timeline_node()

        if timeline_node is not None:
            for point in timeline_node.points():
                item = QtWidgets.QListWidgetItem(f"{point.tick}")
                item.setData(App._PointRole, point)
                ui.timelinePointList.addItem(item)

        sim_info = self.get_selected_running_timeline_simulation()
        if sim_info is not None:
            sim_info.dock.raise_()

        self._refresh_convert_to_selected_sim_button()
        self._refresh_current_timeline_sim_label()
        self._refresh_selected_timeline_tags()
        self._refresh_simulation_tab()

    def _refresh_simulation_tab(self):
        self._refresh_simulation_process_buttons()
        self._refresh_simulation_start_stop_buttons()
        self._refresh_simulation_edit_mode_buttons()
        self._refresh_simulation_edit_buttons()
        self._refresh_simulation_entity_list()
        self._refresh_simulation_singletons_list()

    def _refresh_simulation_process_buttons(self):
        ui = self._ui

        timeline = self.get_selected_timeline()
        simulation = self.get_selected_running_timeline_simulation()

        ui.startSimProcessButton.setEnabled(False)
        ui.killSimProcessButton.setEnabled(False)

        if timeline is not None:
            ui.startSimProcessButton.setEnabled(simulation is None)
            ui.killSimProcessButton.setEnabled(simulation is not None)

    def _refresh_simulation_start_stop_buttons(self):
        ui = self._ui

        sim = self.get_selected_running_timeline_simulation()

        ui.startSimButton.setEnabled(False)
        ui.stopSimButton.setEnabled(False)

        if sim is not None and not sim.client.is_editing():
            is_running = sim.client.is_running()
            ui.startSimButton.setEnabled(not is_running)
            ui.stopSimButton.setEnabled(is_running)

    def _refresh_simulation_edit_mode_buttons(self):
        ui = self._ui

        sim = self.get_selected_running_timeline_simulation()

        ui.startEditSimButton.setEnabled(False)
        ui.commitEditsSimButton.setEnabled(False)
        ui.discardEditsSimButton.setEnabled(False)

        if sim is not None:
            is_self_editing = sim.client.is_editing(True)
            ui.startEditSimButton.setEnabled(sim.timeline_simulation.can_start_editing())
            ui.commitEditsSimButton.setEnabled(is_self_editing)
            ui.discardEditsSimButton.setEnabled(is_self_editing)

    def _refresh_simulation_edit_buttons(self):
        ui = self._ui

        sim, eid, com = self.get_all_sim_tab_selections()
        singleton = self.get_selected_singleton_name()

        ui.createEntityButton.setEnabled(False)
        ui.destroyEntityButton.setEnabled(False)
        ui.assignComponentButton.setEnabled(False)
        ui.removeComponentButton.setEnabled(False)
        ui.revertComStateButton.setEnabled(False)
        ui.saveComStateButton.setEnabled(False)
        ui.revertSingletonStateButton.setEnabled(False)
        ui.saveSingletonStateButton.setEnabled(False)

        if sim is not None and sim.client.is_editing(True):
            ui.createEntityButton.setEnabled(True)

            if eid is not None:
                ui.destroyEntityButton.setEnabled(True)
                ui.assignComponentButton.setEnabled(True)

                if com is not None:
                    ui.removeComponentButton.setEnabled(True)

                    com_state_json, _ = sim.client.get_component_json(eid, com)
                    com_state = json.loads(com_state_json)

                    if com_state is not None:
                        ui.revertComStateButton.setEnabled(True)
                        ui.saveComStateButton.setEnabled(True)

            if singleton is not None:
                ui.revertSingletonStateButton.setEnabled(True)
                ui.saveSingletonStateButton.setEnabled(True)

    def _refresh_simulation_entity_list(self):
        ui = self._ui

        sim = self.get_selected_running_timeline_simulation()

        ui.entityList.clear()

        if sim is not None:
            entities, _ = sim.client.get_all_entities()
            for eid in entities:
                ui.entityList.addItem(str(eid))
                if eid == self._last_entity_selected:
                    ui.entityList.setCurrentRow(ui.entityList.count() - 1)

    def _refresh_simulation_singletons_list(self):
        ui = self._ui

        sim = self.get_selected_running_timeline_simulation()

        ui.singletonList.clear()

        if sim is not None:
            singletons = sim.client.get_singleton_names()
            for singleton in singletons:
                ui.singletonList.addItem(singleton)

    def _on_timeline_point_list_selected_item_changed(self):
        point = self.get_selected_point()

        if point is None:
            self._ui.pointStateJsonTextEdit.setPlainText("")
            return

        def update_text(text):
            if self.get_selected_point() == point:
                self._ui.pointStateJsonTextEdit.setPlainText(text)

        point_file_path = point.point_file_path()
        if point_file_path is not None:
            # TODO: state is no longer json, so either the binary should be converted or this should
            # be removed entirely from the UI

            # task = _ReadFileTask(point_file_path)
            # self._ui.pointStateJsonTextEdit.setPlainText(f"loading point {point}")
            # task.read_done.connect(update_text)
            # self._thread_pool.start(task.runner())

            self._ui.pointStateJsonTextEdit.setPlainText(f"Displaying point json is not currently implemented.")
        else:
            self._ui.pointStateJsonTextEdit.setPlainText(f"Selected point has no data.")

    def _start_sim_process_for_current_timeline(self):
        start_spec = self.get_selected_point()
        if start_spec is None:
            start_spec = self.get_selected_timeline_node()

        self._project.get_or_start_simulation(start_spec)

    def _show_visualizer_for_current_timeline(self):
        sim = self.get_selected_running_timeline_simulation()
        if sim is not None:
            timeline_node = self.get_selected_timeline_node()
            timeline_id = timeline_node.timeline_id
            if timeline_id not in self._visualizations or not self._visualizations[timeline_id].is_alive():
                address, token = sim.timeline_simulation.make_connection_parameters()
                new_visualization = create_gui_process(address, token)
                new_visualization.start()
                self._visualizations[timeline_node.timeline_id] = new_visualization

    def _kill_sim_process_for_current_timeline(self):
        timeline_node = self.get_selected_timeline_node()
        self._project.stop_simulation(timeline_node)

    def _create_entity_on_selected_sim(self):
        sim = self.get_selected_running_timeline_simulation()
        if sim is not None:
            sim.client.create_entity()

        # TODO: temp
        self._refresh_simulation_entity_list()

    def _destroy_selected_entity(self):
        sim = self.get_selected_running_timeline_simulation()
        eid = self.get_selected_eid()
        if sim is not None and eid is not None:
            sim.client.destroy_entity(eid)

        # TODO: temp
        self._refresh_simulation_entity_list()

    @QtCore.Slot()
    def _on_project_simulation_started(self, timeline_sim, timeline_node):
        timeline_id = timeline_node.timeline_id

        timeline_sim.runner_updated.connect(self.simulation_runner_updated.emit, timeline_node.timeline_id)

        new_sim = Simulation(self._main_window, timeline_node, timeline_sim)

        if self._simulations:
            already_existing_sim = next(iter(self._simulations.values()))
            self._main_window.tabifyDockWidget(already_existing_sim.dock, new_sim.dock)

        self._simulations[timeline_id] = new_sim

        self._on_simulation_runner_updated(timeline_node.timeline_id)
        self._refresh_convert_to_selected_sim_button()

    @QtCore.Slot()
    def _on_project_simulation_stopped(self, timeline_sim, timeline_node):
        sim = self._simulations.get(timeline_node.timeline_id, None)

        if sim is not None:
            del self._simulations[timeline_node.timeline_id]
            sim.remove_dock()
            self._refresh_convert_to_selected_sim_button()

    @QtCore.Slot()
    def _on_simulation_runner_updated(self, timeline_id):
        selected_timeline_node = self.get_selected_timeline_node()
        if selected_timeline_node is not None and selected_timeline_node.timeline_id == timeline_id:
            self._refresh_simulation_tab()

    def _on_selected_entity_changed(self):
        ui = self._ui

        self._refresh_simulation_edit_buttons()

        ui.entityComponentList.clear()
        assign_components_button_menu = ui.assignComponentButton.menu()
        assign_components_button_menu.clear()

        selected_sim = self.get_selected_running_timeline_simulation()
        selected_eid = self.get_selected_eid()

        if selected_sim is not None and selected_eid is not None:
            self._last_entity_selected = selected_eid
            component_names = selected_sim.client.get_component_names()
            entity_component_names, _ = selected_sim.client.get_entity_component_names(selected_eid)
            missing_component_names = [c for c in component_names if c not in entity_component_names]
            for c in missing_component_names:
                assign_components_button_menu.addAction(c)
            for c in entity_component_names:
                ui.entityComponentList.addItem(c)
                if c == self._last_component_selected:
                    ui.entityComponentList.setCurrentRow(ui.entityComponentList.count() - 1)

    def _on_assign_component_triggered(self, action):
        selected_simulation = self.get_selected_running_timeline_simulation()
        selected_eid = self.get_selected_eid()
        if selected_simulation is not None and selected_eid is not None:
            selected_simulation.client.assign_component(selected_eid, action.text())

            # TODO: temp
            self._on_selected_entity_changed()

    def _remove_selected_component(self):
        selections = self.get_all_sim_tab_selections()
        if all(s is not None for s in selections):
            sim, eid, com = selections
            sim.client.remove_component(eid, com)

            # TODO: temp
            self._on_selected_entity_changed()

    def _on_selected_component_changed(self):
        ui = self._ui

        self._refresh_simulation_edit_buttons()

        ui.comStateTextEdit.clear()

        selected_sim = self.get_selected_running_timeline_simulation()
        selected_eid = self.get_selected_eid()
        selected_com = self.get_selected_component_name()

        if selected_sim is not None and selected_eid is not None and selected_com is not None:
            self._last_component_selected = selected_com
            com_state_json, _ = selected_sim.client.get_component_json(selected_eid, selected_com)
            com_state = json.loads(com_state_json)
            com_state_json = json.dumps(com_state, indent=2)  # pretty print
            ui.comStateTextEdit.setPlainText(com_state_json)

    def _start_selected_simulation(self):
        selected_sim = self.get_selected_running_timeline_simulation()

        if selected_sim is not None:
            selected_sim.client.start_simulation()

    def _stop_selected_simulation(self):
        selected_sim = self.get_selected_running_timeline_simulation()

        if selected_sim is not None:
            selected_sim.client.stop_simulation()

    def _start_editing_selected_sim(self):
        selected_sim = self.get_selected_running_timeline_simulation()

        if selected_sim is not None and selected_sim.timeline_simulation.can_start_editing():
            selected_sim.timeline_simulation.start_editing(selected_sim.token())

    def _commit_edits_to_selected_sim(self):
        selected_sim = self.get_selected_running_timeline_simulation()

        if selected_sim is not None and selected_sim.client.is_editing(True):
            selected_sim.timeline_simulation.commit_edits(selected_sim.token())
            selected_sim.timeline_simulation.end_editing(selected_sim.token())

    def _discard_edits_to_selected_sim(self):
        selected_sim = self.get_selected_running_timeline_simulation()

        if selected_sim is not None and selected_sim.client.is_editing(True):
            selected_sim.timeline_simulation.discard_edits(selected_sim.token())
            selected_sim.timeline_simulation.end_editing(selected_sim.token())

    def _revert_selected_com_state(self):
        self._on_selected_component_changed()

    def _save_selected_com_state(self):
        sim, eid, com = self.get_all_sim_tab_selections()

        if sim is not None and eid is not None and com is not None:
            com_state_json = self._ui.comStateTextEdit.toPlainText()
            sim.client.replace_component(eid, com, com_state_json)

    def _create_timeline_at_selection(self):
        timeline_node = self.get_selected_timeline_node()
        point = self.get_selected_point()

        if point is None and timeline_node is not None:
            point = timeline_node.head_point()

        self._project.create_timeline(point)

    def _create_sibling_timeline(self):
        timeline_node = self.get_selected_timeline_node()

        if timeline_node is not None:
            self._project.clone_timeline(timeline_node)

    @QtCore.Slot()
    def _on_timeline_created(self, created_timeline_node):
        self._make_timeline_item(created_timeline_node)

    def _delete_selected_timeline(self):
        from PySide2.QtWidgets import QMessageBox
        timeline_node = self.get_selected_timeline_node()

        if timeline_node is not None:
            number_of_nodes = 0

            def count(_):
                nonlocal number_of_nodes
                number_of_nodes += 1

            sm.TimelineNode.traverse(timeline_node, count)

            result = QMessageBox(
                QMessageBox.Warning,
                "Confirm Timeline Deletion",
                f"Selected timeline and all child timelines will be deleted ({number_of_nodes} total). Are you sure?",
                QMessageBox.Yes | QMessageBox.No
            ).exec_()

            if result == QMessageBox.Yes:
                self._project.delete_timeline(timeline_node)

    @QtCore.Slot()
    def _on_timeline_deleted(self, deleted_timeline_node):
        parent_node = deleted_timeline_node.parent_node
        widget: QtWidgets.QTreeWidgetItem = self._timeline_tree_widget_map[deleted_timeline_node]
        parent_widget = self._timeline_tree_widget_map[parent_node]
        parent_widget.removeChild(widget)

    def _on_selected_singleton_changed(self):
        ui = self._ui

        self._refresh_simulation_edit_buttons()

        ui.singletonStateTextEdit.clear()

        singleton = self.get_selected_singleton_name()
        sim = self.get_selected_running_timeline_simulation()

        if sim is not None and singleton is not None:
            singleton_state_json, _ = sim.client.get_singleton_json(singleton)
            singleton_state = json.loads(singleton_state_json)
            singleton_state_json = json.dumps(singleton_state, indent=2)  # pretty print
            ui.singletonStateTextEdit.setPlainText(singleton_state_json)

    def _revert_selected_singleton_state(self):
        self._on_selected_singleton_changed()

    def _save_selected_singleton_state(self):
        sim = self.get_selected_running_timeline_simulation()
        singleton = self.get_selected_singleton_name()

        if sim is not None and singleton is not None:
            singleton_state_json = self._ui.singletonStateTextEdit.toPlainText()
            sim.client.set_singleton_json(singleton, singleton_state_json)

    def _refresh_sim_registry_tab(self):
        self._refresh_simulation_source_list()
        self._refresh_simulation_source_section()
        self._refresh_registered_sim_list()
        self._refresh_registered_sim_section()

    def _refresh_simulation_source_list(self):
        ui = self._ui
        ui.simSourceList.clear()
        for source in self._project.get_simulation_source_paths():
            source = sm.SimulationSource(source)
            item = QtWidgets.QListWidgetItem(f"{source.name}")
            item.setData(App._SimIdentifierRole, source.source_file_path)
            ui.simSourceList.addItem(item)

    def _refresh_simulation_source_section(self):
        ui = self._ui
        selected_source = self.get_selected_simulation_source()
        if selected_source:
            ui.simSourceFilePathLabel.setText(str(selected_source.source_file_path))
            ui.sourceFileContentsTextEdit.setPlainText(selected_source.get_json())
        else:
            ui.simSourceFilePathLabel.setText("")
            ui.sourceFileContentsTextEdit.setPlainText("")

    def _registered_sim_item_text(self, reg):
        return f"{reg.get_description_summary()} ({reg.uuid})"

    def _make_registered_sim_item(self, reg):
        item_text = self._registered_sim_item_text(reg)
        item = QtWidgets.QListWidgetItem(item_text)
        item.setData(App._SimulationRegistration, reg)
        return item

    def _refresh_registered_sim_list(self):
        ui = self._ui
        ui.registeredSimList.clear()
        for reg in self._project.get_registered_simulations():
            item = self._make_registered_sim_item(reg)
            ui.registeredSimList.addItem(item)

    def _refresh_registered_sim_section(self):
        ui = self._ui
        selected_reg = self.get_selected_simulation_registration()
        if selected_reg is not None:
            ui.registeredSimDescriptionTextEdit.setPlainText(selected_reg.get_description())
            ui.registeredSimMetadataTextEdit.setPlainText(selected_reg.get_metadata_json())
        else:
            ui.registeredSimDescriptionTextEdit.setPlainText("")
            ui.registeredSimMetadataTextEdit.setPlainText("")

    def _add_sim_source(self):
        source_file, _ = QFileDialog.getOpenFileName(self._main_window, filter="SM Source (*.smsource)")
        if not source_file:
            return

        self._project.add_simulation_source_path(source_file)
        source = sm.SimulationSource(source_file)
        item = QtWidgets.QListWidgetItem(f"{source.name}")
        item.setData(App._SimIdentifierRole, source.source_file_path)
        self._ui.simSourceList.addItem(item)

        self._add_timeline_simulation_provider_to_combo_box(source)

    def _on_selected_sim_source_changed(self):
        self._refresh_simulation_source_section()

    def _register_from_selected_sim_source(self):
        selected_source = self.get_selected_simulation_source()
        if selected_source:
            reg = self._project.register_simulation(selected_source)
            item = self._make_registered_sim_item(reg)
            self._ui.registeredSimList.addItem(item)

            self._add_timeline_simulation_provider_to_combo_box(reg)

    def _delete_selected_sim_source(self):
        selected_source = self.get_selected_simulation_source()
        if selected_source:
            self._project.remove_simulation_source_path(selected_source.source_file_path)
            self._refresh_simulation_source_list()
            self._refresh_simulation_source_section()

    def _on_selected_registered_sim_changed(self):
        self._refresh_registered_sim_section()

    def _save_registered_sim_description(self):
        selected_reg = self.get_selected_simulation_registration()
        selected_reg_list_item = self.get_selected_simulation_registration_list_item()
        if selected_reg is not None:
            selected_reg.set_description(self._ui.registeredSimDescriptionTextEdit.toPlainText())
            selected_reg_list_item.setText(self._registered_sim_item_text(selected_reg))
            index = self._ui.convertToSimComboBox.findData(selected_reg, App._SimulationBinaryProvider)
            self._ui.convertToSimComboBox.setItemText(index, str(selected_reg))

    def _discard_registered_sim_description(self):
        selected_reg = self.get_selected_simulation_registration()
        if selected_reg is not None:
            self._ui.registeredSimDescriptionTextEdit.setPlainText(selected_reg.get_description())

    def _unregister_selected_sim_registration(self):
        reg = self.get_selected_simulation_registration()
        if reg:
            self._project.unregister_simulation(reg.uuid)
            self._refresh_registered_sim_list()
            self._refresh_registered_sim_section()
            combo_box = self._ui.convertToSimComboBox
            index = combo_box.findData(str(reg))
            combo_box.removeItem(index)

    def _can_change_timeline_simulation_config(self, node):
        if node is None:
            return False

        has_multiple_points = len(node.timeline.tick_list) > 1
        has_child_nodes = len(node.child_nodes) > 0
        simulation_running = node.timeline_id in self._simulations
        return not (has_multiple_points or has_child_nodes or simulation_running)

    def _on_convert_to_sim_combo_box_changed(self, index):
        self._refresh_convert_to_selected_sim_button()

    def _add_timeline_simulation_provider_to_combo_box(self, simulation_provider):
        combo_box = self._ui.convertToSimComboBox
        if isinstance(simulation_provider, sm.SimulationRegistration):
            index = combo_box.count()
        else:
            index = 0

        combo_box.insertItem(index, str(simulation_provider), str(simulation_provider))
        combo_box.setItemData(index, simulation_provider, App._SimulationBinaryProvider)

    def _refresh_current_timeline_sim_label(self):
        label = self._ui.currentTimelineSimLabel
        selected_timeline_node = self.get_selected_timeline_node()
        if selected_timeline_node is None:
            label.setText("N/A")
        else:
            sim_bin_provider = selected_timeline_node.timeline.simulation_binary_provider
            if sim_bin_provider is None:
                label.setText("No simulation configured.")
            else:
                label.setText(str(sim_bin_provider))

    def _refresh_convert_to_selected_sim_button(self):
        selected_timeline_node = self.get_selected_timeline_node()
        self._ui.convertToSimButton.setEnabled(self._can_change_timeline_simulation_config(selected_timeline_node))

    def _convert_to_selected_sim(self):
        selected_timeline_node = self.get_selected_timeline_node()
        if self._can_change_timeline_simulation_config(selected_timeline_node):
            config = self.get_sim_bin_provider_to_convert_to()
            self._project.change_timeline_simulation_provider(selected_timeline_node.timeline_id, config)
            self._refresh_current_timeline_sim_label()

    def _refresh_selected_timeline_tags(self):
        selected_timeline = self.get_selected_timeline()

        tags_string = ""
        if selected_timeline is not None:
            tags = selected_timeline.get_tags()
            tags_string = ", ".join(tags)

        self._ui.timelineTagsLineEdit.setText(tags_string)

    def _save_selected_timeline_tags(self):
        selected_timeline_node = self.get_selected_timeline_node()
        if selected_timeline_node is not None:
            tags_list = [tag.strip() for tag in self._ui.timelineTagsLineEdit.text().split(',')]
            self._project.set_tags(selected_timeline_node.timeline_id, tags_list)

    def _revert_selected_timeline_tags(self):
        self._refresh_selected_timeline_tags()

    def run(self):
        self._main_window.show()
        return self._app.exec_()


if __name__ == "__main__":
    import sys
    app = App(sys.argv)
    app.run()
