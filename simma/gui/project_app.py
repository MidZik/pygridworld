"""
@author: Matt Idzik (MidZik)
"""
import asyncio
import tempfile

import appdirs
import argparse
from collections import defaultdict, deque
from pathlib import Path
from typing import Union, Optional

from simma.gui import window, command_prompt_dock_widget as cmd_widget, process_controls
from simma.grpc_client import Client as SimmaClient, SimulatorContext, CreatorContext, TimelineDetails, BinaryDetails
from simma.simulation.client import Client as ProcessClient
from simma.gui.GUI import create_gui_process
from simma.binary import LocalSimbin, PackedSimbin
from PySide2 import QtCore, QtWidgets, QtGui


_UserRole = QtCore.Qt.UserRole


def _user_data_path():
    return Path(appdirs.user_data_dir('simma', False))


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

        # models
        self.timelines_model = QtGui.QStandardItemModel(0, 1)
        self.points_model = QtGui.QStandardItemModel(0, 1)
        self.local_simbins_model = QtGui.QStandardItemModel(0, 1)
        self.binaries_model = QtGui.QStandardItemModel(0, 1)

        _user_data_path().mkdir(exist_ok=True)
        simbin_paths_file = Path(_user_data_path() / 'simbins.txt')
        if not simbin_paths_file.exists():
            simbin_paths_file.touch()

        self.refresh_timelines_model()
        self.refresh_local_simbins_model()
        self.refresh_binaries_model()

        ui.timelineTree.setModel(self.timelines_model)
        ui.timelinePointList.setModel(self.points_model)
        ui.localSimbinList.setModel(self.local_simbins_model)
        ui.binaryList.setModel(self.binaries_model)

        # signals
        # Navigation
        ui.timelineTree.selectionModel().selectionChanged.connect(self._on_timeline_tree_selection_changed)
        ui.timelineTree.expanded.connect(self._on_timeline_tree_expanded)

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
        ui.localSimbinList.selectionModel().selectionChanged.connect(self._on_local_simbin_list_selection_changed)

        ui.uploadBinaryFromSimbinButton.clicked.connect(self._upload_binary)
        ui.removeSimSourceButton.clicked.connect(self._delete_selected_sim_source)

        ui.binaryList.selectionModel().selectionChanged.connect(self._on_binary_selection_changed)

        ui.saveBinaryDescButton.clicked.connect(self._save_binary_description)
        ui.discardBinaryDescButton.clicked.connect(self._discard_binary_description)
        ui.deleteBinaryButton.clicked.connect(self._delete_selected_binary)

    def refresh_timelines_model(self):
        self.timelines_model.clear()
        timelines = self._client.get_timelines(filter_parents=(None,))

        timeline_details = [self._client.get_timeline_details(timeline_id) for timeline_id in timelines]

        parent_item = self.timelines_model.invisibleRootItem()
        for detail in timeline_details:
            item = QtGui.QStandardItem(f"[{detail.head_tick}] {detail.timeline_id}")
            item.setData(detail)
            parent_item.appendRow(item)

    def refresh_local_simbins_model(self):
        self.local_simbins_model.clear()
        simbin_paths_file = Path(_user_data_path() / 'simbins.txt')
        with simbin_paths_file.open() as f:
            for path_string in f.readlines():
                if path_string:
                    path = Path(path_string)
                    simbin: LocalSimbin = asyncio.run(LocalSimbin.load(path))
                    item = QtGui.QStandardItem(f"{simbin.name} [{path}]")
                    item.setData(simbin)
                    self.local_simbins_model.appendRow(item)

    def refresh_binaries_model(self):
        self.binaries_model.clear()
        binary_details = self._client.get_binary_details()
        for detail in binary_details:
            item = QtGui.QStandardItem(f"{detail.name} ({detail.binary_id})")
            item.setData(detail)
            self.binaries_model.appendRow(item)

    def get_selected_timeline_details(self) -> Optional[TimelineDetails]:
        selection_model = self._ui.timelineTree.selectionModel()
        if selection_model.hasSelection():
            index = selection_model.selectedRows()[0]
            item = self.timelines_model.itemFromIndex(index)
            return item.data()
        else:
            return None

    def get_selected_local_simbin(self) -> Optional[LocalSimbin]:
        selection_model = self._ui.localSimbinList.selectionModel()
        if selection_model.hasSelection():
            index = selection_model.selectedRows()[0]
            item = self.local_simbins_model.itemFromIndex(index)
            return item.data()
        else:
            return None

    def get_selected_binary_item(self) -> Optional[QtGui.QStandardItem]:
        selection_model = self._ui.binaryList.selectionModel()
        if selection_model.hasSelection():
            index = selection_model.selectedRows()[0]
            item = self.binaries_model.itemFromIndex(index)
            return item
        else:
            return None

    def get_selected_timeline_tick(self):
        items = self._ui.timelinePointList.selectedItems()
        return items[0].text() if items else None

    def _on_timeline_tree_selection_changed(self):
        ui = self._ui
        ui.timelinePointList.clear()

        selected_timeline_details = self.get_selected_timeline_details()
        if selected_timeline_details is not None:
            self.points_model.clear()
            self.points_model.appendRow(
                [QtGui.QStandardItem(tick) for tick in
                 self._client.get_timeline_ticks(selected_timeline_details.timeline_id)]
            )

    def _on_timeline_tree_expanded(self, index):
        item = self.timelines_model.itemFromIndex(index)
        detail = item.data()
        item.removeRows(0, item.rowCount())
        child_timelines = self._client.get_timelines(filter_parents=(detail.timeline_id,))
        child_details = [self._client.get_timeline_details(timeline_id) for timeline_id in child_timelines]
        for child_detail in child_details:
            child_item = QtGui.QStandardItem(f"[{detail.head_tick}] {detail.timeline_id}")
            child_item.setData(child_detail)
            item.appendRow(child_item)

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
        local_simbin_path, _ = QtWidgets.QFileDialog.getOpenFileName(self._main_window, filter="Simbin (*.simbin)")
        if not local_simbin_path:
            return

        existing_items = self.local_simbins_model.findItems(local_simbin_path, QtCore.Qt.MatchContains)
        if existing_items:
            return

        simbin = asyncio.run(LocalSimbin.load(Path(local_simbin_path)))
        with (_user_data_path() / 'simbins.txt').open('a') as f:
            f.write(local_simbin_path)
        item = QtGui.QStandardItem(f"{simbin.name} [{local_simbin_path}]")
        item.setData(simbin)
        self.local_simbins_model.appendRow(item)

    def _on_local_simbin_list_selection_changed(self, index):
        pass

    def _upload_binary(self):
        selected_local_simbin = self.get_selected_local_simbin()
        if selected_local_simbin is None:
            return
        print("uploading...")
        with tempfile.TemporaryDirectory() as temp_packed_simbin_dir:
            packed_simbin = asyncio.run(
                PackedSimbin.create_from_local_simbin(Path(temp_packed_simbin_dir), selected_local_simbin))
            binary_id = self._client.upload_packed_simbin(packed_simbin)
        binary_details = self._client.get_binary_details(binary_id)
        item = QtGui.QStandardItem(f"{binary_details.name} [{binary_id}]")
        item.setData(binary_details)
        self.binaries_model.appendRow(item)

    def _delete_selected_sim_source(self):
        pass

    def _on_binary_selection_changed(self):
        pass

    def _save_binary_description(self):
        pass

    def _discard_binary_description(self):
        pass

    def _delete_selected_binary(self):
        item = self.get_selected_binary_item()
        if item is not None:
            self._client.delete_binary(item.data().binary_id)
            self.binaries_model.removeRow(item.row())

    def run(self):
        self._main_window.show()
        return self._app.exec_()


def main():
    import sys
    app = ProjectApp(sys.argv)
    app.run()


if __name__ == "__main__":
    main()
