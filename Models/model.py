import logging
from typing import Optional
import os
import json
from datetime import datetime, timedelta
from Models.data_store import DataStore, Signal, c_LOCALFILE_ID
from Models.derived_quantities import DerivedQuantities
from ServerRequests.server_requests import ServerRequests
from requests.exceptions import ConnectionError
from Utils.settings import Settings
from Utils.unit_standardizer import UnitStandardizer


class Model:

    def __init__(self):
        self.time_range = None
        self.data_stores: list[DataStore] = self.init_data_stores()
        self.current_data_store: Optional[DataStore] = None

    def init_data_stores(self) -> list[DataStore]:
        data_stores = []
        try:
            data_store_ids = ServerRequests().get_data_stores()
            for data_store_id in data_store_ids:
                data_store_info = ServerRequests().get_data_store_info(data_store_id)
                signals = [signal for signal in data_store_info["Signals"] if Settings().getSignalCheckState(data_store_info["Name"], signal) is True]
                data_stores.append(DataStore(name=data_store_info["Name"], signals=signals, database=data_store_info["Db"]))
        except Exception as err:
            logging.debug(f"Connection error {err}")
        return data_stores

    def update_data_stores(self):
        self.data_stores = self.init_data_stores()
        if self.current_data_store:
            self.current_data_store = self.get_data_store(self.current_data_store.name)

    def get_data_store(self, datastore_name: str) -> DataStore:
        for data_store in self.data_stores:
            if data_store.name == datastore_name:
                return data_store

    def set_current_datastore(self, data_store: DataStore):
        self.current_data_store = data_store

    def get_current_data_store(self) -> DataStore:
        return self.current_data_store

    def acquire_data(self, data_store: DataStore):
        if data_store.database != c_LOCALFILE_ID:
            try:
                data = ServerRequests().get_data(data_store)
            except ConnectionError as err:
                logging.debug(f"ConnectionError: {err}")
                return
        else:
            with open(data_store.name, 'r') as openfile:
                data = DataStore.data_from_stream(json.load(openfile))
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

    def init_datastore_from_local_file(self, filename: str):
        try:
            with open(filename, 'r') as openfile:
                try:
                    data = json.load(openfile)
                except json.decoder.JSONDecodeError:
                    return None
        except FileNotFoundError:  # als de naam van de file wordt veranderd tijdens het proces van fileselectie
            return None
        data_store = DataStore.unserialize(data, filename)
        self.data_stores.append(data_store)

    def get_time_range(self):
        return self.time_range

    def calc_derived_data(self, signals, time_range):
        return DerivedQuantities(Settings().get_derived_quantities()).get_values(self.current_data_store, signals, time_range)

    @staticmethod
    def handle_derived_data(data_store: DataStore):
        for derivedSignal in Settings().getDerivedSignals(data_store.data):
            if derived_data := derivedSignal.get():
                data_store.data[derivedSignal.name] = derived_data

    @staticmethod
    def get_derived_colors():
        return Settings().getDerivedSignalColors()

    @staticmethod
    def get_default_time_range(datastore: DataStore):
        end_time = datastore.end_timestamp
        min_time = datastore.start_timestamp
        if end_time:
            start_time = datetime.timestamp(datetime.fromtimestamp(end_time) - timedelta(hours=3))
            if start_time < min_time:
                start_time = min_time
        else:
            start_time = None
        return start_time, end_time

