import os
from datetime import datetime, timedelta
from GUI.Tools.time_format import data_range_fmt, plot_axis_fmt
from PyQt6 import uic
from PyQt6.QtCore import QDateTime, QDate, QTime, Qt
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMenu
from Utils.config import Config
import matplotlib.dates as mdates
import matplotlib as mpl
import mplcursors
from Algorithms.binary_search import b_search
from Models.data_store import DataStore


class GUIView(QMainWindow):
    """ View voor main screen """

    def __init__(self, plot_signal_status: dict[str, bool]):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(Config().getUiDirName(), Config().getMainScreenFileName()), self)
        self.colors = Config().get_colors()
        self.actionCallbacks = {}
        self.visibility_change_notifier = None
        self.data_store = None
        self.time_range = None  # tuple (start, end) of current plot
        self.plot_signal_status = plot_signal_status  # Dict mapping signal name to on/off status
        self.lines: dict[str, mpl.lines.Line2D] = {}  # Dict mapping legend text to line, enabling hiding/showing
        # self.lines = {}  # Dict mapping legend text to line, enabling hiding/showing
        self.span_rect = [None, None]
        self.aspan = None
        self.initialize()

    def initialize(self):
        self.setWindowTitle(f'{Config().getAppName()}  v.{Config().getVersion()}  (c) {Config().getAppInfo()}')
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
            if key == "calcSolarDelay":
                self.actionCallbacks['calcSolarDelay'] = value
            if key == "reload":
                self.actionCallbacks['reload'] = value
            if key == "saveData":
                self.actionCallbacks['saveData'] = value

    def set_change_notifier(self, visibility_change_notifier):
        self.visibility_change_notifier = visibility_change_notifier

    def connect_mpl_events(self):
        self.ui.mplWidget.canvas.mpl_connect('pick_event', self.on_pick_legend_text)
        self.ui.mplWidget.canvas.mpl_connect('button_press_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('button_release_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('motion_notify_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('scroll_event', self.on_mouse_scroll_event)

    def showContextMenu(self, position):
        menu = QMenu()
        settingsAction = menu.addAction("Settings")
        solarDelayAction = menu.addAction("Solar delay")
        reloadAction = menu.addAction("Reload")
        saveAction = menu.addAction("Save")
        action = menu.exec(self.ui.mplWidget.mapToGlobal(position))
        if action == settingsAction:
            self.actionCallbacks['showSettings']()
        elif action == solarDelayAction:
            self.actionCallbacks['calcSolarDelay']()
        elif action == reloadAction:
            self.actionCallbacks['reload']()
        elif action == saveAction:
            self.actionCallbacks['saveData']()

    def hideSettings(self):
        self.ui.settingsGroupBox.setChecked(False)
        self.ui.settingsGroupBox.setVisible(False)

    def showSettings(self):
        self.ui.settingsGroupBox.setChecked(True)
        self.ui.settingsGroupBox.setVisible(True)

    def getSignalsTable(self, data_store_name: str) -> dict[str, bool]:
        assert data_store_name == self.get_data_store_name()
        return {self.ui.signalsTableWidget.item(row, 0).text(): True if
            self.ui.signalsTableWidget.item(row, 0).checkState() == Qt.CheckState.Checked else False
            for row in range(self.ui.signalsTableWidget.rowCount())}

    def get_visibilities(self) -> dict[str, bool]:
        return self.plot_signal_status

    def show_data(self, time_range, data_store: DataStore):
        self.time_range = time_range
        self.data_store = data_store
        self.update_plot()

    def update_plot(self):
        lines = []  # the line plots
        self.ui.mplWidget.canvas.ax.clear()
        myFmt = mdates.DateFormatter(plot_axis_fmt)
        self.ui.mplWidget.canvas.ax.xaxis.set_major_formatter(myFmt)
        self.ui.mplWidget.canvas.ax.set_xlabel('time [.]')
        unit = self.data_store.get_dominant_unit()
        self.ui.mplWidget.canvas.ax.set_ylabel(f"Power [{list(unit)[0]}]")
        self.ui.mplWidget.canvas.ax.xaxis.set_major_formatter(
            mdates.ConciseDateFormatter(self.ui.mplWidget.canvas.ax.xaxis.get_major_locator()))
        if self.data_store:
            signals = [item for item in self.data_store.data if item != DataStore.c_TIMESTAMP_ID]
            i_range = range(b_search(self.data_store.data[DataStore.c_TIMESTAMP_ID], self.time_range[0]),
                            b_search(self.data_store.data[DataStore.c_TIMESTAMP_ID], self.time_range[1]))
            time_data = [datetime.fromtimestamp(self.data_store.data[DataStore.c_TIMESTAMP_ID][idx]) for idx in i_range]
            for signal in signals:
                try:
                    line_plot, = self.ui.mplWidget.canvas.ax.plot(time_data,
                                                                  [self.data_store.data[signal][idx] for idx in i_range],
                                                                  color=self.colors[signal], label=signal)
                    lines.append(line_plot)
                except KeyError:
                    print(f"Error {signal}")
            leg = self.ui.mplWidget.canvas.ax.legend()
            self.lines = {}  # Will map legend lines to original lines.
            for legend_text, origline in zip(leg.get_texts(), lines):
                legend_text.set_picker(4)  # Enable picking on the legend line.
                self.lines[legend_text] = origline
                try:
                    visibility = self.plot_signal_status[legend_text.get_text()]
                except TypeError:
                    visibility = True
                    self.plot_signal_status = {legend_text.get_text(): visibility}
                except KeyError:
                    visibility = True
                    self.plot_signal_status[legend_text.get_text()] = visibility
                self.switch_visible(legend_text, visibility)
        self.cursor = mplcursors.cursor(lines, multiple=False)
        self.cursor.connect("add", self.on_add)
        self.ui.mplWidget.canvas.draw()

    def on_add(self, selection):
        for sel in self.cursor.selections:
            if sel != selection:
                self.cursor.remove_selection(sel)

    def on_pick_legend_text(self, event):
        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        legend_text = event.artist
        origline = self.lines[legend_text]
        self.switch_visible(legend_text, not origline.get_visible())
        self.visibility_change_notifier()
        self.ui.mplWidget.canvas.draw()

    def on_mouse_event(self, event):
        if legend := self.ui.mplWidget.canvas.ax.get_legend():
            if not legend.get_window_extent().contains(event.x, event.y):
                if event.name == 'button_press_event' and event.button == mpl.backend_bases.MouseButton.LEFT:
                    x_range = self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin
                    if event.xdata < self.ui.mplWidget.canvas.ax.dataLim.xmin + Config().getPanPlotRelativePosition() * x_range:
                        delta_x = 0.5 * x_range
                        time_range_start = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmin - delta_x)
                        time_range_end = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmax - delta_x)
                        self.update_timerange(self.data_store, time_range_start, time_range_end, keep_range=True)
                        self.update_plot()
                    elif event.xdata > self.ui.mplWidget.canvas.ax.dataLim.xmax - Config().getPanPlotRelativePosition() * x_range:
                        delta_x = 0.5 * x_range
                        time_range_start = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmin + delta_x)
                        time_range_end = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmax + delta_x)
                        self.update_timerange(self.data_store, time_range_start, time_range_end, keep_range=True)
                        self.update_plot()
                    else:
                        self.span_rect[0] = event.xdata
                elif event.name == 'motion_notify_event':
                    if self.span_rect[0] is not None:
                        self.span_rect[1] = event.xdata
                        if self.aspan:
                            self.aspan.remove()
                        self.aspan = self.ui.mplWidget.canvas.ax.axvspan(self.span_rect[0], self.span_rect[1],
                                                                         color='red',
                                                                         alpha=Config().getSelectionTranslucency())
                        self.ui.mplWidget.canvas.draw()
                elif event.name == 'button_release_event' and event.button == mpl.backend_bases.MouseButton.LEFT:
                    if self.span_rect[0] is not None:
                        try:
                            time_range_start = mdates.num2date(min(self.span_rect))
                            time_range_end = mdates.num2date(max(self.span_rect))
                            self.update_timerange(self.data_store, time_range_start, time_range_end, force_range=True)
                            self.update_plot()
                        except TypeError:  # mogelijk zijn er None-waarden in span_rect
                            pass
                        if self.aspan:
                            self.aspan.remove()
                            self.aspan = None
                        self.span_rect = [None, None]

    def on_mouse_scroll_event(self, event):
        range = (2.0 if event.step > 0 else 0.5) * (
                self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin)
        center = (self.ui.mplWidget.canvas.ax.dataLim.xmin + self.ui.mplWidget.canvas.ax.dataLim.xmax) / 2.0
        time_range_start = mdates.num2date(center - range / 2.0)
        time_range_end = mdates.num2date(center + range / 2.0)
        self.update_timerange(self.data_store, time_range_start, time_range_end)
        self.update_plot()

    def update_timerange(self, datastore: DataStore, time_range_start: datetime, time_range_end: datetime,
                         keep_range: bool = False, force_range: bool = False):
        """
        Past de time_range aan die in gebruik is voor de plot op basis van de hier aangevraagde grenzen.
        Daarbij worden de grenzen van de beschikbare data in acht genomen. Verder:
        - als keep_range is True dan wordt de huidige range in stand gehouden. In gebruik bij panning. Dit vookomt dat
          bij panning de range verandert.
        - de range wordt begrensd volgens de geconfigureerde waarde, tenzij force_range is True. In gebruik bij selectie.
        - als de range-begrenzing aangrijpt is er een uitzondering bij vergroten van de range.
        """
        req_time_range = time_range_end - time_range_start
        actual_time_range = datetime.fromtimestamp(self.time_range[1]) - datetime.fromtimestamp(self.time_range[0])
        max_time = datastore.end_timestamp
        min_time = datastore.start_timestamp
        if req_time_range < timedelta(minutes=Config().getMinPlottedTimeRangeInMinutes()):
            if force_range is False:
                if keep_range is False and req_time_range <= actual_time_range:
                    return
            else:
                avail_time_range = min(timedelta(minutes=Config().getMinPlottedTimeRangeInMinutes()),
                                       datetime.fromtimestamp(max_time) - datetime.fromtimestamp(min_time))
                time_range_start -= (avail_time_range - req_time_range) / 2
                time_range_end += (avail_time_range - req_time_range) / 2
        start_time = datetime.timestamp(time_range_start.replace(tzinfo=None))
        end_time = datetime.timestamp(time_range_end.replace(tzinfo=None))
        orig_time_range = self.time_range[1] - self.time_range[0]
        if end_time > max_time:
            end_time = max_time
            if keep_range is True:
                start_time = end_time - orig_time_range
        if start_time < min_time:
            start_time = min_time
            if keep_range is True:
                end_time = min_time + orig_time_range
        self.time_range = (start_time, end_time)

    def switch_visible(self, legend_text, visible):
        origline = self.lines[legend_text]
        if visible != origline.get_visible():
            self.plot_signal_status[legend_text.get_text()] = visible
            origline.set_visible(visible)
            # Change the alpha on the line in the legend, so we can see what lines have been toggled.
            legend_text.set_alpha(1.0 if visible else 0.2)
            self.visibility_change_notifier()

    def show_data_stores(self, data_stores: list[DataStore]):
        self.ui.datasourceComboBox.blockSignals(True)
        self.ui.datasourceComboBox.addItems([''] + [data_store.name for data_store in data_stores])
        self.ui.datasourceComboBox.blockSignals(False)

    def get_data_store_name(self) -> str:
        return self.ui.datasourceComboBox.currentText()

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

    def set_date_range(self, data_store: DataStore):
        if data_store.end_timestamp and data_store.start_timestamp:
            max_time = datetime.fromtimestamp(data_store.end_timestamp)
            min_time = datetime.fromtimestamp(data_store.start_timestamp)
            self.ui.fromDateTimeLabel.setText(min_time.strftime(data_range_fmt))
            self.ui.toDateTimeLabel.setText(max_time.strftime(data_range_fmt))

    def isSettingsSelected(self) -> bool:
        return self.ui.settingsGroupBox.isChecked()

    def append_colors(self, colors: dict[str, str]) -> None:
        for name in colors:
            self.colors[name] = colors[name]
