import os
from datetime import datetime
from GUI.Tools.time_format import data_range_fmt
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMenu, QFileDialog
from Utils.config import Config
from Utils.settings import Settings
from GUI.plotter import Plotter
from Models.data_store import DataStore
from Models.data_view import DataView
from Models.data_store import c_LOCALFILE_ID


class GUIView(QMainWindow):
    """
    View voor main screen

    Notifiers van de plotter kunnen worden gezet:
        set_change_notifier
        set_redraw_notifier
    """

    c_LOCALFILE_LABEL = 'Local file'

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(Config().getUiDirName(), Config().getMainScreenFileName()), self)
        self.actionCallbacks = {}
        self.plotter = Plotter(self.ui.mpl_widget)
        self.initialize()

    def initialize(self):
        self.setWindowTitle(f'{Config().getAppName()}  v.{Config().getVersion()}  (c) {Config().getAppInfo()}')
        # context menus
        self.ui.mpl_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.mpl_widget.customContextMenuRequested.connect(self.showContextMenu)
        # init data sources
        self.ui.datasourceComboBox.blockSignals(True)
        self.ui.datasourceComboBox.addItem(self.c_LOCALFILE_LABEL)
        self.ui.datasourceComboBox.blockSignals(False)

    def connectEvents(self, commandDict):
        for key, value in commandDict.items():
            if key == "settingsDeactivated":
                self.ui.settingsGroupBox.clicked.connect(value)
            if key == "dataStoreSelected":
                self.ui.datasourceComboBox.activated.connect(value)
            if key == 'signalsTableChanged':
                self.ui.signalsTableWidget.cellChanged.connect(value)
            if key == "showSettings":
                self.actionCallbacks['showSettings'] = value
            if key == "calcSolarDelay":
                self.actionCallbacks['calcSolarDelay'] = value
            if key == "reload":
                self.actionCallbacks['reload'] = value
            if key == "saveData":
                self.actionCallbacks['saveData'] = value

    def set_visibility_change_notifier(self, visibility_change_notifier):
        self.plotter.set_visibility_change_notifier(visibility_change_notifier)

    def set_redraw_notifier(self, redraw_notifier):
        self.plotter.set_redraw_notifier(redraw_notifier)

    def showContextMenu(self, position):
        menu = QMenu()
        settingsAction = menu.addAction("Control panel")
        solarDelayAction = menu.addAction("Solar delay")
        reloadAction = menu.addAction("Reload")
        saveSubMenu = QMenu("Save")
        menu.addMenu(saveSubMenu)
        saveAsDisplayedAction = saveSubMenu.addAction("As displayed")
        saveCompleteAction = saveSubMenu.addAction("Complete")
        action = menu.exec(self.ui.mpl_widget.mapToGlobal(position))
        if action == settingsAction:
            self.actionCallbacks['showSettings']()
        elif action == solarDelayAction:
            self.actionCallbacks['calcSolarDelay']()
        elif action == reloadAction:
            self.actionCallbacks['reload']()
        elif action == saveAsDisplayedAction:
            self.actionCallbacks['saveData'](signals=self.plotter.get_displayed_signals(), time_range=self.plotter.time_range)
        elif action == saveCompleteAction:
            self.actionCallbacks['saveData']()

    def hideSettings(self):
        self.ui.settingsGroupBox.setChecked(False)
        self.ui.settingsGroupBox.setVisible(False)

    def showSettings(self):
        self.ui.settingsGroupBox.setChecked(True)
        self.ui.settingsGroupBox.setVisible(True)

    def getSignalsTable(self, data_store_name: str) -> dict[str, bool]:
        assert data_store_name == self.get_data_store_name()
        return {self.ui.signalsTableWidget.item(row, 0).text(): True if self.ui.signalsTableWidget.item(row, 0).checkState() == Qt.CheckState.Checked
                else False for row in range(self.ui.signalsTableWidget.rowCount())}

    def get_visibilities(self) -> dict[str, bool]:
        return self.plotter.signal_visibilities

    def show_data(self, time_range, data_view: DataView):
        self.plotter.time_range = time_range
        self.plotter.data_view = data_view
        for data_store in data_view.get_data_stores():
            self.plotter.set_signal_visibiities(Settings().get_checked_visibilities(data_store.name))
        self.plotter.update_plot()

    def show_data_views(self, data_views: dict[str, DataView]):
        self.ui.datasourceComboBox.blockSignals(True)
        self.ui.datasourceComboBox.addItems([data_view for data_view in data_views])
        self.ui.datasourceComboBox.blockSignals(False)

    def get_data_store_name(self) -> str:
        current_text = self.ui.datasourceComboBox.currentText()
        if current_text != self.c_LOCALFILE_LABEL:
            return current_text
        else:
            return c_LOCALFILE_ID

    def set_data_store_name(self, datastore_name: str) -> None:
        return self.ui.datasourceComboBox.setCurrentText(datastore_name)

    def show_signals_table(self, signal_check_states: dict[str, bool]):
        self.ui.signalsTableWidget.clearContents()
        self.ui.signalsTableWidget.setRowCount(len(signal_check_states))
        self.ui.signalsTableWidget.blockSignals(True)
        for row, signal in enumerate(signal_check_states):
            item = QTableWidgetItem(signal)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(
                Qt.CheckState.Unchecked if signal_check_states[signal] is False else Qt.CheckState.Checked)
            self.ui.signalsTableWidget.setItem(row, 0, item)
        self.ui.signalsTableWidget.blockSignals(False)

    def set_date_range(self, data_stores: list[DataStore]):
        if all([data_store.end_timestamp is not None for data_store in data_stores]) and all([data_store.start_timestamp is not None for data_store in data_stores]):
            max_time = min([datetime.fromtimestamp(data_store.end_timestamp) for data_store in data_stores])
            min_time = max([datetime.fromtimestamp(data_store.start_timestamp) for data_store in data_stores])
            self.ui.fromDateTimeLabel.setText(min_time.strftime(data_range_fmt))
            self.ui.toDateTimeLabel.setText(max_time.strftime(data_range_fmt))

    def isSettingsSelected(self) -> bool:
        return self.ui.settingsGroupBox.isChecked()

    def append_colors(self, colors: dict[str, str]) -> None:
        self.plotter.append_colors(colors)

    def query_local_file(self) -> str:
        filename, _ = QFileDialog.getOpenFileName(self, "Select data file", Config().getDataFilesPath())
        return filename

    def show_derived_data(self, derived_data: dict[str, float]):
        self.ui.deductionsTableWidget.setColumnWidth(0, 180)
        self.ui.deductionsTableWidget.clearContents()
        self.ui.deductionsTableWidget.setRowCount(len(derived_data))
        for row, signal in enumerate(derived_data):
            self.ui.deductionsTableWidget.setItem(row, 0, QTableWidgetItem(signal))
            try:
                self.ui.deductionsTableWidget.setItem(row, 1, QTableWidgetItem(f"{derived_data[signal]:.3f}"))
            except TypeError:
                self.ui.deductionsTableWidget.setItem(row, 1, QTableWidgetItem("-"))
