# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'process_controls.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1037, 732)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.showVisualizerButton = QPushButton(Form)
        self.showVisualizerButton.setObjectName(u"showVisualizerButton")

        self.horizontalLayout_2.addWidget(self.showVisualizerButton)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)

        self.disconnectButton = QPushButton(Form)
        self.disconnectButton.setObjectName(u"disconnectButton")
        palette = QPalette()
        brush = QBrush(QColor(170, 0, 0, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        brush1 = QBrush(QColor(120, 120, 120, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush1)
        self.disconnectButton.setPalette(palette)

        self.horizontalLayout_2.addWidget(self.disconnectButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.simulatorControlsGroupBox = QGroupBox(Form)
        self.simulatorControlsGroupBox.setObjectName(u"simulatorControlsGroupBox")
        self.horizontalLayout = QHBoxLayout(self.simulatorControlsGroupBox)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.goToSelectedTickButton = QPushButton(self.simulatorControlsGroupBox)
        self.goToSelectedTickButton.setObjectName(u"goToSelectedTickButton")

        self.horizontalLayout.addWidget(self.goToSelectedTickButton)

        self.line_3 = QFrame(self.simulatorControlsGroupBox)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.VLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line_3)

        self.saveToPointButton = QPushButton(self.simulatorControlsGroupBox)
        self.saveToPointButton.setObjectName(u"saveToPointButton")

        self.horizontalLayout.addWidget(self.saveToPointButton)

        self.line = QFrame(self.simulatorControlsGroupBox)
        self.line.setObjectName(u"line")
        self.line.setLineWidth(1)
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.simulatorStartButton = QPushButton(self.simulatorControlsGroupBox)
        self.simulatorStartButton.setObjectName(u"simulatorStartButton")

        self.horizontalLayout.addWidget(self.simulatorStartButton)

        self.simulatorStopButton = QPushButton(self.simulatorControlsGroupBox)
        self.simulatorStopButton.setObjectName(u"simulatorStopButton")

        self.horizontalLayout.addWidget(self.simulatorStopButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.simulatorControlsGroupBox)

        self.creatorControlsGroupBox = QGroupBox(Form)
        self.creatorControlsGroupBox.setObjectName(u"creatorControlsGroupBox")
        self.horizontalLayout_3 = QHBoxLayout(self.creatorControlsGroupBox)
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(2, 2, 2, 2)
        self.startEditingButton = QPushButton(self.creatorControlsGroupBox)
        self.startEditingButton.setObjectName(u"startEditingButton")

        self.horizontalLayout_3.addWidget(self.startEditingButton)

        self.stopEditingButton = QPushButton(self.creatorControlsGroupBox)
        self.stopEditingButton.setObjectName(u"stopEditingButton")

        self.horizontalLayout_3.addWidget(self.stopEditingButton)

        self.line_2 = QFrame(self.creatorControlsGroupBox)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_2)

        self.goToSelectedTimelineButton = QPushButton(self.creatorControlsGroupBox)
        self.goToSelectedTimelineButton.setObjectName(u"goToSelectedTimelineButton")

        self.horizontalLayout_3.addWidget(self.goToSelectedTimelineButton)

        self.saveToNewTimelineButton = QPushButton(self.creatorControlsGroupBox)
        self.saveToNewTimelineButton.setObjectName(u"saveToNewTimelineButton")

        self.horizontalLayout_3.addWidget(self.saveToNewTimelineButton)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addWidget(self.creatorControlsGroupBox)

        self.tabWidget_2 = QTabWidget(Form)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_2.sizePolicy().hasHeightForWidth())
        self.tabWidget_2.setSizePolicy(sizePolicy)
        self.entitiesTab = QWidget()
        self.entitiesTab.setObjectName(u"entitiesTab")
        self.horizontalLayout_8 = QHBoxLayout(self.entitiesTab)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.entityLayout = QVBoxLayout()
        self.entityLayout.setObjectName(u"entityLayout")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.createEntityButton = QPushButton(self.entitiesTab)
        self.createEntityButton.setObjectName(u"createEntityButton")

        self.horizontalLayout_9.addWidget(self.createEntityButton)

        self.destroyEntityButton = QPushButton(self.entitiesTab)
        self.destroyEntityButton.setObjectName(u"destroyEntityButton")

        self.horizontalLayout_9.addWidget(self.destroyEntityButton)


        self.entityLayout.addLayout(self.horizontalLayout_9)

        self.entityList = QListWidget(self.entitiesTab)
        self.entityList.setObjectName(u"entityList")

        self.entityLayout.addWidget(self.entityList)


        self.horizontalLayout_8.addLayout(self.entityLayout)

        self.entityComponentLayout = QVBoxLayout()
        self.entityComponentLayout.setObjectName(u"entityComponentLayout")
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.assignComponentButton = QPushButton(self.entitiesTab)
        self.assignComponentButton.setObjectName(u"assignComponentButton")

        self.horizontalLayout_10.addWidget(self.assignComponentButton)

        self.removeComponentButton = QPushButton(self.entitiesTab)
        self.removeComponentButton.setObjectName(u"removeComponentButton")

        self.horizontalLayout_10.addWidget(self.removeComponentButton)


        self.entityComponentLayout.addLayout(self.horizontalLayout_10)

        self.entityComponentList = QListWidget(self.entitiesTab)
        self.entityComponentList.setObjectName(u"entityComponentList")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.entityComponentList.sizePolicy().hasHeightForWidth())
        self.entityComponentList.setSizePolicy(sizePolicy1)

        self.entityComponentLayout.addWidget(self.entityComponentList)


        self.horizontalLayout_8.addLayout(self.entityComponentLayout)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_2)

        self.revertComStateButton = QPushButton(self.entitiesTab)
        self.revertComStateButton.setObjectName(u"revertComStateButton")

        self.horizontalLayout_11.addWidget(self.revertComStateButton)

        self.saveComStateButton = QPushButton(self.entitiesTab)
        self.saveComStateButton.setObjectName(u"saveComStateButton")

        self.horizontalLayout_11.addWidget(self.saveComStateButton)


        self.verticalLayout_5.addLayout(self.horizontalLayout_11)

        self.comStateTextEdit = QPlainTextEdit(self.entitiesTab)
        self.comStateTextEdit.setObjectName(u"comStateTextEdit")

        self.verticalLayout_5.addWidget(self.comStateTextEdit)


        self.horizontalLayout_8.addLayout(self.verticalLayout_5)

        self.horizontalLayout_8.setStretch(2, 1)
        self.tabWidget_2.addTab(self.entitiesTab, "")
        self.singletonsTab = QWidget()
        self.singletonsTab.setObjectName(u"singletonsTab")
        self.horizontalLayout_12 = QHBoxLayout(self.singletonsTab)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.singletonList = QListWidget(self.singletonsTab)
        self.singletonList.setObjectName(u"singletonList")

        self.horizontalLayout_12.addWidget(self.singletonList)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.revertSingletonStateButton = QPushButton(self.singletonsTab)
        self.revertSingletonStateButton.setObjectName(u"revertSingletonStateButton")

        self.horizontalLayout_5.addWidget(self.revertSingletonStateButton)

        self.saveSingletonStateButton = QPushButton(self.singletonsTab)
        self.saveSingletonStateButton.setObjectName(u"saveSingletonStateButton")

        self.horizontalLayout_5.addWidget(self.saveSingletonStateButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.singletonStateTextEdit = QPlainTextEdit(self.singletonsTab)
        self.singletonStateTextEdit.setObjectName(u"singletonStateTextEdit")

        self.verticalLayout_2.addWidget(self.singletonStateTextEdit)


        self.horizontalLayout_12.addLayout(self.verticalLayout_2)

        self.horizontalLayout_12.setStretch(1, 1)
        self.tabWidget_2.addTab(self.singletonsTab, "")

        self.verticalLayout.addWidget(self.tabWidget_2)


        self.retranslateUi(Form)

        self.tabWidget_2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.showVisualizerButton.setText(QCoreApplication.translate("Form", u"Show Visualizer", None))
        self.disconnectButton.setText(QCoreApplication.translate("Form", u"Disconnect", None))
        self.simulatorControlsGroupBox.setTitle(QCoreApplication.translate("Form", u"Simulator Controls", None))
        self.goToSelectedTickButton.setText(QCoreApplication.translate("Form", u"Go To Tick", None))
        self.saveToPointButton.setText(QCoreApplication.translate("Form", u"Save To Point", None))
        self.simulatorStartButton.setText(QCoreApplication.translate("Form", u"Start", None))
        self.simulatorStopButton.setText(QCoreApplication.translate("Form", u"Stop", None))
        self.creatorControlsGroupBox.setTitle(QCoreApplication.translate("Form", u"Creator Controls", None))
        self.startEditingButton.setText(QCoreApplication.translate("Form", u"Start Editing", None))
        self.stopEditingButton.setText(QCoreApplication.translate("Form", u"Stop Editing", None))
        self.goToSelectedTimelineButton.setText(QCoreApplication.translate("Form", u"Go To Timeline", None))
        self.saveToNewTimelineButton.setText(QCoreApplication.translate("Form", u"Save As New Timeline", None))
        self.createEntityButton.setText(QCoreApplication.translate("Form", u"Create", None))
        self.destroyEntityButton.setText(QCoreApplication.translate("Form", u"Destroy", None))
        self.assignComponentButton.setText(QCoreApplication.translate("Form", u"Assign", None))
        self.removeComponentButton.setText(QCoreApplication.translate("Form", u"Remove", None))
        self.revertComStateButton.setText(QCoreApplication.translate("Form", u"Revert", None))
        self.saveComStateButton.setText(QCoreApplication.translate("Form", u"Save", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.entitiesTab), QCoreApplication.translate("Form", u"Entities", None))
        self.revertSingletonStateButton.setText(QCoreApplication.translate("Form", u"Revert", None))
        self.saveSingletonStateButton.setText(QCoreApplication.translate("Form", u"Save", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.singletonsTab), QCoreApplication.translate("Form", u"Singletons", None))
    # retranslateUi

