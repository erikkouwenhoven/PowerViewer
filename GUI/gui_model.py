import logging
import json
from datetime import datetime, timedelta
from Models.data_store import DataStore, Signal
from ServerRequests.server_requests import ServerRequests
from requests.exceptions import ConnectionError
from Utils.settings import Settings
from Utils.unit_standardizer import UnitStandardizer


class GUIModel:

    _c_MOCK_FILE_NAME: str = 'sample.json'
    c_MOCK_DATASTORE_NAME: str = 'localfile'

    def __init__(self):
        self.time_range = None
        self.working_connection = False
        self.data_stores: list[DataStore] = self.init_data_stores()

    def init_data_stores(self) -> list[DataStore]:
        data_stores = []
        try:
            data_store_ids = ServerRequests().get_data_stores()
            for data_store_id in data_store_ids:
                data_store_info = ServerRequests().get_data_store_info(data_store_id)
                signals = [signal for signal in data_store_info["Signals"] if Settings().getSignalCheckState(data_store_info["Name"], signal) is True]
                data_stores.append(DataStore(name=data_store_info["Name"], signals=signals, database=data_store_info["Db"]))
            self.working_connection = True
        except Exception as err:
            logging.debug(f"Connection error {err}")
            self.working_connection = False
            with open(self._c_MOCK_FILE_NAME, 'r') as openfile:
                data = json.load(openfile)
            signals = [signal for signal in data if signal != DataStore.c_TIMESTAMP_ID and signal != "units"]
            data_stores.append(DataStore(name=self.c_MOCK_DATASTORE_NAME, signals=signals, database=""))
        return data_stores

    def update_data_stores(self):
        self.data_stores = self.init_data_stores()

    def get_data_store(self, datastore_name: str) -> DataStore:
        for data_store in self.data_stores:
            if data_store.name == datastore_name:
                return data_store

    def acquire_data(self, data_store: DataStore):
        try:
            data = ServerRequests().get_data(data_store)
        except ConnectionError as err:
            self.working_connection = False
            logging.debug(f"ConnectionError: {err}")
        if self.working_connection is False:
            with open(self._c_MOCK_FILE_NAME, 'r') as openfile:
                data = json.load(openfile)
            logging.debug(f"Got data from file")
        units = data["units"]
        data_store.data = {k: Signal(name=k, data=v, unit=units[k] if k in units else "") for k, v in data.items() if k != "units" and k in data_store.signals or k == DataStore.c_TIMESTAMP_ID}
        UnitStandardizer().execute(units, data_store.data, data_store.signals)
        data_store.end_timestamp = max(data_store.data[DataStore.c_TIMESTAMP_ID])
        data_store.start_timestamp = min(data_store.data[DataStore.c_TIMESTAMP_ID])

        try:
            t_prev = None
            for i, t in enumerate(data_store.data[DataStore.c_TIMESTAMP_ID]):
                if i != 0:
                    delta_t = t - t_prev
                    if delta_t > {'real_time': 11, 'persistent': 66}[data_store.name]:
                        print(f"delta = {delta_t} @ t = {datetime.fromtimestamp(t_prev)} > {datetime.fromtimestamp(t)}")
                t_prev = t
        except KeyError:
            pass

    def handle_derived_data(self, data_store: DataStore):
        for derivedSignal in Settings().getDerivedSignals(data_store.data):
            if derived_data := derivedSignal.get():
                data_store.data[derivedSignal.name] = derived_data

    def get_derived_colors(self):
        return Settings().getDerivedSignalColors()

    def get_time_range(self):
        return self.time_range

    def get_default_time_range(self, datastore: DataStore):
        end_time = datastore.end_timestamp
        min_time = datastore.start_timestamp
        if end_time:
            start_time = datetime.timestamp(datetime.fromtimestamp(end_time) - timedelta(hours=3))
            if start_time < min_time:
                start_time = min_time
        else:
            start_time = None
        return start_time, end_time



