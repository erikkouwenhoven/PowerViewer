import os
from datetime import datetime
from GUI.Tools.time_format import data_range_fmt
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMenu, QFileDialog, QStatusBar
from Utils.config import Config
from Utils.settings import Settings
from GUI.plotter import Plotter
from GUI.table_view import TableView
from Models.data_store import DataStore
from Models.data_view import DataView
from Models.data_store import c_LOCALFILE_ID
from ServerRequests.server_requests import TransferInfo  # TODO naar Utils


class GUIView(QMainWindow):
    """
    View voor main screen

    Notifiers van de plotter kunnen worden gezet:
        set_change_notifier
        set_redraw_notifier
    """

    c_LOCAL_FILE_LABEL = 'Local file'

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(Config().getUiDirName(), Config().getMainScreenFileName()), self)
        self.actionCallbacks = {}
        self.plotter = Plotter(self.ui.mpl_widget)
        self.table_view = TableView(self.ui.tableWidget)
        self.initialize()

    def initialize(self):
        self.setWindowTitle(f'{Config().getAppName()}  v.{Config().getVersion()}  (c) {Config().getAppInfo()}')
        self.ui.stackedWidget.setCurrentWidget(self.ui.plot)
        self.setStatusBar(QStatusBar())
        # context menus
        self.ui.stackedWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.stackedWidget.customContextMenuRequested.connect(self.show_graph_page_context_menu)
        # init data sources
        self.ui.datasourceComboBox.blockSignals(True)
        self.ui.datasourceComboBox.addItem(self.c_LOCAL_FILE_LABEL)
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
            if key == "calcExponentialDecay":
                self.actionCallbacks['calcExponentialDecay'] = value
            if key == "reload":
                self.actionCallbacks['reload'] = value
            if key == "saveData":
                self.actionCallbacks['saveData'] = value
            if key == "serverQuerySelected":
                self.ui.serverQueriesComboBox.activated.connect(value)
            if key == "serverQueries":
                self.actionCallbacks['serverQueries'] = value
            if key == "graphPage":
                self.actionCallbacks['graphPage'] = value
            if key == "tableView":
                self.actionCallbacks['tableView'] = value

    def set_visibility_change_notifier(self, visibility_change_notifier):
        self.plotter.set_visibility_change_notifier(visibility_change_notifier)

    def set_redraw_notifier(self, redraw_notifier):
        self.plotter.set_redraw_notifier(redraw_notifier)

    def show_graph_page_context_menu(self, position):
        menu = QMenu()
        settingsAction = menu.addAction("Control panel")
        solarDelayAction = menu.addAction("Solar delay")
        exponentialDecayAction = menu.addAction("Exponential decay")
        reloadAction = menu.addAction("Reload")
        saveSubMenu = QMenu("Save")
        menu.addMenu(saveSubMenu)
        saveAsDisplayedAction = saveSubMenu.addAction("As displayed")
        saveCompleteAction = saveSubMenu.addAction("Complete")
        menu.addSeparator()
        graphPageAction = menu.addAction("Graphs")
        serverQueriesAction = menu.addAction("Server queries")
        tableViewAction = menu.addAction("Table view")

        action = menu.exec(self.ui.mpl_widget.mapToGlobal(position))
        if action == settingsAction:
            self.actionCallbacks['showSettings']()
        elif action == solarDelayAction:
            self.actionCallbacks['calcSolarDelay']()
        elif action == exponentialDecayAction:
            self.actionCallbacks['calcExponentialDecay']()
        elif action == reloadAction:
            self.actionCallbacks['reload']()
        elif action == saveAsDisplayedAction:
            self.actionCallbacks['saveData'](signals=self.plotter.get_displayed_signals(), time_range=self.plotter.time_range)
        elif action == saveCompleteAction:
            self.actionCallbacks['saveData']()
        elif action == graphPageAction:
            self.actionCallbacks['graphPage']()
        elif action == serverQueriesAction:
            self.actionCallbacks['serverQueries']()
        elif action == tableViewAction:
            self.actionCallbacks['tableView']()

    def hide_settings(self):
        self.ui.settingsGroupBox.setChecked(False)
        self.ui.settingsGroupBox.setVisible(False)

    def show_settings(self):
        self.ui.settingsGroupBox.setChecked(True)
        self.ui.settingsGroupBox.setVisible(True)

    def set_server_requests(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.server)

    def set_graph_page(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.plot)

    def set_table_view(self, data_view: DataView):
        self.ui.stackedWidget.setCurrentWidget(self.ui.table)

    def show_table_data(self, data_view: DataView):
        self.table_view.show_data(data_view)

    def is_plotter_view(self) -> bool:
        return self.ui.stackedWidget.currentWidget() == self.ui.plot

    def get_signals_table(self, data_store_name: str) -> dict[str, bool]:
        assert data_store_name == self.get_data_store_name()
        return {self.ui.signalsTableWidget.item(row, 0).text(): True if self.ui.signalsTableWidget.item(row, 0).checkState() == Qt.CheckState.Checked
                else False for row in range(self.ui.signalsTableWidget.rowCount())}

    def get_visibilities(self) -> dict[str, bool]:
        return self.plotter.signal_visibilities

    def show_data(self, time_range, data_view: DataView):
        if self.is_plotter_view():
            self.plotter.time_range = time_range
            self.plotter.data_view = data_view
            for data_store in data_view.get_data_stores():
                self.plotter.set_signal_visibiities(Settings().get_checked_visibilities(data_store.name))
            self.plotter.update_plot()
        else:
            self.show_table_data(data_view)

    def show_data_views(self, data_views: dict[str, DataView]):
        self.ui.datasourceComboBox.blockSignals(True)
        self.ui.datasourceComboBox.addItems([data_view for data_view in data_views])
        self.ui.datasourceComboBox.blockSignals(False)

    def show_server_queries(self, server_queries: list[str]):
        self.ui.serverQueriesComboBox.blockSignals(True)
        self.ui.serverQueriesComboBox.addItems([server_query for server_query in server_queries])
        self.ui.serverQueriesComboBox.blockSignals(False)

    def get_data_store_name(self) -> str:
        current_text = self.ui.datasourceComboBox.currentText()
        if current_text != self.c_LOCAL_FILE_LABEL:
            return current_text
        else:
            return c_LOCALFILE_ID

    def set_data_store_name(self, datastore_name: str) -> None:
        return self.ui.datasourceComboBox.setCurrentText(datastore_name)

    def get_server_query(self) -> str:
        return self.ui.serverQueriesComboBox.currentText()

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

    def is_settings_selected(self) -> bool:
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

    def show_transfer_info(self, transfer_info: TransferInfo):
        self.statusBar().showMessage(str(transfer_info))
