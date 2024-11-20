import logging
import requests
from datetime import datetime
from Models.data_store import DataStore
from Utils.config import Config


class ServerRequests:

    def __init__(self):
        pass

    def get_data(self, data_store: DataStore):
        """
        Vraage beschikbare data op van data_store voor alle signalen.
        Retourneert data en TransferInfo
        """
        result: TransferInfo | None = None
        try:
            resp = requests.get(self.url_with_args(self.server_url(Config().get_data_url()),
                                {'data_store_name': data_store.name, 'signals': data_store.signals_comma_separated()}),
                                headers={'Accept': 'application/json'})
            data = resp.json()
            result = TransferInfo(resp)
            logging.debug(f"Received data. # bytes: {len(resp.text)} in {resp.elapsed.microseconds / 1000} ms "
                          f"({len(resp.text) / resp.elapsed.microseconds} MB/s)")
        except Exception as e:
            logging.debug(f"Could not receive data, error: {e}")
            return None
        logging.debug(f"Number of samples received: {len(data[DataStore.c_TIMESTAMP_ID])}")
        try:
            logging.debug(f"Time range: from {datetime.fromtimestamp(data[DataStore.c_TIMESTAMP_ID][0])} to {datetime.fromtimestamp(data[DataStore.c_TIMESTAMP_ID][-1])}")
        except IndexError:
            logging.debug(f"Not possible to obtain time range limits")
        return data, result

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

    def get_urls(self) -> list[str]:
        urls = [
            'raw',
            'dumpdata',
            '',
            'data_stores',
            'data_store_info',
            'get_data',
            'shift_info',
            'system_info',
            'terminate'
        ]
        return urls

    def apply_url(self, path: str):
        try:
            resp = requests.get(self.server_url(path), headers={'Accept': 'application/json'})
            logging.debug(f"Received response on {path} query: {resp.json()}")
            return resp.json()
        except Exception:
            logging.debug("Exception while querying get_shift_info()")


class TransferInfo:
    """
    Helper class to handle information about transfer speed
    """

    def __init__(self, resp: requests.Response):
        self.num_bytes = len(resp.text)
        self.time_in_sec = resp.elapsed.microseconds / 1e6

    @property
    def transfer_speed(self):
        return self.num_bytes / self.time_in_sec

    def __repr__(self):
        return (f"{self.format_prefixed(self.num_bytes)}B in {self.format_prefixed(self.time_in_sec)}s "
                f"({self.format_prefixed(self.transfer_speed)}B/s)")

    def format_prefixed(self, value) -> str:
        mult, factor = self.prefix_multiplier(value)
        return f"{value / mult:.2f} {factor}"

    def prefix_multiplier(self, value: float) -> tuple[float, str]:
        if value < 1e-6:
            return 1e-9, "n"
        elif value < 1e-3:
            return 1e-6, "u"
        elif value < 1e0:
            return 1e-3, "m"
        elif value < 1e3:
            return 1, ""
        elif value < 1e6:
            return 1e3, "k"
        elif value < 1e9:
            return 1e6, "M"
