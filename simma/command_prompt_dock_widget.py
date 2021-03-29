# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'command_prompt_dock_widget.ui',
# licensing of 'command_prompt_dock_widget.ui' applies.
#
# Created: Mon Dec 28 07:58:25 2020
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_commandPromptDock(object):
    def setupUi(self, commandPromptDock):
        commandPromptDock.setObjectName("commandPromptDock")
        commandPromptDock.resize(712, 426)
        commandPromptDock.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable|QtWidgets.QDockWidget.DockWidgetMovable)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.cmdPromptOutput = QtWidgets.QPlainTextEdit(self.dockWidgetContents)
        self.cmdPromptOutput.setReadOnly(True)
        self.cmdPromptOutput.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.cmdPromptOutput.setMaximumBlockCount(1000)
        self.cmdPromptOutput.setObjectName("cmdPromptOutput")
        self.verticalLayout.addWidget(self.cmdPromptOutput)
        self.cmdPromptInput = QtWidgets.QLineEdit(self.dockWidgetContents)
        self.cmdPromptInput.setObjectName("cmdPromptInput")
        self.verticalLayout.addWidget(self.cmdPromptInput)
        commandPromptDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(commandPromptDock)
        QtCore.QMetaObject.connectSlotsByName(commandPromptDock)

    def retranslateUi(self, commandPromptDock):
        commandPromptDock.setWindowTitle(QtWidgets.QApplication.translate("commandPromptDock", "Command Prompt", None, -1))
        self.cmdPromptInput.setPlaceholderText(QtWidgets.QApplication.translate("commandPromptDock", "Enter command here.", None, -1))

