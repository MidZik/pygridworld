"""
@author: Matt Idzik (MidZik)
"""
import argparse
from collections import defaultdict, deque
from typing import Union

from simma.gui import window, command_prompt_dock_widget as cmd_widget, process_controls
from simma.grpc_client import Client as SimmaClient, SimulatorContext, CreatorContext, TimelineDetails
from simma.simulation.client import Client as ProcessClient
from simma.gui.GUI import create_gui_process
from PySide2 import QtCore, QtWidgets, QtGui


_UserRole = QtCore.Qt.UserRole


class _WorkerSignals(QtCore.QObject):
    success = QtCore.Signal(object)
    error = QtCore.Signal(Exception)


class _Worker(QtCore.QRunnable):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self.signals = _WorkerSignals()

    @QtCore.Slot()
    def run(self) -> None:
        try:
            result = self._func(*self._args, **self._kwargs)
        except Exception as e:
            self.signals.error.emit(e)
        else:
            self.signals.success.emit(result)


class SimCommandPromptValidator(QtGui.QValidator):
    def validate(self, input, pos):
        if input.strip() != "":
            # any string that isn't only whitespace is valid
            return SimCommandPromptValidator.Acceptable
        return SimCommandPromptValidator.Intermediate


class ProcessControlsWidget(QtWidgets.QWidget):
    def __init__(self, parent, process_context: Union[SimulatorContext, CreatorContext]):
        super().__init__(parent)

        ui = process_controls.Ui_Form()
        ui.setupUi(self)
        self._ui = ui

        # Universal controls
        ui.showVisualizerButton.clicked.connect(self._show_visualizer_for_current_timeline)
        ui.disconnectButton.clicked.connect(self._disconnect)

        # Simulator controls
        ui.goToSelectedTickButton.clicked.connect(self._go_to_selected_tick)
        ui.saveToPointButton.clicked.connect(self._save_to_point)
        ui.simulatorStartButton.clicked.connect(self._start_simulator)
        ui.simulatorStopButton.clicked.connect(self._stop_simulator)

        # creator controls
        ui.startEditingButton.clicked.connect(self._start_editing)
        ui.stopEditingButton.clicked.connect(self._stop_editing)
        ui.goToSelectedTimelineButton.clicked.connect(self._go_to_selected_timeline)
        ui.saveToNewTimelineButton.clicked.connect(self._save_as_new_timeline)

        # Entities Subtab
        ui.createEntityButton.clicked.connect(self._create_entity)
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

        self.process_context = process_context

        if isinstance(process_context, SimulatorContext):
            ui.creatorControlsGroupBox.hide()
        elif isinstance(process_context, CreatorContext):
            ui.simulatorControlsGroupBox.hide()

        self.process_client = ProcessClient(process_context.address, process_context.user_token)


class ProjectApp(QtCore.QObject):
    def __init__(self, argv):
        super().__init__(None)
        self._app = QtWidgets.QApplication(argv)
        self._app.setQuitOnLastWindowClosed(True)
        self._main_window = QtWidgets.QMainWindow()

        cmd_parse = QtCore.QCommandLineParser()
        cmd_parse.process(self._app)
        self._server_address = cmd_parse.positionalArguments()[0]

        self._client = SimmaClient(self._server_address)

        ui = window.Ui_MainWindow()
        ui.setupUi(self._main_window)
        self._ui = ui

        # Navigation
        ui.timelineTree.itemSelectionChanged.connect(self._on_timeline_tree_selected_item_changed)
        ui.timelineTree.itemExpanded.connect(self._on_timeline_tree_item_expanded)
        ui.timelinePointList.itemSelectionChanged.connect(self._on_timeline_point_list_selected_item_changed)

        # processes tab
        ui.startSimulatorButton.clicked.connect(self._start_simulator)
        ui.startCreatorButton.clicked.connect(self._start_creator)

        # Timeline Tab
        ui.createCreatorAtSelection.clicked.connect(self._create_creator_at_selection)
        ui.createSimulatorAtSelection.clicked.connect(self._create_simulator_at_selection)
        ui.deleteSelectedTimelineButton.clicked.connect(self._delete_selected_timeline)
        ui.newTagButton.clicked.connect(self._add_new_tag_to_selected_timeline)
        ui.deleteTagsButton.clicked.connect(self._delete_tags_from_selected_timeline)

        # Simulation Registry Tab
        ui.addLocalSimbinButton.clicked.connect(self._add_local_simbin)
        ui.localSimbinList.itemSelectionChanged.connect(self._on_selected_local_simbin_changed)

        ui.uploadBinaryFromSimbinButton.clicked.connect(self._upload_binary)
        ui.removeSimSourceButton.clicked.connect(self._delete_selected_sim_source)

        ui.registeredSimList.itemSelectionChanged.connect(self._on_selected_registered_sim_changed)

        ui.saveRegisteredSimDescButton.clicked.connect(self._save_registered_sim_description)
        ui.discardRegisteredSimDescButton.clicked.connect(self._discard_registered_sim_description)
        ui.unregisterSimButton.clicked.connect(self._unregister_selected_sim_registration)

        self._timeline_tree_item_map = {}
        self.refresh_timeline_tree()

        self._process_widgets = {}

    def refresh_timeline_tree(self):
        self._timeline_tree_item_map.clear()
        timelines = self._client.get_timelines(filter_parents=(None,))
        root_item = self._ui.timelineTree.invisibleRootItem()

        timeline_details = [self._client.get_timeline_details(timeline_id) for timeline_id in timelines]

        for detail in timeline_details:
            item = QtWidgets.QTreeWidgetItem(root_item)
            item.setText(0, f"[{detail.head_tick}] {detail.timeline_id}")
            item.setData(0, _UserRole, detail)
            self._timeline_tree_item_map[detail.timeline_id] = item

    def _make_timeline_item(self, timeline_details: TimelineDetails):
        if timeline_details.timeline_id in self._timeline_tree_widget_map:
            raise ValueError('Timeline already has an item associated with it.')

        parent_item = self._timeline_tree_widget_map[timeline_details.parent_id]
        result_item = QtWidgets.QTreeWidgetItem(parent_item)
        result_item.setText(0, f"[{timeline_details.head_tick}] {timeline_details.timeline_id}")
        result_item.setData(0, _UserRole, timeline_details)
        self._timeline_tree_widget_map[timeline_details.timeline_id] = result_item
        return result_item

    def get_selected_timeline_id(self):
        items = self._ui.timelineTree.selectedItems()
        return items[0].data(0, _UserRole) if items else None

    def get_selected_timeline_tick(self):
        items = self._ui.timelinePointList.selectedItems()
        return items[0].text() if items else None

    def _on_timeline_tree_selected_item_changed(self):
        ui = self._ui
        ui.timelinePointList.clear()

        selected_timeline_id = self.get_selected_timeline_id()
        if selected_timeline_id is not None:
            ui.timelinePointList.addItems(self._client.get_timeline_ticks(selected_timeline_id))

    def _on_timeline_tree_item_expanded(self, item):
        detail = item.getData(0, _UserRole)
        item.takeChildren()
        child_timelines = self._client.get_timelines(filter_parents=(detail.timeline_id,))
        child_details = [self._client.get_timeline_details(timeline_id) for timeline_id in child_timelines]
        for child_detail in child_details:
            child_item = QtWidgets.QTreeWidgetItem(item)
            child_item.setText(0, f"[{child_detail.head_tick}] {child_detail.timeline_id}")
            child_item.setData(0, _UserRole, child_detail)
            self._timeline_tree_item_map[child_detail.timeline_id] = item

    def _on_timeline_point_list_selected_item_changed(self):
        pass

    def _start_simulator(self):
        pass

    def _start_creator(self):
        pass

    def _create_creator_at_selection(self):
        pass

    def _create_simulator_at_selection(self):
        pass

    def _delete_selected_timeline(self):
        pass

    def _add_new_tag_to_selected_timeline(self):
        pass

    def _delete_tags_from_selected_timeline(self):
        pass

    def _add_local_simbin(self):
        pass

    def _on_selected_local_simbin_changed(self):
        pass

    def _upload_binary(self):
        pass

    def _delete_selected_sim_source(self):
        pass

    def _on_selected_registered_sim_changed(self):
        pass

    def _save_registered_sim_description(self):
        pass

    def _discard_registered_sim_description(self):
        pass

    def _unregister_selected_sim_registration(self):
        pass

    def run(self):
        self._main_window.show()
        return self._app.exec_()


def main():
    import sys
    app = ProjectApp(sys.argv)
    app.run()


if __name__ == "__main__":
    main()
