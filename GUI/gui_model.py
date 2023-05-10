from datetime import datetime, timedelta
from dateutil import tz
from ServerRequests.server_requests import ServerRequests
from requests.exceptions import ConnectionError


class GUIModel:

    def __init__(self, view):
        self.view = view
        self.time_range = self.init_time_range()
        self.data = None

    def init_time_range(self):
        now = datetime.now(tz.gettz('Europe/Amsterdam'))
        time_range = [now - timedelta(hours=3), now]  # TODO naar Settings
        self.view.show_time(time_range)
        return time_range

    def acquire_data(self, mode):
        try:
            self.data = ServerRequests().get_data(f'?mode={mode}')
        except ConnectionError as err:
            print(f"ConnectionError: {err}")
            return
        except Exception as e:
            print(e)
        if mode == 'realtime':
            t_prev = None
            for i, t in enumerate(self.data['timestamp']):
                if i != 0:
                    delta_t = t - t_prev
                    if delta_t > 11:
                        print(f"delta = {delta_t} @ t = {datetime.fromtimestamp(t_prev)} > {datetime.fromtimestamp(t)}")
                t_prev = t
        self.view.show_data(self.data, self.time_range)

    def get_data(self):
        return self.data

    def set_time_range(self, time_range):
        self.time_range = time_range
        self.view.show_time(time_range)
        self.view.show_data(self.data, self.time_range)

    def get_time_range(self):
        return self.time_range
