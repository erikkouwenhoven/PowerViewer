import logging
import requests
from datetime import datetime
from Utils.settings import Settings


class ServerRequests:

    def __init__(self):
        pass

    def get_data(self):
        try:
            resp = requests.get(self.server_url(Settings().get_data_url()), headers={'Accept': 'application/json'})
        except ConnectionError as err:
            print(f"{err}")
            return None
        data = resp.json()
        logging.debug(f"Received data. # bytes: {len(resp.text)}")
        logging.debug(f"Number of samples received: {len(data['timestamp'])}")
        logging.debug(f"Time range: from {datetime.fromtimestamp(data['timestamp'][0])} to {datetime.fromtimestamp(data['timestamp'][-1])}")
        for i, t in enumerate(data['timestamp']):
            if i != 0:
                delta_t = t - t_prev
                if delta_t > 11:
                    print(f"delta = {delta_t} @ t = {datetime.fromtimestamp(t_prev)} > {datetime.fromtimestamp(t)}")
            t_prev = t
        if 'SOLAR' in data:
            data['SOLAR'] = [power/1000.0 if power is not None else 0.0 for power in data['SOLAR']]  # TODO
        return data

    @staticmethod
    def server_url(path):
        return f"{Settings().adapter()}{Settings().server()}:{Settings().port()}/{path}"
