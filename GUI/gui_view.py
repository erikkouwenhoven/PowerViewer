import os
from datetime import datetime, timedelta
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

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(Settings().getUiDirName(), Settings().getMainScreenFileName()), self)
        self.setWindowTitle(f'{Settings().getAppName()}  v.{Settings().getVersion()}  (c) {Settings().getAppInfo()}')
        self.plot_signal_status = {}  # Dict mapping signal name to on/off status
        self.lined = {}  # Dict mapping legend text to line, enabling hiding/showing
        self.initialize()

    def connectEvents(self, commandDict):
        for key, value in commandDict.items():
            if key == "nuSelected":
                self.ui.nuPushButton.clicked.connect(value)
            if key == "fromChanged":
                self.ui.fromDateTimeEdit.dateTimeChanged.connect(value)
            if key == "toChanged":
                self.ui.toDateTimeEdit.dateTimeChanged.connect(value)

    def initialize(self):
        self.initTimeFrame()

    def initTimeFrame(self):
        dt = datetime.now() - timedelta(hours=2)  # TODO naar Settings
        self.ui.fromDateTimeEdit.setDateTime(QDateTime(QDate(dt.year, dt.month, dt.day), QTime(dt.hour, dt.minute, dt.second)))
        dt = datetime.now()
        self.ui.toDateTimeEdit.setDateTime(QDateTime(QDate(dt.year, dt.month, dt.day), QTime(dt.hour, dt.minute, dt.second)))

    def show_data(self, data):
        lines = []  # the line plots
        self.ui.mplWidget.canvas.ax.clear()
        myFmt = mdates.DateFormatter('%H:%M')
        self.ui.mplWidget.canvas.ax.xaxis.set_major_formatter(myFmt)
        self.ui.mplWidget.canvas.ax.set_xlabel('time [.]')
        self.ui.mplWidget.canvas.ax.set_ylabel('Power [W]')
        if data:
            signals = [item for item in data if item != 'timestamp']

            i_range = range(b_search(data['timestamp'], self.getFromQDateTime(self.ui.fromDateTimeEdit.dateTime()).timestamp()),
                            b_search(data['timestamp'], self.getFromQDateTime(self.ui.toDateTimeEdit.dateTime()).timestamp()))
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
        self.ui.mplWidget.canvas.mpl_connect('pick_event', self.on_pick)
        self.ui.mplWidget.canvas.draw()

    def on_pick(self, event):
        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        legend_text = event.artist
        origline = self.lined[legend_text]
        self.switch_visible(legend_text, not origline.get_visible())

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
