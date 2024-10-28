from GUI.time_delay_view import TimeDelayView
from ServerRequests.server_requests import ServerRequests


class TimeDelayController:
    """ Controller voor de time delay dialog """

    def __init__(self, cross_corr, shift_in_samples, sampling_time):
        self.view = TimeDelayView()
        self.initialize(cross_corr, shift_in_samples, sampling_time, ServerRequests().get_shift_info())
        self.view.show()

    def initialize(self, cross_corr, shift_in_samples, sampling_time, server_shift_info):
        self.view.show_plot(cross_corr, shift_in_samples, sampling_time)
        self.view.show_server_shift_info(server_shift_info)
