import os
from PyQt6.QtWidgets import QDialog
from PyQt6 import uic
from Utils.config import Config


class TimeDelayView(QDialog):
    """ View voor time delay dialog """

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(Config().getUiDirName(), Config().getTimeDelayDialogFileName()), self)
        self.initialize()

    def initialize(self):
        pass

    def show_plot(self, cross_corr, shift_in_samples, sampling_time):
        t = cross_corr[0]
        cc = cross_corr[1]
        self.ui.mplWidget.canvas.ax.bar(t, cc)
        self.ui.mplWidget.canvas.ax.set_ylim(min(cc) - 0.1*(max(cc) - min(cc)), max(cc) + 0.1*(max(cc) - min(cc)))
        self.ui.mplWidget.canvas.ax.axvline(shift_in_samples, color='red')
        self.ui.mplWidget.canvas.draw()
        self.display_shift_in_samples(shift_in_samples)
        self.display_shift_in_seconds(shift_in_samples * sampling_time)
        self.display_sampling_time(sampling_time)

    def display_shift_in_samples(self, shift_in_samples):
        self.ui.shiftSamplesLineEdit.setText(f"{shift_in_samples:.1f}")

    def display_shift_in_seconds(self, shift_in_seconds):
        self.ui.shiftSecondsLineEdit.setText(f"{shift_in_seconds:.1f}")

    def display_sampling_time(self, sampling_time):
        self.ui.samplingTimeLineEdit.setText(f"{sampling_time:.1f}")

    def show_server_shift_info(self, server_shift_info: dict):
        self.ui.shiftSecondsLineEdit.setToolTip(str(server_shift_info))
