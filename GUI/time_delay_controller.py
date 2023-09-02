from Utils.settings import Settings
from Utils.config import Config
from GUI.time_delay_view import TimeDelayView


class TimeDelayController:
    """ Controller voor de time delay dialog """

    def __init__(self, cross_corr, shift):
        self.view = TimeDelayView()
        self.initialize(cross_corr, shift)
        self.view.show()

    def initialize(self, cross_corr, shift):
        self.view.show_plot(cross_corr, shift)

