# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'window.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1282, 880)
        self.actionConnectToSimmaServer = QAction(MainWindow)
        self.actionConnectToSimmaServer.setObjectName(u"actionConnectToSimmaServer")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.timelineTree = QTreeView(self.splitter)
        self.timelineTree.setObjectName(u"timelineTree")
        self.timelineTree.setHeaderHidden(True)
        self.splitter.addWidget(self.timelineTree)
        self.timelinePointList = QListView(self.splitter)
        self.timelinePointList.setObjectName(u"timelinePointList")
        self.splitter.addWidget(self.timelinePointList)

        self.horizontalLayout.addWidget(self.splitter)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.processTab = QWidget()
        self.processTab.setObjectName(u"processTab")
        self.horizontalLayout_6 = QHBoxLayout(self.processTab)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.simulatorGroupBox = QGroupBox(self.processTab)
        self.simulatorGroupBox.setObjectName(u"simulatorGroupBox")
        self.horizontalLayout_18 = QHBoxLayout(self.simulatorGroupBox)
        self.horizontalLayout_18.setSpacing(2)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(2, 2, 2, 2)
        self.startSimulatorButton = QPushButton(self.simulatorGroupBox)
        self.startSimulatorButton.setObjectName(u"startSimulatorButton")

        self.horizontalLayout_18.addWidget(self.startSimulatorButton)


        self.verticalLayout_4.addWidget(self.simulatorGroupBox)

        self.creatorGroupBox = QGroupBox(self.processTab)
        self.creatorGroupBox.setObjectName(u"creatorGroupBox")
        self.verticalLayout_2 = QVBoxLayout(self.creatorGroupBox)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.startCreatorButton = QPushButton(self.creatorGroupBox)
        self.startCreatorButton.setObjectName(u"startCreatorButton")

        self.horizontalLayout_5.addWidget(self.startCreatorButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_8 = QLabel(self.creatorGroupBox)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_7.addWidget(self.label_8)

        self.startCreatorBinaryComboBox = QComboBox(self.creatorGroupBox)
        self.startCreatorBinaryComboBox.setObjectName(u"startCreatorBinaryComboBox")

        self.horizontalLayout_7.addWidget(self.startCreatorBinaryComboBox)

        self.horizontalLayout_7.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_7)


        self.verticalLayout_4.addWidget(self.creatorGroupBox)

        self.currentProcessesGroupBox = QGroupBox(self.processTab)
        self.currentProcessesGroupBox.setObjectName(u"currentProcessesGroupBox")
        self.horizontalLayout_2 = QHBoxLayout(self.currentProcessesGroupBox)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.currentProcessesList = QListView(self.currentProcessesGroupBox)
        self.currentProcessesList.setObjectName(u"currentProcessesList")

        self.horizontalLayout_2.addWidget(self.currentProcessesList)


        self.verticalLayout_4.addWidget(self.currentProcessesGroupBox)


        self.horizontalLayout_6.addLayout(self.verticalLayout_4)

        self.horizontalLayout_6.setStretch(0, 1)
        self.tabWidget.addTab(self.processTab, "")
        self.timelineTab = QWidget()
        self.timelineTab.setObjectName(u"timelineTab")
        self.verticalLayout = QVBoxLayout(self.timelineTab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.createCreatorAtSelection = QPushButton(self.timelineTab)
        self.createCreatorAtSelection.setObjectName(u"createCreatorAtSelection")

        self.horizontalLayout_4.addWidget(self.createCreatorAtSelection)

        self.createSimulatorAtSelection = QPushButton(self.timelineTab)
        self.createSimulatorAtSelection.setObjectName(u"createSimulatorAtSelection")

        self.horizontalLayout_4.addWidget(self.createSimulatorAtSelection)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_6)

        self.deleteSelectedTimelineButton = QPushButton(self.timelineTab)
        self.deleteSelectedTimelineButton.setObjectName(u"deleteSelectedTimelineButton")
        palette = QPalette()
        brush = QBrush(QColor(170, 0, 0, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        brush1 = QBrush(QColor(120, 120, 120, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush1)
        self.deleteSelectedTimelineButton.setPalette(palette)

        self.horizontalLayout_4.addWidget(self.deleteSelectedTimelineButton)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label_7 = QLabel(self.timelineTab)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_16.addWidget(self.label_7)

        self.timelineBinaryLabel = QLabel(self.timelineTab)
        self.timelineBinaryLabel.setObjectName(u"timelineBinaryLabel")
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.timelineBinaryLabel.setFont(font)

        self.horizontalLayout_16.addWidget(self.timelineBinaryLabel)

        self.horizontalLayout_16.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_5 = QLabel(self.timelineTab)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_8.addWidget(self.label_5)

        self.newTagLineEdit = QLineEdit(self.timelineTab)
        self.newTagLineEdit.setObjectName(u"newTagLineEdit")

        self.horizontalLayout_8.addWidget(self.newTagLineEdit)

        self.newTagButton = QPushButton(self.timelineTab)
        self.newTagButton.setObjectName(u"newTagButton")

        self.horizontalLayout_8.addWidget(self.newTagButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer)

        self.deleteTagsButton = QPushButton(self.timelineTab)
        self.deleteTagsButton.setObjectName(u"deleteTagsButton")
        palette1 = QPalette()
        brush2 = QBrush(QColor(181, 0, 0, 255))
        brush2.setStyle(Qt.SolidPattern)
        palette1.setBrush(QPalette.Active, QPalette.ButtonText, brush2)
        palette1.setBrush(QPalette.Inactive, QPalette.ButtonText, brush2)
        palette1.setBrush(QPalette.Disabled, QPalette.ButtonText, brush1)
        self.deleteTagsButton.setPalette(palette1)

        self.horizontalLayout_8.addWidget(self.deleteTagsButton)


        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.tagsListWidget = QListWidget(self.timelineTab)
        self.tagsListWidget.setObjectName(u"tagsListWidget")
        self.tagsListWidget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.verticalLayout.addWidget(self.tagsListWidget)

        self.label = QLabel(self.timelineTab)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.label)

        self.pointStateJsonTextEdit = QPlainTextEdit(self.timelineTab)
        self.pointStateJsonTextEdit.setObjectName(u"pointStateJsonTextEdit")
        self.pointStateJsonTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.pointStateJsonTextEdit)

        self.tabWidget.addTab(self.timelineTab, "")
        self.binaryRegistryTab = QWidget()
        self.binaryRegistryTab.setObjectName(u"binaryRegistryTab")
        self.verticalLayout_3 = QVBoxLayout(self.binaryRegistryTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.binarySourceLayout = QHBoxLayout()
        self.binarySourceLayout.setObjectName(u"binarySourceLayout")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.addLocalSimbinButton = QPushButton(self.binaryRegistryTab)
        self.addLocalSimbinButton.setObjectName(u"addLocalSimbinButton")

        self.verticalLayout_6.addWidget(self.addLocalSimbinButton)

        self.localSimbinList = QListView(self.binaryRegistryTab)
        self.localSimbinList.setObjectName(u"localSimbinList")

        self.verticalLayout_6.addWidget(self.localSimbinList)


        self.binarySourceLayout.addLayout(self.verticalLayout_6)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.uploadBinaryFromSimbinButton = QPushButton(self.binaryRegistryTab)
        self.uploadBinaryFromSimbinButton.setObjectName(u"uploadBinaryFromSimbinButton")

        self.horizontalLayout_3.addWidget(self.uploadBinaryFromSimbinButton)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)

        self.removeSimSourceButton = QPushButton(self.binaryRegistryTab)
        self.removeSimSourceButton.setObjectName(u"removeSimSourceButton")
        palette2 = QPalette()
        palette2.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette2.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette2.setBrush(QPalette.Disabled, QPalette.ButtonText, brush1)
        self.removeSimSourceButton.setPalette(palette2)

        self.horizontalLayout_3.addWidget(self.removeSimSourceButton)


        self.verticalLayout_7.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_2 = QLabel(self.binaryRegistryTab)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.horizontalLayout_13.addWidget(self.label_2)

        self.simSourceFilePathLabel = QLabel(self.binaryRegistryTab)
        self.simSourceFilePathLabel.setObjectName(u"simSourceFilePathLabel")
        self.simSourceFilePathLabel.setText(u"")
        self.simSourceFilePathLabel.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.horizontalLayout_13.addWidget(self.simSourceFilePathLabel)

        self.horizontalLayout_13.setStretch(1, 1)

        self.verticalLayout_7.addLayout(self.horizontalLayout_13)

        self.simbinFileContentsTextEdit = QPlainTextEdit(self.binaryRegistryTab)
        self.simbinFileContentsTextEdit.setObjectName(u"simbinFileContentsTextEdit")
        self.simbinFileContentsTextEdit.setReadOnly(True)

        self.verticalLayout_7.addWidget(self.simbinFileContentsTextEdit)


        self.binarySourceLayout.addLayout(self.verticalLayout_7)

        self.binarySourceLayout.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.binarySourceLayout)

        self.registeredSimsLayout = QHBoxLayout()
        self.registeredSimsLayout.setObjectName(u"registeredSimsLayout")
        self.binaryList = QListView(self.binaryRegistryTab)
        self.binaryList.setObjectName(u"binaryList")

        self.registeredSimsLayout.addWidget(self.binaryList)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.saveBinaryDescButton = QPushButton(self.binaryRegistryTab)
        self.saveBinaryDescButton.setObjectName(u"saveBinaryDescButton")

        self.horizontalLayout_14.addWidget(self.saveBinaryDescButton)

        self.discardBinaryDescButton = QPushButton(self.binaryRegistryTab)
        self.discardBinaryDescButton.setObjectName(u"discardBinaryDescButton")

        self.horizontalLayout_14.addWidget(self.discardBinaryDescButton)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_5)

        self.deleteBinaryButton = QPushButton(self.binaryRegistryTab)
        self.deleteBinaryButton.setObjectName(u"deleteBinaryButton")
        palette3 = QPalette()
        palette3.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette3.setBrush(QPalette.Disabled, QPalette.ButtonText, brush1)
        self.deleteBinaryButton.setPalette(palette3)

        self.horizontalLayout_14.addWidget(self.deleteBinaryButton)


        self.verticalLayout_9.addLayout(self.horizontalLayout_14)

        self.label_3 = QLabel(self.binaryRegistryTab)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_9.addWidget(self.label_3)

        self.bianryDescriptionTextEdit = QPlainTextEdit(self.binaryRegistryTab)
        self.bianryDescriptionTextEdit.setObjectName(u"bianryDescriptionTextEdit")

        self.verticalLayout_9.addWidget(self.bianryDescriptionTextEdit)

        self.label_4 = QLabel(self.binaryRegistryTab)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout_9.addWidget(self.label_4)

        self.binaryMetadataTextEdit = QPlainTextEdit(self.binaryRegistryTab)
        self.binaryMetadataTextEdit.setObjectName(u"binaryMetadataTextEdit")
        self.binaryMetadataTextEdit.setReadOnly(True)
        self.binaryMetadataTextEdit.setBackgroundVisible(False)

        self.verticalLayout_9.addWidget(self.binaryMetadataTextEdit)


        self.registeredSimsLayout.addLayout(self.verticalLayout_9)

        self.registeredSimsLayout.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.registeredSimsLayout)

        self.tabWidget.addTab(self.binaryRegistryTab, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1282, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionConnectToSimmaServer.setText(QCoreApplication.translate("MainWindow", u"Connec to Simma Server", None))
        self.simulatorGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Simulator", None))
        self.startSimulatorButton.setText(QCoreApplication.translate("MainWindow", u"Start Simulator", None))
        self.creatorGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Creator", None))
        self.startCreatorButton.setText(QCoreApplication.translate("MainWindow", u"Start Creator", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Creator Binary:", None))
        self.currentProcessesGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"Current Processes", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.processTab), QCoreApplication.translate("MainWindow", u"Processes", None))
        self.createCreatorAtSelection.setText(QCoreApplication.translate("MainWindow", u"Create Timeline Creator at Selection", None))
        self.createSimulatorAtSelection.setText(QCoreApplication.translate("MainWindow", u"Create Timeline Simulator at Selection", None))
        self.deleteSelectedTimelineButton.setText(QCoreApplication.translate("MainWindow", u"Delete Selected Timeline", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Timeline Binary:", None))
        self.timelineBinaryLabel.setText(QCoreApplication.translate("MainWindow", u"<current binary>", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"New Tag:", None))
        self.newTagButton.setText(QCoreApplication.translate("MainWindow", u"Add New Tag", None))
        self.deleteTagsButton.setText(QCoreApplication.translate("MainWindow", u"Delete Tags", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Point State JSON", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.timelineTab), QCoreApplication.translate("MainWindow", u"Timeline", None))
        self.addLocalSimbinButton.setText(QCoreApplication.translate("MainWindow", u"Add Local Simbin", None))
        self.uploadBinaryFromSimbinButton.setText(QCoreApplication.translate("MainWindow", u"Upload New Binary from Simbin", None))
        self.removeSimSourceButton.setText(QCoreApplication.translate("MainWindow", u"Remove Source", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Source File Path:", None))
        self.saveBinaryDescButton.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.discardBinaryDescButton.setText(QCoreApplication.translate("MainWindow", u"Discard", None))
        self.deleteBinaryButton.setText(QCoreApplication.translate("MainWindow", u"Delete Binary", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Description:", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Metadata:", None))
        self.binaryMetadataTextEdit.setPlainText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.binaryRegistryTab), QCoreApplication.translate("MainWindow", u"Simulation Registry", None))
    # retranslateUi

