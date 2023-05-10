import logging
import requests
from datetime import datetime
from Utils.settings import Settings


class ServerRequests:

    def __init__(self):
        pass

    def get_data(self, mode):
        resp = requests.get(self.server_url(Settings().get_data_url()) + mode, headers={'Accept': 'application/json'})
        data = resp.json()
        logging.debug(f"Received data. # bytes: {len(resp.text)}")
        logging.debug(f"Number of samples received: {len(data['timestamp'])}")
        logging.debug(f"Time range: from {datetime.fromtimestamp(data['timestamp'][0])} to {datetime.fromtimestamp(data['timestamp'][-1])}")
        if 'SOLAR' in data:
            data['SOLAR'] = [power/1000.0 if power is not None else 0.0 for power in data['SOLAR']]  # TODO
        return data

    @staticmethod
    def server_url(path):
        return f"{Settings().adapter()}{Settings().server()}:{Settings().port()}/{path}"
