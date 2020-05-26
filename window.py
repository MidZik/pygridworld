# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'window.ui',
# licensing of 'window.ui' applies.
#
# Created: Fri May 22 03:34:07 2020
#      by: pyside2-uic  running on PySide2 5.13.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1428, 965)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.timelineTab = QtWidgets.QWidget()
        self.timelineTab.setObjectName("timelineTab")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.timelineTab)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_2 = QtWidgets.QLabel(self.timelineTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_4.addWidget(self.label_2)
        self.current_navigation_timeline_id = QtWidgets.QLabel(self.timelineTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.current_navigation_timeline_id.sizePolicy().hasHeightForWidth())
        self.current_navigation_timeline_id.setSizePolicy(sizePolicy)
        self.current_navigation_timeline_id.setObjectName("current_navigation_timeline_id")
        self.horizontalLayout_4.addWidget(self.current_navigation_timeline_id)
        self.go_to_parent_button = QtWidgets.QPushButton(self.timelineTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.go_to_parent_button.sizePolicy().hasHeightForWidth())
        self.go_to_parent_button.setSizePolicy(sizePolicy)
        self.go_to_parent_button.setObjectName("go_to_parent_button")
        self.horizontalLayout_4.addWidget(self.go_to_parent_button)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.timelinePointTree = QtWidgets.QTreeWidget(self.timelineTab)
        self.timelinePointTree.setHeaderHidden(True)
        self.timelinePointTree.setObjectName("timelinePointTree")
        self.timelinePointTree.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.timelinePointTree)
        self.horizontalLayout_5.addLayout(self.verticalLayout)
        self.simulationsLayout = QtWidgets.QVBoxLayout()
        self.simulationsLayout.setObjectName("simulationsLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.start_sim_process_button = QtWidgets.QPushButton(self.timelineTab)
        self.start_sim_process_button.setEnabled(True)
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
        self.start_sim_process_button.setPalette(palette)
        self.start_sim_process_button.setObjectName("start_sim_process_button")
        self.verticalLayout_2.addWidget(self.start_sim_process_button)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.simulationsLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtWidgets.QLabel(self.timelineTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.reloadStateButton = QtWidgets.QPushButton(self.timelineTab)
        self.reloadStateButton.setObjectName("reloadStateButton")
        self.horizontalLayout_3.addWidget(self.reloadStateButton)
        self.saveStateButton = QtWidgets.QPushButton(self.timelineTab)
        self.saveStateButton.setObjectName("saveStateButton")
        self.horizontalLayout_3.addWidget(self.saveStateButton)
        self.simulationsLayout.addLayout(self.horizontalLayout_3)
        self.stateJsonTextEdit = QtWidgets.QPlainTextEdit(self.timelineTab)
        self.stateJsonTextEdit.setReadOnly(True)
        self.stateJsonTextEdit.setObjectName("stateJsonTextEdit")
        self.simulationsLayout.addWidget(self.stateJsonTextEdit)
        self.horizontalLayout_5.addLayout(self.simulationsLayout)
        self.tabWidget.addTab(self.timelineTab, "")
        self.simulationTab = QtWidgets.QWidget()
        self.simulationTab.setObjectName("simulationTab")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.simulationTab)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.simulationList = QtWidgets.QListWidget(self.simulationTab)
        self.simulationList.setObjectName("simulationList")
        self.verticalLayout_3.addWidget(self.simulationList)
        self.horizontalLayout_6.addLayout(self.verticalLayout_3)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.startSimButton = QtWidgets.QPushButton(self.simulationTab)
        self.startSimButton.setObjectName("startSimButton")
        self.horizontalLayout_7.addWidget(self.startSimButton)
        self.stopSimButton = QtWidgets.QPushButton(self.simulationTab)
        self.stopSimButton.setObjectName("stopSimButton")
        self.horizontalLayout_7.addWidget(self.stopSimButton)
        self.toggleSimEditButton = QtWidgets.QPushButton(self.simulationTab)
        self.toggleSimEditButton.setObjectName("toggleSimEditButton")
        self.horizontalLayout_7.addWidget(self.toggleSimEditButton)
        self.killSimButton = QtWidgets.QPushButton(self.simulationTab)
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
        self.killSimButton.setPalette(palette)
        self.killSimButton.setObjectName("killSimButton")
        self.horizontalLayout_7.addWidget(self.killSimButton)
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
        self.revertComStateButton = QtWidgets.QPushButton(self.entitiesTab)
        self.revertComStateButton.setObjectName("revertComStateButton")
        self.horizontalLayout_11.addWidget(self.revertComStateButton)
        self.saveComStateButton = QtWidgets.QPushButton(self.entitiesTab)
        self.saveComStateButton.setObjectName("saveComStateButton")
        self.horizontalLayout_11.addWidget(self.saveComStateButton)
        self.verticalLayout_5.addLayout(self.horizontalLayout_11)
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.entitiesTab)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.verticalLayout_5.addWidget(self.plainTextEdit)
        self.horizontalLayout_8.addLayout(self.verticalLayout_5)
        self.horizontalLayout_8.setStretch(2, 1)
        self.tabWidget_2.addTab(self.entitiesTab, "")
        self.singletonsTab = QtWidgets.QWidget()
        self.singletonsTab.setObjectName("singletonsTab")
        self.tabWidget_2.addTab(self.singletonsTab, "")
        self.verticalLayout_4.addWidget(self.tabWidget_2)
        self.horizontalLayout_6.addLayout(self.verticalLayout_4)
        self.horizontalLayout_6.setStretch(1, 1)
        self.tabWidget.addTab(self.simulationTab, "")
        self.horizontalLayout.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1428, 21))
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
        self.label_2.setText(QtWidgets.QApplication.translate("MainWindow", "Timeline ID:", None, -1))
        self.current_navigation_timeline_id.setText(QtWidgets.QApplication.translate("MainWindow", "-", None, -1))
        self.go_to_parent_button.setText(QtWidgets.QApplication.translate("MainWindow", "Go To Parent", None, -1))
        self.start_sim_process_button.setText(QtWidgets.QApplication.translate("MainWindow", "Start Simulation Process", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("MainWindow", "State JSON", None, -1))
        self.reloadStateButton.setText(QtWidgets.QApplication.translate("MainWindow", "Reload State", None, -1))
        self.saveStateButton.setText(QtWidgets.QApplication.translate("MainWindow", "Save State", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.timelineTab), QtWidgets.QApplication.translate("MainWindow", "Timelines", None, -1))
        self.startSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Start", None, -1))
        self.stopSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Stop", None, -1))
        self.toggleSimEditButton.setText(QtWidgets.QApplication.translate("MainWindow", "Toggle Edit", None, -1))
        self.killSimButton.setText(QtWidgets.QApplication.translate("MainWindow", "Kill Simulation", None, -1))
        self.createEntityButton.setText(QtWidgets.QApplication.translate("MainWindow", "Create", None, -1))
        self.destroyEntityButton.setText(QtWidgets.QApplication.translate("MainWindow", "Destroy", None, -1))
        self.assignComponentButton.setText(QtWidgets.QApplication.translate("MainWindow", "Assign", None, -1))
        self.removeComponentButton.setText(QtWidgets.QApplication.translate("MainWindow", "Remove", None, -1))
        self.revertComStateButton.setText(QtWidgets.QApplication.translate("MainWindow", "Revert", None, -1))
        self.saveComStateButton.setText(QtWidgets.QApplication.translate("MainWindow", "Save", None, -1))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.entitiesTab), QtWidgets.QApplication.translate("MainWindow", "Entities", None, -1))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.singletonsTab), QtWidgets.QApplication.translate("MainWindow", "Singletons", None, -1))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.simulationTab), QtWidgets.QApplication.translate("MainWindow", "Simulations", None, -1))
        self.menuProject.setTitle(QtWidgets.QApplication.translate("MainWindow", "Project", None, -1))
        self.actionOpen_Project.setText(QtWidgets.QApplication.translate("MainWindow", "Open Project", None, -1))
