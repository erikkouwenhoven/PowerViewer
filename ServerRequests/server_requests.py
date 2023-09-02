import logging
import requests
import json
from datetime import datetime
from Utils.config import Config


class ServerRequests:

    def __init__(self):
        pass

    def get_data(self, mode):
        try:
            resp = requests.get(self.server_url(Config().get_data_url()) + mode, headers={'Accept': 'application/json'})
            data = resp.json()
            logging.debug(f"Received data. # bytes: {len(resp.text)}")
        except Exception:
            with open('sample.json', 'r') as openfile:
                data = json.load(openfile)
            logging.debug("Got data from file")

        logging.debug(f"Number of samples received: {len(data['timestamp'])}")
        logging.debug(f"Time range: from {datetime.fromtimestamp(data['timestamp'][0])} to {datetime.fromtimestamp(data['timestamp'][-1])}")
        # if 'SOLAR' in data:
        #     data['SOLAR'] = [power/1000.0 if power is not None else 0.0 for power in data['SOLAR']]  # TODO
        return data

    def get_data_stores(self) -> list[str]:
        try:
            resp = requests.get(self.server_url(Config().get_data_stores_url()), headers={'Accept': 'application/json'})
            logging.debug(f"Received response on get_data_stores() query: {resp.json()}")
            return resp.json()["data_stores"]
        except ConnectionError:
            logging.debug("Exception while querying get_data_stores()")

    def get_data_store_info(self, data_store_id: str):
        try:
            resp = requests.get(self.server_url(Config().get_data_store_info_url(data_store_id)), headers={'Accept': 'application/json'})
            logging.debug(f"Received response on get_data_store_info_url() query: {resp.text}")
            return resp.json()
        except Exception:
            logging.debug("Exception while querying get_data_store_info()")

    @staticmethod
    def server_url(path):
        return f"{Config().adapter()}{Config().server()}:{Config().port()}/{path}"
