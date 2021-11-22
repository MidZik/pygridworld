# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'command_prompt_dock_widget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_commandPromptDock(object):
    def setupUi(self, commandPromptDock):
        if not commandPromptDock.objectName():
            commandPromptDock.setObjectName(u"commandPromptDock")
        commandPromptDock.resize(712, 426)
        commandPromptDock.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.cmdPromptOutput = QPlainTextEdit(self.dockWidgetContents)
        self.cmdPromptOutput.setObjectName(u"cmdPromptOutput")
        self.cmdPromptOutput.setReadOnly(True)
        self.cmdPromptOutput.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)
        self.cmdPromptOutput.setMaximumBlockCount(1000)

        self.verticalLayout.addWidget(self.cmdPromptOutput)

        self.cmdPromptInput = QLineEdit(self.dockWidgetContents)
        self.cmdPromptInput.setObjectName(u"cmdPromptInput")

        self.verticalLayout.addWidget(self.cmdPromptInput)

        commandPromptDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(commandPromptDock)

        QMetaObject.connectSlotsByName(commandPromptDock)
    # setupUi

    def retranslateUi(self, commandPromptDock):
        commandPromptDock.setWindowTitle(QCoreApplication.translate("commandPromptDock", u"Command Prompt", None))
        self.cmdPromptInput.setPlaceholderText(QCoreApplication.translate("commandPromptDock", u"Enter command here.", None))
    # retranslateUi

