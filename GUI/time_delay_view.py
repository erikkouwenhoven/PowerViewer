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

    def show_plot(self, cross_corr, shift):
        t = cross_corr[0]
        cc = cross_corr[1]
        self.ui.mplWidget.canvas.ax.bar(t, cc)
        self.ui.mplWidget.canvas.ax.set_ylim(min(cc) - 0.1*(max(cc) - min(cc)), max(cc) + 0.1*(max(cc) - min(cc)))
        self.ui.mplWidget.canvas.ax.axvline(shift, color='red')
        self.ui.mplWidget.canvas.draw()
