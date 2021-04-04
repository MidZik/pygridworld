# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'window.ui',
# licensing of 'window.ui' applies.
#
# Created: Tue Feb  9 00:06:47 2021
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1356, 965)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.timelineTree = QtWidgets.QTreeWidget(self.splitter)
        self.timelineTree.setHeaderHidden(True)
        self.timelineTree.setObjectName("timelineTree")
        self.timelineTree.headerItem().setText(0, "1")
        self.timelinePointList = QtWidgets.QListWidget(self.splitter)
        self.timelinePointList.setObjectName("timelinePointList")
        self.horizontalLayout.addWidget(self.splitter)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.simulationTab = QtWidgets.QWidget()
        self.simulationTab.setObjectName("simulationTab")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.simulationTab)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.startSimProcessButton = QtWidgets.QPushButton(self.simulationTab)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 170, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 170, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.startSimProcessButton.setPalette(palette)
        self.startSimProcessButton.setObjectName("startSimProcessButton")
        self.horizontalLayout_2.addWidget(self.startSimProcessButton)
        self.showVisualizerButton = QtWidgets.QPushButton(self.simulationTab)
        self.showVisualizerButton.setObjectName("showVisualizerButton")
        self.horizontalLayout_2.addWidget(self.showVisualizerButton)
        self.killSimProcessButton = QtWidgets.QPushButton(self.simulationTab)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.killSimProcessButton.setPalette(palette)
        self.killSimProcessButton.setObjectName("killSimProcessButton")
        self.horizontalLayout_2.addWidget(self.killSimProcessButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.startSimButton = QtWidgets.QPushButton(self.simulationTab)
        self.startSimButton.setObjectName("startSimButton")
        self.horizontalLayout_7.addWidget(self.startSimButton)
        self.stopSimButton = QtWidgets.QPushButton(self.simulationTab)
        self.stopSimButton.setObjectName("stopSimButton")
        self.horizontalLayout_7.addWidget(self.stopSimButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem)
        self.startEditSimButton = QtWidgets.QPushButton(self.simulationTab)
        self.startEditSimButton.setObjectName("startEditSimButton")
        self.horizontalLayout_7.addWidget(self.startEditSimButton)
        self.commitEditsSimButton = QtWidgets.QPushButton(self.simulationTab)
        self.commitEditsSimButton.setObjectName("commitEditsSimButton")
        self.horizontalLayout_7.addWidget(self.commitEditsSimButton)
        self.discardEditsSimButton = QtWidgets.QPushButton(self.simulationTab)
        self.discardEditsSimButton.setObjectName("discardEditsSimButton")
        self.horizontalLayout_7.addWidget(self.discardEditsSimButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout_7)
        self.tabWidget_2 = QtWidgets.QTabWidget(self.simulationTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_2.sizePolicy().hasHeightForWidth())
        self.tabWidget_2.setSizePolicy(sizePolicy)
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.entitiesTab = QtWidgets.QWidget()
        self.entitiesTab.setObjectName("entitiesTab")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.entitiesTab)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.entityLayout = QtWidgets.QVBoxLayout()
        self.entityLayout.setObjectName("entityLayout")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.createEntityButton = QtWidgets.QPushButton(self.entitiesTab)
        self.createEntityButton.setObjectName("createEntityButton")
        self.horizontalLayout_9.addWidget(self.createEntityButton)
        self.destroyEntityButton = QtWidgets.QPushButton(self.entitiesTab)
        self.destroyEntityButton.setObjectName("destroyEntityButton")
        self.horizontalLayout_9.addWidget(self.destroyEntityButton)
        self.entityLayout.addLayout(self.horizontalLayout_9)
        self.entityList = QtWidgets.QListWidget(self.entitiesTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.entityList.sizePolicy().hasHeightForWidth())
        self.entityList.setSizePolicy(sizePolicy)
        self.entityList.setObjectName("entityList")
        self.entityLayout.addWidget(self.entityList)
        self.horizontalLayout_8.addLayout(self.entityLayout)
        self.entityComponentLayout = QtWidgets.QVBoxLayout()
        self.entityComponentLayout.setObjectName("entityComponentLayout")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.assignComponentButton = QtWidgets.QPushButton(self.entitiesTab)
        self.assignComponentButton.setObjectName("assignComponentButton")
        self.horizontalLayout_10.addWidget(self.assignComponentButton)
        self.removeComponentButton = QtWidgets.QPushButton(self.entitiesTab)
        self.removeComponentButton.setObjectName("removeComponentButton")
        self.horizontalLayout_10.addWidget(self.removeComponentButton)
        self.entityComponentLayout.addLayout(self.horizontalLayout_10)
        self.entityComponentList = QtWidgets.QListWidget(self.entitiesTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.entityComponentList.sizePolicy().hasHeightForWidth())
        self.entityComponentList.setSizePolicy(sizePolicy)
        self.entityComponentList.setObjectName("entityComponentList")
        self.entityComponentLayout.addWidget(self.entityComponentList)
        self.horizontalLayout_8.addLayout(self.entityComponentLayout)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_11.addItem(spacerItem1)
        self.revertComStateButton = QtWidgets.QPushButton(self.entitiesTab)
        self.revertComStateButton.setObjectName("revertComStateButton")
        self.horizontalLayout_11.addWidget(self.revertComStateButton)
        self.saveComStateButton = QtWidgets.QPushButton(self.entitiesTab)
        self.saveComStateButton.setObjectName("saveComStateButton")
        self.horizontalLayout_11.addWidget(self.saveComStateButton)
        self.verticalLayout_5.addLayout(self.horizontalLayout_11)
        self.comStateTextEdit = QtWidgets.QPlainTextEdit(self.entitiesTab)
        self.comStateTextEdit.setObjectName("comStateTextEdit")
        self.verticalLayout_5.addWidget(self.comStateTextEdit)
        self.horizontalLayout_8.addLayout(self.verticalLayout_5)
        self.horizontalLayout_8.setStretch(2, 1)
        self.tabWidget_2.addTab(self.entitiesTab, "")
        self.singletonsTab = QtWidgets.QWidget()
        self.singletonsTab.setObjectName("singletonsTab")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.singletonsTab)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.singletonList = QtWidgets.QListWidget(self.singletonsTab)
        self.singletonList.setObjectName("singletonList")
        self.horizontalLayout_12.addWidget(self.singletonList)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem2)
        self.revertSingletonStateButton = QtWidgets.QPushButton(self.singletonsTab)
        self.revertSingletonStateButton.setObjectName("revertSingletonStateButton")
        self.horizontalLayout_5.addWidget(self.revertSingletonStateButton)
        self.saveSingletonStateButton = QtWidgets.QPushButton(self.singletonsTab)
        self.saveSingletonStateButton.setObjectName("saveSingletonStateButton")
        self.horizontalLayout_5.addWidget(self.saveSingletonStateButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.singletonStateTextEdit = QtWidgets.QPlainTextEdit(self.singletonsTab)
        self.singletonStateTextEdit.setObjectName("singletonStateTextEdit")
        self.verticalLayout_2.addWidget(self.singletonStateTextEdit)
        self.horizontalLayout_12.addLayout(self.verticalLayout_2)
        self.horizontalLayout_12.setStretch(1, 1)
        self.tabWidget_2.addTab(self.singletonsTab, "")
        self.verticalLayout_4.addWidget(self.tabWidget_2)
        self.horizontalLayout_6.addLayout(self.verticalLayout_4)
        self.horizontalLayout_6.setStretch(0, 1)
        self.tabWidget.addTab(self.simulationTab, "")
        self.timelineTab = QtWidgets.QWidget()
        self.timelineTab.setObjectName("timelineTab")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.timelineTab)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.createTimelineAtSelectionButton = QtWidgets.QPushButton(self.timelineTab)
        self.createTimelineAtSelectionButton.setObjectName("createTimelineAtSelectionButton")
        self.horizontalLayout_4.addWidget(self.createTimelineAtSelectionButton)
        self.createSiblingTimelineButton = QtWidgets.QPushButton(self.timelineTab)
        self.createSiblingTimelineButton.setObjectName("createSiblingTimelineButton")
        self.horizontalLayout_4.addWidget(self.createSiblingTimelineButton)
        self.deleteSelectedTimelineButton = QtWidgets.QPushButton(self.timelineTab)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.deleteSelectedTimelineButton.setPalette(palette)
        self.deleteSelectedTimelineButton.setObjectName("deleteSelectedTimelineButton")
        self.horizontalLayout_4.addWidget(self.deleteSelectedTimelineButton)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.label_7 = QtWidgets.QLabel(self.timelineTab)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_16.addWidget(self.label_7)
        self.currentTimelineSimLabel = QtWidgets.QLabel(self.timelineTab)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.currentTimelineSimLabel.setFont(font)
        self.currentTimelineSimLabel.setObjectName("currentTimelineSimLabel")
        self.horizontalLayout_16.addWidget(self.currentTimelineSimLabel)
        self.horizontalLayout_16.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_16)
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.label_5 = QtWidgets.QLabel(self.timelineTab)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_15.addWidget(self.label_5)
        self.convertToSimComboBox = QtWidgets.QComboBox(self.timelineTab)
        self.convertToSimComboBox.setObjectName("convertToSimComboBox")
        self.horizontalLayout_15.addWidget(self.convertToSimComboBox)
        self.convertToSimButton = QtWidgets.QPushButton(self.timelineTab)
        self.convertToSimButton.setObjectName("convertToSimButton")
        self.horizontalLayout_15.addWidget(self.convertToSimButton)
        self.horizontalLayout_15.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_15)
        self.horizontalLayout_17 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.label_6 = QtWidgets.QLabel(self.timelineTab)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_17.addWidget(self.label_6)
        self.timelineTagsLineEdit = QtWidgets.QLineEdit(self.timelineTab)
        self.timelineTagsLineEdit.setObjectName("timelineTagsLineEdit")
        self.horizontalLayout_17.addWidget(self.timelineTagsLineEdit)
        self.revertTimelineTagsButton = QtWidgets.QPushButton(self.timelineTab)
        self.revertTimelineTagsButton.setObjectName("revertTimelineTagsButton")
        self.horizontalLayout_17.addWidget(self.revertTimelineTagsButton)
        self.saveTimelineTagsButton = QtWidgets.QPushButton(self.timelineTab)
        self.saveTimelineTagsButton.setObjectName("saveTimelineTagsButton")
        self.horizontalLayout_17.addWidget(self.saveTimelineTagsButton)
        self.verticalLayout.addLayout(self.horizontalLayout_17)
        self.label = QtWidgets.QLabel(self.timelineTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.pointStateJsonTextEdit = QtWidgets.QPlainTextEdit(self.timelineTab)
        self.pointStateJsonTextEdit.setReadOnly(True)
        self.pointStateJsonTextEdit.setObjectName("pointStateJsonTextEdit")
        self.verticalLayout.addWidget(self.pointStateJsonTextEdit)
        self.tabWidget.addTab(self.timelineTab, "")
        self.simRegistryTab = QtWidgets.QWidget()
        self.simRegistryTab.setObjectName("simRegistryTab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.simRegistryTab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.simSourceLayout = QtWidgets.QHBoxLayout()
        self.simSourceLayout.setObjectName("simSourceLayout")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.addSimSourceButton = QtWidgets.QPushButton(self.simRegistryTab)
        self.addSimSourceButton.setObjectName("addSimSourceButton")
        self.verticalLayout_6.addWidget(self.addSimSourceButton)
        self.simSourceList = QtWidgets.QListWidget(self.simRegistryTab)
        self.simSourceList.setObjectName("simSourceList")
        self.verticalLayout_6.addWidget(self.simSourceList)
        self.simSourceLayout.addLayout(self.verticalLayout_6)
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.registerSimFromSourceButton = QtWidgets.QPushButton(self.simRegistryTab)
        self.registerSimFromSourceButton.setObjectName("registerSimFromSourceButton")
        self.horizontalLayout_3.addWidget(self.registerSimFromSourceButton)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.removeSimSourceButton = QtWidgets.QPushButton(self.simRegistryTab)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.removeSimSourceButton.setPalette(palette)
        self.removeSimSourceButton.setObjectName("removeSimSourceButton")
        self.horizontalLayout_3.addWidget(self.removeSimSourceButton)
        self.verticalLayout_7.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_2 = QtWidgets.QLabel(self.simRegistryTab)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_13.addWidget(self.label_2)
        self.simSourceFilePathLabel = QtWidgets.QLabel(self.simRegistryTab)
        self.simSourceFilePathLabel.setText("")
        self.simSourceFilePathLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.simSourceFilePathLabel.setObjectName("simSourceFilePathLabel")
        self.horizontalLayout_13.addWidget(self.simSourceFilePathLabel)
        self.horizontalLayout_13.setStretch(1, 1)
        self.verticalLayout_7.addLayout(self.horizontalLayout_13)
        self.sourceFileContentsTextEdit = QtWidgets.QPlainTextEdit(self.simRegistryTab)
        self.sourceFileContentsTextEdit.setReadOnly(True)
        self.sourceFileContentsTextEdit.setObjectName("sourceFileContentsTextEdit")
        self.verticalLayout_7.addWidget(self.sourceFileContentsTextEdit)
        self.simSourceLayout.addLayout(self.verticalLayout_7)
        self.simSourceLayout.setStretch(1, 1)
        self.verticalLayout_3.addLayout(self.simSourceLayout)
        self.registeredSimsLayout = QtWidgets.QHBoxLayout()
        self.registeredSimsLayout.setObjectName("registeredSimsLayout")
        self.registeredSimList = QtWidgets.QListWidget(self.simRegistryTab)
        self.registeredSimList.setObjectName("registeredSimList")
        self.registeredSimsLayout.addWidget(self.registeredSimList)
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.saveRegisteredSimDescButton = QtWidgets.QPushButton(self.simRegistryTab)
        self.saveRegisteredSimDescButton.setObjectName("saveRegisteredSimDescButton")
        self.horizontalLayout_14.addWidget(self.saveRegisteredSimDescButton)
        self.discardRegisteredSimDescButton = QtWidgets.QPushButton(self.simRegistryTab)
        self.discardRegisteredSimDescButton.setObjectName("discardRegisteredSimDescButton")
        self.horizontalLayout_14.addWidget(self.discardRegisteredSimDescButton)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_14.addItem(spacerItem4)
        self.unregisterSimButton = QtWidgets.QPushButton(self.simRegistryTab)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        self.unregisterSimButton.setPalette(palette)
        self.unregisterSimButton.setObjectName("unregisterSimButton")
        self.horizontalLayout_14.addWidget(self.unregisterSimButton)
        self.verticalLayout_9.addLayout(self.horizontalLayout_14)
        self.label_3 = QtWidgets.QLabel(self.simRegistryTab)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_9.addWidget(self.label_3)
        self.registeredSimDescriptionTextEdit = QtWidgets.QPlainTextEdit(self.simRegistryTab)
        self.registeredSimDescriptionTextEdit.setObjectName("registeredSimDescriptionTextEdit")
        self.verticalLayout_9.addWidget(self.registeredSimDescriptionTextEdit)
        self.label_4 = QtWidgets.QLabel(self.simRegistryTab)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_9.addWidget(self.label_4)
        self.registeredSimMetadataTextEdit = QtWidgets.QPlainTextEdit(self.simRegistryTab)
        self.registeredSimMetadataTextEdit.setReadOnly(True)
        self.registeredSimMetadataTextEdit.setPlainText("")
        self.registeredSimMetadataTextEdit.setBackgroundVisible(False)
        self.registeredSimMetadataTextEdit.setObjectName("registeredSimMetadataTextEdit")
        self.verticalLayout_9.addWidget(self.registeredSimMetadataTextEdit)
        self.registeredSimsLayout.addLayout(self.verticalLayout_9)
        self.registeredSimsLayout.setStretch(1, 1)
        self.verticalLayout_3.addLayout(self.registeredSimsLayout)
        self.tabWidget.addTab(self.simRegistryTab, "")
        self.horizontalLayout.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1356, 21))
        self.menubar.setObjectName("menubar")
        self.menuProject = QtWidgets.QMenu(self.menubar)
        self.menuProject.setObjectName("menuProject")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpen_Project = QtWidgets.QAction(MainWindow)
        self.actionOpen_Project.setObjectName("actionOpen_Project")
        self.menuProject.addAction(self.actionOpen_Project)
        self.menubar.addAction(self.menuProject.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "MainWindow", None, -1))
        self.startSimProcessButton.setText(QtWidgets.QApplication.translate("MainWindow", "Start Simulation Process", None, -1))
        self.showVisualizerButton.setText(QtWidgets.QApplication.translate("MainWindow", "Show Visualizer", None, -1))
        self.killSimProcessButton.setText(QtWidgets.QApplication.translate("MainWindow", "Kill Simulation Process", None, -1))
        self.startSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Start", None, -1))
        self.stopSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Stop", None, -1))
        self.startEditSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Start Editing", None, -1))
        self.commitEditsSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Commit Edits", None, -1))
        self.discardEditsSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Discard Edits", None, -1))
        self.createEntityButton.setText(QtWidgets.QApplication.translate("MainWindow", "Create", None, -1))
        self.destroyEntityButton.setText(QtWidgets.QApplication.translate("MainWindow", "Destroy", None, -1))
        self.assignComponentButton.setText(QtWidgets.QApplication.translate("MainWindow", "Assign", None, -1))
        self.removeComponentButton.setText(QtWidgets.QApplication.translate("MainWindow", "Remove", None, -1))
        self.revertComStateButton.setText(QtWidgets.QApplication.translate("MainWindow", "Revert", None, -1))
        self.saveComStateButton.setText(QtWidgets.QApplication.translate("MainWindow", "Save", None, -1))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.entitiesTab), QtWidgets.QApplication.translate("MainWindow", "Entities", None, -1))
        self.revertSingletonStateButton.setText(QtWidgets.QApplication.translate("MainWindow", "Revert", None, -1))
        self.saveSingletonStateButton.setText(QtWidgets.QApplication.translate("MainWindow", "Save", None, -1))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.singletonsTab), QtWidgets.QApplication.translate("MainWindow", "Singletons", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.simulationTab), QtWidgets.QApplication.translate("MainWindow", "Simulation", None, -1))
        self.createTimelineAtSelectionButton.setText(QtWidgets.QApplication.translate("MainWindow", "Create Timeline at Selection", None, -1))
        self.createSiblingTimelineButton.setText(QtWidgets.QApplication.translate("MainWindow", "Create Sibling Timeline", None, -1))
        self.deleteSelectedTimelineButton.setText(QtWidgets.QApplication.translate("MainWindow", "Delete Selected Timeline", None, -1))
        self.label_7.setText(QtWidgets.QApplication.translate("MainWindow", "Current simulation:", None, -1))
        self.currentTimelineSimLabel.setText(QtWidgets.QApplication.translate("MainWindow", "<current sim>", None, -1))
        self.label_5.setText(QtWidgets.QApplication.translate("MainWindow", "Convert to simulation:", None, -1))
        self.convertToSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Convert", None, -1))
        self.label_6.setText(QtWidgets.QApplication.translate("MainWindow", "Tags:", None, -1))
        self.revertTimelineTagsButton.setText(QtWidgets.QApplication.translate("MainWindow", "Revert", None, -1))
        self.saveTimelineTagsButton.setText(QtWidgets.QApplication.translate("MainWindow", "Save", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("MainWindow", "Point State JSON", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.timelineTab), QtWidgets.QApplication.translate("MainWindow", "Timeline", None, -1))
        self.addSimSourceButton.setText(QtWidgets.QApplication.translate("MainWindow", "Add Source", None, -1))
        self.registerSimFromSourceButton.setText(QtWidgets.QApplication.translate("MainWindow", "Register Simulation from Source", None, -1))
        self.removeSimSourceButton.setText(QtWidgets.QApplication.translate("MainWindow", "Remove Source", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("MainWindow", "Source File Path:", None, -1))
        self.saveRegisteredSimDescButton.setText(QtWidgets.QApplication.translate("MainWindow", "Save", None, -1))
        self.discardRegisteredSimDescButton.setText(QtWidgets.QApplication.translate("MainWindow", "Discard", None, -1))
        self.unregisterSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Unregister", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("MainWindow", "Description:", None, -1))
        self.label_4.setText(QtWidgets.QApplication.translate("MainWindow", "Metadata:", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.simRegistryTab), QtWidgets.QApplication.translate("MainWindow", "Simulation Registry", None, -1))
        self.menuProject.setTitle(QtWidgets.QApplication.translate("MainWindow", "Project", None, -1))
        self.actionOpen_Project.setText(QtWidgets.QApplication.translate("MainWindow", "Open Project", None, -1))
