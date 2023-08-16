import os
from datetime import datetime
from PyQt6 import uic
from PyQt6.QtCore import QDateTime, QDate, QTime, Qt
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMenu
from Utils.config import Config
import matplotlib.dates as mdates
import matplotlib as mpl
from GUI.gui_model import GUIModel
from Models.data_store import DataStore


class GUIView(QMainWindow):
    """ View voor main screen """

    colors = {
        "CURRENT_USAGE": "blue",
        "CURRENT_PRODUCTION": "red",
        "CURRENT_USAGE_PHASE1": "aqua",
        "CURRENT_USAGE_PHASE2": "pink",
        "CURRENT_USAGE_PHASE3": "maroon",
        "CURRENT_PRODUCTION_PHASE1": "purple",
        "CURRENT_PRODUCTION_PHASE2": "cyan",
        "CURRENT_PRODUCTION_PHASE3": "magenta",
        "USAGE_GAS": "lime",
        "SOLAR": "yellow",
    }

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(Config().getUiDirName(), Config().getMainScreenFileName()), self)
        self.setWindowTitle(f'{Config().getAppName()}  v.{Config().getVersion()}  (c) {Config().getAppInfo()}')
        self.actionCallbacks = {}
        self.data_store = None
        self.time_range = None  # tuple (start, end) of current plot
        self.plot_signal_status = {}  # Dict mapping signal name to on/off status
        self.lined = {}  # Dict mapping legend text to line, enabling hiding/showing
        self.span_rect = [None, None]
        self.aspan = None
        self.initialize()

    def initialize(self):
        self.connect_mpl_events()
        # context menus
        self.ui.mplWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.mplWidget.customContextMenuRequested.connect(self.showContextMenu)

    def connectEvents(self, commandDict):
        for key, value in commandDict.items():
            if key == "settingsDeactivated":
                self.ui.settingsGroupBox.clicked.connect(value)
            if key == "dataStoreSelected":
                self.ui.datasourceComboBox.currentIndexChanged.connect(value)
            if key == 'signalsTableChanged':
                self.ui.signalsTableWidget.cellChanged.connect(value)
            if key == "showSettings":
                self.actionCallbacks['showSettings'] = value

    def connect_mpl_events(self):
        self.ui.mplWidget.canvas.mpl_connect('pick_event', self.on_pick)
        self.ui.mplWidget.canvas.mpl_connect('button_press_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('button_release_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('motion_notify_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('scroll_event', self.on_mouse_scroll_event)

    def showContextMenu(self, position):
        menu = QMenu()
        settingsAction = menu.addAction("Settings")
        action = menu.exec(self.ui.mplWidget.mapToGlobal(position))
        if action == settingsAction:
            self.actionCallbacks['showSettings']()

    def hideSettings(self):
        self.ui.settingsGroupBox.setChecked(False)
        self.ui.settingsGroupBox.setVisible(False)

    def showSettings(self):
        self.ui.settingsGroupBox.setChecked(True)
        self.ui.settingsGroupBox.setVisible(True)

    def getSignalsTable(self, data_store_name: str) -> dict[str, bool]:
        assert data_store_name == self.get_data_store_name()
        return {self.ui.signalsTableWidget.item(row, 0).text(): True if self.ui.signalsTableWidget.item(row, 0).checkState() == Qt.CheckState.Checked else False
                for row in range(self.ui.signalsTableWidget.rowCount())}

    def show_data(self, data, time_range, data_store: DataStore):
        self.time_range = time_range
        self.data_store = data_store
        self.update_plot()

    def update_plot(self):
        lines = []  # the line plots
        self.ui.mplWidget.canvas.ax.clear()
        myFmt = mdates.DateFormatter('%H:%M')
        self.ui.mplWidget.canvas.ax.xaxis.set_major_formatter(myFmt)
        self.ui.mplWidget.canvas.ax.set_xlabel('time [.]')
        unit = {'W', 'kW'}.intersection(Config().getPreferredUnits())  # TODO dit hoort hier niet
        self.ui.mplWidget.canvas.ax.set_ylabel(f"Power [{list(unit)[0]}]")
        self.ui.mplWidget.canvas.ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(self.ui.mplWidget.canvas.ax.xaxis.get_major_locator()))
        if self.data_store:
            signals = [item for item in self.data_store.data if item != 'timestamp']
            i_range = range(GUIModel.b_search(self.data_store.data['timestamp'], self.time_range[0]),
                            GUIModel.b_search(self.data_store.data['timestamp'], self.time_range[1]))
            time_data = [datetime.fromtimestamp(self.data_store.data['timestamp'][idx]) for idx in i_range]
            for signal in signals:
                try:
                    line_plot, = self.ui.mplWidget.canvas.ax.plot(time_data, [self.data_store.data[signal][idx] for idx in i_range],
                                                                  color=self.colors[signal], label=signal)
                    lines.append(line_plot)
                except KeyError:
                    print(f"Error {signal}")
            leg = self.ui.mplWidget.canvas.ax.legend()
            self.lined = {}  # Will map legend lines to original lines.
            for legend_text, origline in zip(leg.get_texts(), lines):
                legend_text.set_picker(4)  # Enable picking on the legend line.
                self.lined[legend_text] = origline
                if legend_text.get_text() in self.plot_signal_status:
                    if self.plot_signal_status[legend_text.get_text()] is False:
                        self.switch_visible(legend_text, False)
        self.ui.mplWidget.canvas.draw()

    def on_pick(self, event):
        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        legend_text = event.artist
        origline = self.lined[legend_text]
        self.switch_visible(legend_text, not origline.get_visible())

    def on_mouse_event(self, event):
        if legend := self.ui.mplWidget.canvas.ax.get_legend():
            if not legend.get_window_extent().contains(event.x, event.y):
                if event.name == 'button_press_event' and event.button == mpl.backend_bases.MouseButton.LEFT:
                    if event.xdata < self.ui.mplWidget.canvas.ax.dataLim.xmin + 0.1 * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin):
                        delta_x = 0.5 * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin)
                        time_range_start = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmin - delta_x)
                        time_range_end = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmax - delta_x)
                        self.update_timerange(self.data_store, time_range_start, time_range_end)
                        self.update_plot()
                    elif event.xdata > self.ui.mplWidget.canvas.ax.dataLim.xmax - 0.1 * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin):
                        delta_x = 0.5 * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin)
                        time_range_start = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmin + delta_x)
                        time_range_end = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmax + delta_x)
                        self.update_timerange(self.data_store, time_range_start, time_range_end)
                        self.update_plot()
                    else:
                        self.span_rect[0] = event.xdata
                elif event.name == 'motion_notify_event':
                    if self.span_rect[0] is not None:
                        self.span_rect[1] = event.xdata
                        if self.aspan:
                            self.aspan.remove()
                        self.aspan = self.ui.mplWidget.canvas.ax.axvspan(self.span_rect[0], self.span_rect[1], color='red', alpha=0.3)  # TODO in settings
                        self.ui.mplWidget.canvas.draw()
                elif event.name == 'button_release_event' and event.button == mpl.backend_bases.MouseButton.LEFT:
                    if self.span_rect[0] is not None:
                        time_range_start = mdates.num2date(min(self.span_rect))
                        time_range_end = mdates.num2date(max(self.span_rect))
                        self.aspan.remove()
                        self.aspan = None
                        self.span_rect = [None, None]
                        self.update_timerange(self.data_store, time_range_start, time_range_end)
                        self.update_plot()

    def on_mouse_scroll_event(self, event):
        range = (2.0 if event.step > 0 else 0.5) * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin)
        center = (self.ui.mplWidget.canvas.ax.dataLim.xmin + self.ui.mplWidget.canvas.ax.dataLim.xmax) / 2.0
        time_range_start = mdates.num2date(center - range/2.0)
        time_range_end = mdates.num2date(center + range/2.0)
        self.update_timerange(self.data_store, time_range_start, time_range_end)
        self.update_plot()

    def update_timerange(self, datastore: DataStore, time_range_start: datetime, time_range_end: datetime):
        max_time = datastore.end_timestamp
        min_time = datastore.start_timestamp
        print(f"update_timerange: HET WAS from {datetime.fromtimestamp(self.time_range[0])} to {datetime.fromtimestamp(self.time_range[1])}")
        start_time = datetime.timestamp(time_range_start.replace(tzinfo=None))
        end_time = datetime.timestamp(time_range_end.replace(tzinfo=None))
        orig_time_range = self.time_range[1] - self.time_range[0]
        req_time_range = datetime.timestamp(time_range_end) - datetime.timestamp(time_range_start)
        if end_time > max_time:
            end_time = max_time
            if req_time_range == orig_time_range:
                start_time = end_time - orig_time_range
            else:
                print(f"new range req: {orig_time_range} vs {req_time_range}")
                if start_time < min_time:
                    start_time = min_time
        if start_time < min_time:
            start_time = min_time
            if req_time_range == orig_time_range:
                end_time = min_time + orig_time_range
            else:
                if end_time > max_time:
                    end_time = max_time
        print(f"          : HET WORDT from {datetime.fromtimestamp(start_time)} to {datetime.fromtimestamp(end_time)} request {time_range_start} {time_range_end}")
        self.time_range = (start_time, end_time)

    def switch_visible(self, legend_text, visible):
        origline = self.lined[legend_text]
        if legend_text.get_text() not in self.plot_signal_status or visible != origline.get_visible():
            self.plot_signal_status[legend_text.get_text()] = visible
            origline.set_visible(visible)
            # Change the alpha on the line in the legend, so we can see what lines have been toggled.
            legend_text.set_alpha(1.0 if visible else 0.2)
            self.ui.mplWidget.canvas.draw()

    def show_data_stores(self, data_stores):
        self.ui.datasourceComboBox.blockSignals(True)
        self.ui.datasourceComboBox.addItems([''] + [data_store.name for data_store in data_stores])
        self.ui.datasourceComboBox.blockSignals(False)

    def get_data_store_name(self):
        return self.ui.datasourceComboBox.currentText()

    def set_data_store_name(self, datastore_name: str):
        return self.ui.datasourceComboBox.setCurrentText(datastore_name)

    def show_signals_table(self, signal_check_states: dict[str, bool]):
        self.ui.signalsTableWidget.clearContents()
        self.ui.signalsTableWidget.setRowCount(len(signal_check_states))
        self.ui.signalsTableWidget.blockSignals(True)
        for row, signal in enumerate(signal_check_states):
            item = QTableWidgetItem(signal)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Unchecked if signal_check_states[signal] is False else Qt.CheckState.Checked)
            self.ui.signalsTableWidget.setItem(row, 0, item)
        self.ui.signalsTableWidget.blockSignals(False)

    def set_date_range(self, data_store: DataStore):
        if data_store.end_timestamp and data_store.start_timestamp:
            max_time = datetime.fromtimestamp(data_store.end_timestamp)
            min_time = datetime.fromtimestamp(data_store.start_timestamp)
            self.ui.fromDateTimeEdit.setDateTime(QDateTime(QDate(min_time.year, min_time.month, min_time.day), QTime(min_time.hour, min_time.minute, min_time.second)))
            self.ui.toDateTimeEdit.setDateTime(QDateTime(QDate(max_time.year, max_time.month, max_time.day), QTime(max_time.hour, max_time.minute, max_time.second)))

    def isSettingsSelected(self):
        return self.ui.settingsGroupBox.isChecked()

    def set_colors(self, colors: dict[str, str]):
        for name in colors:
            self.colors[name] = colors[name]
