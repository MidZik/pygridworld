"""
@author: Matt Idzik (MidZik)
"""
import SimulationManager as sm
from GUI import create_gui_process
import window
from typing import Optional
from PySide2 import QtCore, QtWidgets
from pathlib import Path
import json
from collections import deque
from weakref import WeakKeyDictionary
from ts_server import Server
from PySide2.QtWidgets import QFileDialog


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
    _TimelineTreeNodeRole = QtCore.Qt.UserRole + 1
    _SimIdentifierRole = QtCore.Qt.UserRole + 2
    _SimulationRegistration = QtCore.Qt.UserRole + 0

    _SimulationBinaryProvider = QtCore.Qt.UserRole + 1

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
        ui.deleteSelectedTimelineButton.clicked.connect(self._delete_selected_timeline)
        ui.convertToSimComboBox.currentIndexChanged.connect(self._on_convert_to_sim_combo_box_changed)
        ui.convertToSimButton.clicked.connect(self._convert_to_selected_sim)

        # Simulation Registry Tab
        ui.addSimSourceButton.clicked.connect(self._add_sim_source)
        ui.simSourceList.itemSelectionChanged.connect(self._on_selected_sim_source_changed)

        ui.registerSimFromSourceButton.clicked.connect(self._register_from_selected_sim_source)
        ui.removeSimSourceButton.clicked.connect(self._delete_selected_sim_source)

        ui.registeredSimList.itemSelectionChanged.connect(self._on_selected_registered_sim_changed)

        ui.saveRegisteredSimDescButton.clicked.connect(self._save_registered_sim_description)
        ui.discardRegisteredSimDescButton.clicked.connect(self._discard_registered_sim_description)
        ui.unregisterSimButton.clicked.connect(self._unregister_selected_sim_registration)

        self._project: Optional[sm.TimelinesProject] = None
        self._server = None

        self._simulations = {}
        self._visualizations = {}

        self._timeline_tree_widget_map = WeakKeyDictionary()

        self._thread_pool = QtCore.QThreadPool()

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

    def get_selected_timeline_simulation(self) -> Optional[sm.TimelineSimulation]:
        timeline_node = self.get_selected_timeline_node()

        if timeline_node is None:
            return None
        else:
            return self._simulations.get(timeline_node.timeline_id, None)

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
        return self.get_selected_timeline_simulation(), self.get_selected_eid(), self.get_selected_component_name()

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

    def get_sim_bin_provider_to_convert_to(self):
        return self._ui.convertToSimComboBox.currentData(App._SimulationBinaryProvider)

    def _on_application_quitting(self):
        for sim in self._simulations.values():
            sim.stop_process()

    def _make_timeline_item(self, timeline_node: sm.TimelineNode, preceding_item):
        if timeline_node in self._timeline_tree_widget_map:
            raise ValueError('Timeline node already has an item associated with it.')

        parent_item = self._timeline_tree_widget_map[timeline_node.parent_node]
        result_item = QtWidgets.QTreeWidgetItem(parent_item, preceding_item)
        result_item.setText(0, f"[{timeline_node.timeline.head()}] {timeline_node.timeline_id}")
        result_item.setData(0, App._TimelineTreeNodeRole, timeline_node)
        self._timeline_tree_widget_map[timeline_node] = result_item
        return result_item

    def _open_project(self):
        project_dir = QFileDialog.getExistingDirectory(self._main_window, options=QFileDialog.ShowDirsOnly)

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
            child_item = None
            for child_node in cur_node.child_nodes:
                child_item = self._make_timeline_item(child_node, child_item)
                node_deque.append(child_node)

        # TODO: Temp?
        self._on_timeline_tree_selected_item_changed()
        self._refresh_sim_registry_tab()

        combo_box = self._ui.convertToSimComboBox
        combo_box.clear()
        for config in self._project.get_all_simulation_providers():
            self._add_timeline_simulation_provider_to_combo_box(config)
        self._refresh_convert_to_selected_sim_button()

    def _on_timeline_tree_selected_item_changed(self):
        ui = self._ui

        ui.timelinePointList.clear()

        timeline_node = self.get_selected_timeline_node()

        if timeline_node is not None:
            for point in timeline_node.points():
                item = QtWidgets.QListWidgetItem(f"{point.tick}")
                item.setData(App._PointRole, point)
                ui.timelinePointList.addItem(item)

        self._refresh_convert_to_selected_sim_button()
        self._refresh_current_timeline_sim_label()
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
        singleton = self.get_selected_singleton_name()

        ui.createEntityButton.setEnabled(False)
        ui.destroyEntityButton.setEnabled(False)
        ui.assignComponentButton.setEnabled(False)
        ui.removeComponentButton.setEnabled(False)
        ui.revertComStateButton.setEnabled(False)
        ui.saveComStateButton.setEnabled(False)
        ui.revertSingletonStateButton.setEnabled(False)
        ui.saveSingletonStateButton.setEnabled(False)

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

            if singleton is not None:
                ui.revertSingletonStateButton.setEnabled(True)
                ui.saveSingletonStateButton.setEnabled(True)

    def _refresh_simulation_entity_list(self):
        ui = self._ui

        sim = self.get_selected_timeline_simulation()

        ui.entityList.clear()

        if sim is not None:
            entities = sim.get_all_entities()
            for eid in entities:
                ui.entityList.addItem(str(eid))

    def _refresh_simulation_singletons_list(self):
        ui = self._ui

        sim = self.get_selected_timeline_simulation()

        ui.singletonList.clear()

        if sim is not None:
            singletons = sim.get_singleton_names()
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
        point = self.get_selected_point()
        if point is not None:
            self.start_simulation_process(point)
        else:
            timeline_node = self.get_selected_timeline_node()
            if timeline_node is not None:
                self.start_simulation_process(timeline_node.head_point())
        self._refresh_convert_to_selected_sim_button()

    def _show_visualizer_for_current_timeline(self):
        sim = self.get_selected_timeline_simulation()
        if sim is not None:
            timeline_node = self.get_selected_timeline_node()
            timeline_id = timeline_node.timeline_id
            if timeline_id not in self._visualizations or not self._visualizations[timeline_id].is_alive():
                new_visualization = create_gui_process(sim.get_new_client())
                new_visualization.start()
                self._visualizations[timeline_node.timeline_id] = new_visualization

    def _kill_sim_process_for_current_timeline(self):
        timeline_node = self.get_selected_timeline_node()
        sim = self.get_selected_timeline_simulation()

        if sim is not None:
            sim.stop_process()
            del self._simulations[timeline_node.timeline_id]
            self._refresh_simulation_tab()
            self._refresh_convert_to_selected_sim_button()

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

    def start_simulation_process(self, point):
        if point.timeline_id() in self._simulations:
            return

        new_sim = self._project.create_timeline_simulation(point.timeline_id())
        new_sim.start_process(point.tick)

        self._simulations[point.timeline_id()] = new_sim
        self._refresh_simulation_tab()

    def _on_selected_entity_changed(self):
        ui = self._ui

        self._refresh_simulation_edit_buttons()

        ui.entityComponentList.clear()
        assign_components_button_menu = ui.assignComponentButton.menu()
        assign_components_button_menu.clear()

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

    def _on_assign_component_triggered(self, action):
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

        self._refresh_simulation_edit_buttons()

        ui.comStateTextEdit.clear()

        selected_sim = self.get_selected_timeline_simulation()
        selected_eid = self.get_selected_eid()
        selected_com = self.get_selected_component_name()

        if selected_sim is not None and selected_eid is not None and selected_com is not None:
            com_state_json = selected_sim.get_component_json(selected_eid, selected_com)
            com_state = json.loads(com_state_json)
            com_state_json = json.dumps(com_state, indent=2)  # pretty print
            ui.comStateTextEdit.setPlainText(com_state_json)

    def _start_selected_simulation(self):
        selected_sim = self.get_selected_timeline_simulation()

        if selected_sim is not None:
            selected_sim.start_simulation()
            # TODO: temp?
            self._refresh_simulation_start_stop_buttons()

    def _stop_selected_simulation(self):
        selected_sim = self.get_selected_timeline_simulation()

        if selected_sim is not None:
            selected_sim.stop_simulation()
            # TODO: temp?
            self._refresh_simulation_start_stop_buttons()

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
        self._on_selected_component_changed()

    def _save_selected_com_state(self):
        sim, eid, com = self.get_all_sim_tab_selections()

        if sim is not None and eid is not None and com is not None:
            com_state_json = self._ui.comStateTextEdit.toPlainText()
            sim.replace_component(eid, com, com_state_json)

    def _create_timeline_at_selection(self):
        timeline_node = self.get_selected_timeline_node()
        point = self.get_selected_point()

        if point is None and timeline_node is not None:
            point = timeline_node.head_point()

        new_timeline_node = self._project.create_timeline(point)

        previous_sibling = new_timeline_node.previous_sibling()
        if previous_sibling is not None:
            preceding_item = self._timeline_tree_widget_map[previous_sibling]
        else:
            preceding_item = None

        self._make_timeline_item(new_timeline_node, preceding_item)

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
                parent_node = timeline_node.parent_node
                self._project.delete_timeline(timeline_node)
                widget: QtWidgets.QTreeWidgetItem = self._timeline_tree_widget_map[timeline_node]
                parent_widget = self._timeline_tree_widget_map[parent_node]
                parent_widget.removeChild(widget)

    def _on_selected_singleton_changed(self):
        ui = self._ui

        self._refresh_simulation_edit_buttons()

        ui.singletonStateTextEdit.clear()

        singleton = self.get_selected_singleton_name()
        sim = self.get_selected_timeline_simulation()

        if sim is not None and singleton is not None:
            singleton_state_json = sim.get_singleton_json(singleton)
            singleton_state = json.loads(singleton_state_json)
            singleton_state_json = json.dumps(singleton_state, indent=2)  # pretty print
            ui.singletonStateTextEdit.setPlainText(singleton_state_json)

    def _revert_selected_singleton_state(self):
        self._on_selected_singleton_changed()

    def _save_selected_singleton_state(self):
        sim = self.get_selected_timeline_simulation()
        singleton = self.get_selected_singleton_name()

        if sim is not None and singleton is not None:
            singleton_state_json = self._ui.singletonStateTextEdit.toPlainText()
            sim.set_singleton_json(singleton, singleton_state_json)

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

    def _refresh_registered_sim_list(self):
        ui = self._ui
        ui.registeredSimList.clear()
        for reg in self._project.get_registered_simulations():
            item = QtWidgets.QListWidgetItem(str(reg.uuid))
            item.setData(App._SimulationRegistration, reg)
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

        combo_box = self._ui.convertToSimComboBox
        self._add_timeline_simulation_provider_to_combo_box(source)

    def _on_selected_sim_source_changed(self):
        self._refresh_simulation_source_section()

    def _register_from_selected_sim_source(self):
        selected_source = self.get_selected_simulation_source()
        if selected_source:
            reg = self._project.register_simulation(selected_source)
            item = QtWidgets.QListWidgetItem(str(reg.uuid))
            item.setData(App._SimulationRegistration, reg)
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
        if selected_reg is not None:
            selected_reg.set_description(self._ui.registeredSimDescriptionTextEdit.toPlainText())

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
        simulation_running = node.timeline_id in self._simulations
        return not (has_multiple_points or simulation_running)

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

    def run(self):
        self._main_window.show()
        return self._app.exec_()


if __name__ == "__main__":
    import sys
    app = App(sys.argv)
    app.run()
