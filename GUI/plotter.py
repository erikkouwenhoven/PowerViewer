from typing import Type, Optional
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib as mpl
import mplcursors
from GUI.Tools.mplwidget import MplWidget
from Utils.config import Config
from GUI.Tools.time_format import plot_axis_fmt
from Models.data_store import DataStore
from Models.data_view import DataView
from Algorithms.binary_search import interval_to_range
from Utils.unit_standardizer import UnitStandardizer


class Plotter:
    
    def __init__(self, mpl_widget: Type[MplWidget]):
        self.mpl_widget: Type[MplWidget] = mpl_widget
        self.data_view: DataView = None
        self.visibility_change_notifier = None
        self.redraw_notifier = None
        self.colors = Config().get_colors()
        self.time_range = None  # tuple (start, end) of current plot
        self.signal_visibilities: Optional[dict[str, bool]] = None  # Dict mapping signal name to on/off status
        self.lines: dict[str, mpl.lines.Line2D] = {}  # Dict mapping legend text to line, enabling hiding/showing
        self.span_rect = [None, None]
        self.aspan = None
        self.cursor = None
        self.twin_axes = None
        self.connect_mpl_events()

    def connect_mpl_events(self):
        self.mpl_widget.canvas.mpl_connect('pick_event', self.on_pick_legend_text)
        self.mpl_widget.canvas.mpl_connect('button_press_event', self.on_mouse_event)
        self.mpl_widget.canvas.mpl_connect('button_release_event', self.on_mouse_event)
        self.mpl_widget.canvas.mpl_connect('motion_notify_event', self.on_mouse_event)
        self.mpl_widget.canvas.mpl_connect('scroll_event', self.on_mouse_scroll_event)

    def set_visibility_change_notifier(self, visibility_change_notifier):
        self.visibility_change_notifier = visibility_change_notifier

    def set_signal_visibiities(self, signal_visibilities: dict[str, bool]):
        self.signal_visibilities = signal_visibilities

    def set_redraw_notifier(self, redraw_notifier):
        self.redraw_notifier = redraw_notifier

    def update_plot(self):
        lines = []  # the line plots
        self.mpl_widget.canvas.ax.clear()
        self.mpl_widget.canvas.ax.xaxis.set_major_formatter(mdates.DateFormatter(plot_axis_fmt))
        self.mpl_widget.canvas.ax.set_xlabel('time')
        units = None
        for data_store in self.data_view.get_data_stores():
            units = data_store.combine_signals_grouped_units(units)
        if units:
            axes_signals = {}
            if self.twin_axes and len(units) <= 1:
                self.twin_axes.remove()
                self.twin_axes = None
            for i_unit, unit in enumerate(units):
                if i_unit == 0:
                    if self.twin_axes:
                        self.twin_axes.clear()  # kennelijk nodig omdat anders problemen optreden bij bijv. zooming
                    self.mpl_widget.canvas.ax.set_ylabel(f"{UnitStandardizer().get_quantity(unit)} [{unit}]")

                    axes_signals = {signal.name: self.mpl_widget.canvas.ax for signal in units[unit]}
                elif i_unit == 1:
                    if self.twin_axes is None:
                        self.twin_axes = self.mpl_widget.canvas.ax.twinx()
                    else:
                        self.twin_axes.clear()  # kennelijk nodig omdat anders problemen optreden bij bijv. zooming
                    self.twin_axes.set_ylabel(f"{UnitStandardizer().get_quantity(unit)} [{unit}]")
                    axes_signals = axes_signals | {signal.name: self.twin_axes for signal in units[unit]}
                else:
                    raise RuntimeError("Niet meer dan 2 assen mogelijk")
        self.mpl_widget.canvas.ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(self.mpl_widget.canvas.ax.xaxis.get_major_locator()))
        for data_store in self.data_view.get_data_stores():
            if data_store and data_store.data and (t := data_store.data[DataStore.c_TIMESTAMP_ID]):
                i_range = interval_to_range(t, self.time_range[0], self.time_range[1])
                time_data = [datetime.fromtimestamp(data_store.data[DataStore.c_TIMESTAMP_ID][idx]) for idx in i_range]
                signals = [item for item in data_store.data if item in self.data_view.get_signals(data_store) and item != DataStore.c_TIMESTAMP_ID]
                for signal in signals:
                    try:
                        ax = axes_signals[signal] if signal in axes_signals else self.mpl_widget.canvas.ax  # de else heeft betrekking op derived signals
                        signal_data = [data_store.data[signal][idx] for idx in i_range]
                        if signal in Config().getBarPlotSignals():
                            ax.bar(time_data, signal_data, color=self.colors[signal], label=signal, width=timedelta(minutes=30))
                        else:
                            line_plot, = ax.plot(time_data, signal_data, color=self.colors[signal], label=signal,
                                                 marker='o' if signal in Config().getSymbolPlotSignals() else '')
                            lines.append(line_plot)
                    except KeyError:
                        print(f"Error {signal}")
                leg = self.mpl_widget.canvas.ax.legend(handles=lines) if self.twin_axes is None else self.twin_axes.legend(handles=lines)
                self.lines = {}  # Will map legend lines to original lines.
                for legend_text, origline in zip(leg.get_texts(), lines):
                    legend_text.set_picker(4)  # Enable picking on the legend line.
                    self.lines[legend_text] = origline
                    try:
                        visibility = self.signal_visibilities[legend_text.get_text()]
                    except TypeError:
                        visibility = True
                        self.signal_visibilities = {legend_text.get_text(): visibility}
                    except KeyError:
                        visibility = True
                        self.signal_visibilities[legend_text.get_text()] = visibility
                    self.switch_visible(legend_text, visibility)
        if self.twin_axes:
            self.twin_axes.autoscale()
            print("autoscale")
        if self.cursor:
            self.cursor.remove()
        self.cursor = mplcursors.cursor(lines, multiple=False)
        self.mpl_widget.canvas.draw()
        if self.redraw_notifier:
            self.redraw_notifier()

    def on_pick_legend_text(self, event):
        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        try:
            legend_text = event.artist
            try:
                origline = self.lines[legend_text]
                self.switch_visible(legend_text, not origline.get_visible())
                self.mpl_widget.canvas.draw()
            except KeyError:  # the mplcursor is a legend too
                pass
        except AttributeError:
            pass  # no artist

    def on_mouse_event(self, event):
        if legend := (self.twin_axes.get_legend() if self.twin_axes else self.mpl_widget.canvas.ax.get_legend()):
            if not legend.get_window_extent().contains(event.x, event.y):
                if event.name == 'button_press_event' and event.button == mpl.backend_bases.MouseButton.LEFT:
                    x_range = self.mpl_widget.canvas.ax.dataLim.xmax - self.mpl_widget.canvas.ax.dataLim.xmin
                    if event.xdata < self.mpl_widget.canvas.ax.dataLim.xmin + Config().getPanPlotRelativePosition() * x_range:
                        delta_x = 0.5 * x_range
                        time_range_start = mdates.num2date(self.mpl_widget.canvas.ax.dataLim.xmin - delta_x)
                        time_range_end = mdates.num2date(self.mpl_widget.canvas.ax.dataLim.xmax - delta_x)
                        self.update_timerange(self.data_view.get_data_stores(), time_range_start, time_range_end, keep_range=True)
                        self.update_plot()
                    elif event.xdata > self.mpl_widget.canvas.ax.dataLim.xmax - Config().getPanPlotRelativePosition() * x_range:
                        delta_x = 0.5 * x_range
                        time_range_start = mdates.num2date(self.mpl_widget.canvas.ax.dataLim.xmin + delta_x)
                        time_range_end = mdates.num2date(self.mpl_widget.canvas.ax.dataLim.xmax + delta_x)
                        self.update_timerange(self.data_view.get_data_stores(), time_range_start, time_range_end, keep_range=True)
                        self.update_plot()
                    else:
                        self.span_rect[0] = event.xdata
                elif event.name == 'motion_notify_event':
                    if self.span_rect[0] is not None:
                        self.span_rect[1] = event.xdata
                        if self.aspan:
                            self.aspan.remove()
                        self.aspan = self.mpl_widget.canvas.ax.axvspan(self.span_rect[0], self.span_rect[1],
                                                                       color='red',
                                                                       alpha=Config().getSelectionTranslucency())
                        self.mpl_widget.canvas.draw()
                elif event.name == 'button_release_event' and event.button == mpl.backend_bases.MouseButton.LEFT:
                    if self.span_rect[0] is not None:
                        try:
                            time_range_start = mdates.num2date(min(self.span_rect))
                            time_range_end = mdates.num2date(max(self.span_rect))
                            self.update_timerange(self.data_view.get_data_stores(), time_range_start, time_range_end, force_range=True)
                            self.update_plot()
                        except TypeError:  # mogelijk zijn er None-waarden in span_rect
                            pass
                        if self.aspan:
                            self.aspan.remove()
                            self.aspan = None
                        self.span_rect = [None, None]

    def on_mouse_scroll_event(self, event):
        xmin = self.mpl_widget.canvas.ax.dataLim.xmin
        xmax = self.mpl_widget.canvas.ax.dataLim.xmax
        if self.twin_axes:
            xmin = min(xmin, self.twin_axes.dataLim.xmin)
            xmax = max(xmax, self.twin_axes.dataLim.xmax)
        range = (2.0 if event.step > 0 else 0.5) * (xmax - xmin)
        center = (self.mpl_widget.canvas.ax.dataLim.xmin + self.mpl_widget.canvas.ax.dataLim.xmax) / 2.0
        time_range_start = mdates.num2date(center - range / 2.0)
        time_range_end = mdates.num2date(center + range / 2.0)
        self.update_timerange(self.data_view.get_data_stores(), time_range_start, time_range_end)
        self.update_plot()

    def update_timerange(self, data_stores: list[DataStore], time_range_start: datetime, time_range_end: datetime,
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
        max_time = min(data_store.end_timestamp for data_store in data_stores)
        min_time = max(data_store.start_timestamp for data_store in data_stores)
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
            self.signal_visibilities[legend_text.get_text()] = visible
            origline.set_visible(visible)
            # Change the alpha on the line in the legend, so we can see what lines have been toggled.
            legend_text.set_alpha(1.0 if visible else 0.2)
            self.visibility_change_notifier()

    def get_displayed_signals(self):
        return [signal for signal in self.signal_visibilities if self.signal_visibilities[signal] is True]

    def append_colors(self, colors: dict[str, str]) -> None:
        for name in colors:
            self.colors[name] = colors[name]

