import logging
import requests
from datetime import datetime
from Models.data_store import DataStore
from Utils.config import Config


class ServerRequests:

    def __init__(self):
        pass

    def get_data(self, data_store: DataStore):
        try:
            # resp = requests.get(self.server_url(Config().get_data_url()) + data_store_name, headers={'Accept': 'application/json'})
            resp = requests.get(self.url_with_args(self.server_url(Config().get_data_url()),
                                {'data_store_name': data_store.name, 'signals': data_store.signals_comma_separated()}),
                                headers={'Accept': 'application/json'})
            data = resp.json()
            logging.debug(f"Received data. # bytes: {len(resp.text)}")
        except Exception as e:
            logging.debug(f"Could not receive data, error: {e}")
            return None
        logging.debug(f"Number of samples received: {len(data[DataStore.c_TIMESTAMP_ID])}")
        logging.debug(f"Time range: from {datetime.fromtimestamp(data[DataStore.c_TIMESTAMP_ID][0])} to {datetime.fromtimestamp(data[DataStore.c_TIMESTAMP_ID][-1])}")
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
            logging.debug(f"Received response on get_data_store_info_url() query: {resp.json()}")
            return resp.json()
        except Exception:
            logging.debug("Exception while querying get_data_store_info()")

    def get_shift_info(self):
        try:
            resp = requests.get(self.server_url(Config().get_shift_info_url()), headers={'Accept': 'application/json'})
            logging.debug(f"Received response on get_shift_info() query: {resp.json()}")
            return resp.json()
        except Exception:
            logging.debug("Exception while querying get_shift_info()")

    @staticmethod
    def url_with_args(url: str, args: dict[str, str]) -> str:
        res = url
        for i, arg in enumerate(args):
            res += '?' if i == 0 else '&'
            res += f'{arg}={args[arg]}'
        return res

    @staticmethod
    def server_url(path):
        return f"{Config().adapter()}{Config().server()}:{Config().port()}/{path}"
