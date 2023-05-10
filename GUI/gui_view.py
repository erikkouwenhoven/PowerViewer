import os
from datetime import datetime
from PyQt6 import uic
from PyQt6.QtCore import QDateTime, QDate, QTime
from PyQt6.QtWidgets import QMainWindow
from Utils.settings import Settings
import matplotlib.dates as mdates


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

    def __init__(self, time_range_changed):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(Settings().getUiDirName(), Settings().getMainScreenFileName()), self)
        self.setWindowTitle(f'{Settings().getAppName()}  v.{Settings().getVersion()}  (c) {Settings().getAppInfo()}')
        self.time_range_changed = time_range_changed
        self.plot_signal_status = {}  # Dict mapping signal name to on/off status
        self.lined = {}  # Dict mapping legend text to line, enabling hiding/showing
        self.span_rect = [None, None]
        self.aspan = None

    def connectEvents(self, commandDict):
        for key, value in commandDict.items():
            if key == "nuSelected":
                self.ui.nuPushButton.clicked.connect(value)
            if key == "dagenSelected":
                self.ui.dagenPushButton.clicked.connect(value)
            if key == "timeRangeChanged":
                self.ui.fromDateTimeEdit.dateTimeChanged.connect(value)
                self.ui.toDateTimeEdit.dateTimeChanged.connect(value)

    def show_time(self, time_range):
        self.ui.fromDateTimeEdit.setDateTime(QDateTime(QDate(time_range[0].year, time_range[0].month, time_range[0].day), QTime(time_range[0].hour, time_range[0].minute, time_range[0].second)))
        self.ui.toDateTimeEdit.setDateTime(QDateTime(QDate(time_range[1].year, time_range[1].month, time_range[1].day), QTime(time_range[1].hour, time_range[1].minute, time_range[1].second)))

    def get_time_range(self):
        return [self.getFromQDateTime(self.ui.fromDateTimeEdit.dateTime()),
                self.getFromQDateTime(self.ui.toDateTimeEdit.dateTime())]

    def show_data(self, data, time_range):
        lines = []  # the line plots
        self.ui.mplWidget.canvas.ax.clear()
        myFmt = mdates.DateFormatter('%H:%M')
        self.ui.mplWidget.canvas.ax.xaxis.set_major_formatter(myFmt)
        self.ui.mplWidget.canvas.ax.set_xlabel('time [.]')
        self.ui.mplWidget.canvas.ax.set_ylabel('Power [W]')
        if data:
            signals = [item for item in data if item != 'timestamp']

            i_range = range(b_search(data['timestamp'], (time_range[0]).timestamp()),
                            b_search(data['timestamp'], (time_range[1]).timestamp()))
            time_data = [datetime.fromtimestamp(data['timestamp'][idx]) for idx in i_range]
            for signal in signals:
                line_plot, = self.ui.mplWidget.canvas.ax.plot(time_data, [data[signal][idx] for idx in i_range],
                                                              color=self.colors[signal], label=signal)
                lines.append(line_plot)
            leg = self.ui.mplWidget.canvas.ax.legend()
            self.lined = {}  # Will map legend lines to original lines.
            for legend_text, origline in zip(leg.get_texts(), lines):
                legend_text.set_picker(4)  # Enable picking on the legend line.
                self.lined[legend_text] = origline
                if legend_text.get_text() in self.plot_signal_status:
                    if self.plot_signal_status[legend_text.get_text()] is False:
                        self.switch_visible(legend_text, False)
        self.connect_events()
        self.ui.mplWidget.canvas.draw()

    def connect_events(self):
        self.ui.mplWidget.canvas.mpl_connect('pick_event', self.on_pick)
        self.ui.mplWidget.canvas.mpl_connect('button_press_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('button_release_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('motion_notify_event', self.on_mouse_event)
        self.ui.mplWidget.canvas.mpl_connect('scroll_event', self.on_mouse_scroll_event)


    def on_pick(self, event):
        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        legend_text = event.artist
        origline = self.lined[legend_text]
        self.switch_visible(legend_text, not origline.get_visible())

    def on_mouse_event(self, event):
        if not self.ui.mplWidget.canvas.ax.get_legend().get_window_extent().contains(event.x, event.y):
            if event.name == 'button_press_event':
                if event.xdata < self.ui.mplWidget.canvas.ax.dataLim.xmin + 0.1 * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin):
                    delta_x = 0.5 * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin)
                    time_range_start = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmin - delta_x)
                    time_range_end = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmax - delta_x)
                    self.time_range_changed([time_range_start, time_range_end])
                elif event.xdata > self.ui.mplWidget.canvas.ax.dataLim.xmax - 0.1 * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin):
                    delta_x = 0.5 * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin)
                    time_range_start = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmin + delta_x)
                    time_range_end = mdates.num2date(self.ui.mplWidget.canvas.ax.dataLim.xmax + delta_x)
                    self.time_range_changed([time_range_start, time_range_end])
                else:
                    self.span_rect[0] = event.xdata
            elif event.name == 'motion_notify_event':
                if self.span_rect[0] is not None:
                    self.span_rect[1] = event.xdata
                    if self.aspan:
                        self.aspan.remove()
                    self.aspan = self.ui.mplWidget.canvas.ax.axvspan(self.span_rect[0], self.span_rect[1], color='red', alpha=0.3)  # TODO in settings
                    self.ui.mplWidget.canvas.draw()
            elif event.name == 'button_release_event':
                if self.span_rect[0] is not None:
                    time_range_start = mdates.num2date(self.span_rect[0])
                    time_range_end = mdates.num2date(self.span_rect[1])
                    self.aspan.remove()
                    self.aspan = None
                    self.span_rect = [None, None]
                    self.time_range_changed([time_range_start, time_range_end])

    def on_mouse_scroll_event(self, event):
        range = (2.0 if event.step > 0 else 0.5) * (self.ui.mplWidget.canvas.ax.dataLim.xmax - self.ui.mplWidget.canvas.ax.dataLim.xmin)
        center = (self.ui.mplWidget.canvas.ax.dataLim.xmin + self.ui.mplWidget.canvas.ax.dataLim.xmax) / 2.0
        time_range_start = mdates.num2date(center - range/2.0)
        time_range_end = mdates.num2date(center + range/2.0)
        self.time_range_changed([time_range_start, time_range_end])

    def switch_visible(self, legend_text, visible):
        origline = self.lined[legend_text]
        if legend_text.get_text() not in self.plot_signal_status or visible != origline.get_visible():
            self.plot_signal_status[legend_text.get_text()] = visible
            origline.set_visible(visible)
            # Change the alpha on the line in the legend, so we can see what lines have been toggled.
            legend_text.set_alpha(1.0 if visible else 0.2)
            self.ui.mplWidget.canvas.draw()

    def getFromQDateTime(self, qdatetime):
        return datetime(qdatetime.date().year(), qdatetime.date().month(), qdatetime.date().day(),
                        qdatetime.time().hour(), qdatetime.time().minute(), qdatetime.time().second())


def b_search(array, value):
    lo = 0
    hi = len(array) - 1
    while lo < hi:
        m = int((lo + hi) / 2)
        if array[m] < value:
            lo = m + 1
        elif array[m] > value:
            hi = m - 1
        elif array[m] == value:
            return m
        if hi - lo <= 1:
            return lo
