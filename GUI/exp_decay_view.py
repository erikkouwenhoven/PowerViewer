import os
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import QDialog
from PyQt6 import uic
import matplotlib.dates as mdates
from Utils.config import Config


class ExponentialDecayView(QDialog):

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi(os.path.join(Config().getUiDirName(), Config().getExpDecayDialogFileName()), self)
        self.initialize()

    def initialize(self):
        pass

    def connectEvents(self, command_dict):
        for key, value in command_dict.items():
            if key == "fitButtonPressed":
                self.ui.fitPushButton.clicked.connect(value)

    def show_plot(self, coords: tuple[list[datetime], list[float]], title: str, ylabel: str, fit_coords: Optional[tuple[list[datetime], list[float]]] = None):
        self.ui.mpl_widget.canvas.ax.clear()
        self.ui.mpl_widget.canvas.ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(self.ui.mpl_widget.canvas.ax.xaxis.get_major_locator()))
        self.ui.mpl_widget.canvas.ax.plot(coords[0], coords[1], 'bo')
        self.ui.mpl_widget.canvas.ax.set_xlabel('time')
        self.ui.mpl_widget.canvas.ax.set_ylabel(ylabel)
        self.ui.mpl_widget.canvas.ax.set_title(title)
        if fit_coords:
            self.ui.mpl_widget.canvas.ax.plot(fit_coords[0], fit_coords[1], color='red', linestyle=':')
        self.ui.mpl_widget.canvas.draw()

    def show_halftime(self, half_time):
        self.ui.halftimeLineEdit.setText(f"{half_time:.2f}")

    def show_ampl(self, amplitude):
        self.ui.amplitudeLineEdit.setText(f"{amplitude:.1f}")

    def show_level(self, level):
        self.ui.levelLineEdit.setText(f"{level:.1f}")
