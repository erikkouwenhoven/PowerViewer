from datetime import datetime, timedelta
from Models.data_store import DataStore
from ServerRequests.server_requests import ServerRequests
from requests.exceptions import ConnectionError
from Utils.settings import Settings
from Utils.unit_standardizer import UnitStandardizer
from Algorithms.signal_shift import SignalShift
from Algorithms.derived_signal import Operation


class GUIModel:

    def __init__(self):
        self.time_range = None  # self.init_time_range()
        self.data_stores: list[DataStore] = GUIModel.init_data_stores()

    @staticmethod
    def init_data_stores() -> list[DataStore]:
        try:
            data_stores = []
            data_store_ids = ServerRequests().get_data_stores()
            for data_store_id in data_store_ids:
                data_store_info = ServerRequests().get_data_store_info(data_store_id)
                data_stores.append(DataStore(name=data_store_info["Name"], signals=data_store_info["Signals"], database=data_store_info["Db"]))
        except Exception:
            raise RuntimeError("Connection failure")
        # signals = [
        #     "CURRENT_USAGE",
        #     "CURRENT_PRODUCTION",
        #     "SOLAR",
        #     "CURRENT_USAGE_PHASE1",
        #     "CURRENT_USAGE_PHASE2",
        #     "CURRENT_USAGE_PHASE3",
        #     "CURRENT_PRODUCTION_PHASE1",
        #     "CURRENT_PRODUCTION_PHASE2",
        #     "CURRENT_PRODUCTION_PHASE3"
        # ]
        return data_stores

    def update_data_stores(self):
        self.data_stores = self.init_data_stores()

    def get_data_store(self, datastore_name: str) -> DataStore:
        for data_store in self.data_stores:
            if data_store.name == datastore_name:
                return data_store

    def acquire_data(self, data_store: DataStore):
        try:
            orig_data = ServerRequests().get_data(f'?{data_store.name}')
            # orig_data["SOLAR"] = SignalShift(Operation.fix_signal(orig_data["SOLAR"])).do_shift(-2.0 if data_store.name == "realtime" else -2.0/6.0)  # TODO dit hoort niet hier
            data_store.data = {k: v for k, v in orig_data.items() if k != "units" and k in data_store.signals or k == "timestamp"}
            units = orig_data["units"]
            UnitStandardizer().execute(units, data_store.data, data_store.signals)
            data_store.end_timestamp = max(data_store.data["timestamp"])
            data_store.start_timestamp = min(data_store.data["timestamp"])
        except ConnectionError as err:
            print(f"ConnectionError: {err}")
            return

        t_prev = None
        for i, t in enumerate(data_store.data['timestamp']):
            if i != 0:
                delta_t = t - t_prev
                if delta_t > {'real_time': 11, 'persistent': 66}[data_store.name]:
                    print(f"delta = {delta_t} @ t = {datetime.fromtimestamp(t_prev)} > {datetime.fromtimestamp(t)}")
            t_prev = t

    def handle_derived_data(self, data_store: DataStore):
        for derivedSignal in Settings().getDerivedSignals(data_store.data):
            data_store.data[derivedSignal.name] = derivedSignal.get()

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

    @staticmethod
    def b_search(array, value):
        lo = 0
        hi = len(array) - 1
        while lo < hi:
            m = int((lo + hi) / 2)
            if array[m] < value:
                lo = m + 1
            elif array[m] > value:
                hi = m - 1
            elif array[m] == value:
                return m
            if hi - lo <= 1:
                return lo


