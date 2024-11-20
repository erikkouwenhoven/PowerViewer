from datetime import datetime
import math
from GUI.exp_decay_view import ExponentialDecayView
from Models.data_view import DataView
from Algorithms.binary_search import interval_to_range
from Algorithms.curve_fit import CurveFitFloatingExponent


class ExponentialDecayController:

    def __init__(self, data_view: DataView, signals: list[str], time_range: tuple[float, float]):
        self.view = ExponentialDecayView()
        self.coords = self.extract_coordinates(data_view, signals, time_range)
        self.title, self.ylabel = self.extract_labeling(data_view, signals)
        self.view.connectEvents(
            {
                'fitButtonPressed': self.fit,
            }
        )
        if self.coords:
            self.fit()
        self.view.exec()

    def extract_coordinates(self, data_view: DataView, signals: list[str], time_range: tuple[float, float]) -> tuple[list[datetime], list[float]]:
        for data_store in data_view.get_data_stores():
            for signal in data_view.get_signals(data_store):
                if signal in signals:
                    if i_range := interval_to_range(data_store.get_time_signal().data, time_range[0], time_range[1]):
                        time_data = [datetime.fromtimestamp(data_store.get_time_signal().data[idx]) for idx in i_range]
                        signal_data = [data_store.get_signal(signal)[idx] for idx in i_range]
                        return time_data, signal_data

    def extract_labeling(self, data_view: DataView, signals: list[str]) -> tuple[str, str]:
        for data_store in data_view.get_data_stores():
            for signal in data_view.get_signals(data_store):
                if signal in signals:
                    return data_store.name, signal

    def fit(self):
        time_stamps = [datetime.timestamp(t) for t in self.coords[0]]
        time_stamps_min = min(time_stamps)
        time_stamps_fromzero = [t - time_stamps_min for t in time_stamps]
        curve_fit = CurveFitFloatingExponent(time_stamps_fromzero, self.coords[1])
        curve_fit.solve()
        parms = curve_fit.getParameters()
        xfit = range(math.floor(time_stamps_fromzero[0]), math.ceil(time_stamps_fromzero[-1]),
                     int((time_stamps_fromzero[-1] - time_stamps_fromzero[0])/20.0))  # 20 stappen
        yfit = [CurveFitFloatingExponent.func(x, parms) for x in xfit]
        self.view.show_plot(self.coords, title=self.title, ylabel=self.ylabel, fit_coords=([datetime.fromtimestamp(x + time_stamps_min) for x in xfit], yfit))
        self.view.show_halftime(curve_fit.half_value_time() / 3600.0)
        self.view.show_ampl(parms[0])
        self.view.show_level(parms[2])
