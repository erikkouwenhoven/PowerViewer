import logging
from datetime import datetime, timedelta
from Models.data_store import DataStore, c_LOCALFILE_ID
from Models.data_view import DataView
from Models.derived_quantities import DerivedQuantities
from ServerRequests.server_requests import ServerRequests
from requests.exceptions import ConnectionError
from Utils.settings import Settings
from Utils.config import Config


class Model:
    """
    Eigenaar van de data_views en de data_stores. De data_views houden referenties bij van de data_stores. Bij
    initialisatie zijn de data_stores nog niet gevuld met data.
    """

    def __init__(self):
        self.time_range = None
        self.data_stores: list[DataStore] = self.init_data_stores()
        self.data_views: dict[str, DataView] = self.init_data_views()
        self.current_data_view_name: str | None = None

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

    def init_data_views(self) -> dict[str, DataView] | None:
        if all_data_stores := self.data_stores:
            data_views = Settings().get_data_views(all_data_stores)
            for data_store in self.data_stores:
                data_views[data_store.name] = DataView.from_data_store(data_store, self.data_stores)
            return data_views
        else:
            return {}

    def update_data_stores(self):
        self.data_stores = self.init_data_stores()

    def get_data_store(self, datastore_name: str) -> DataStore:
        for data_store in self.data_stores:
            if data_store.name == datastore_name:
                return data_store

    def handle_new_data_stores(self, new_data_stores: list[DataStore]):
        for data_store in new_data_stores:
            if existing := self.get_data_store(data_store.name):
                self.data_stores.remove(existing)
            self.data_stores.append(data_store)

    def get_data_view(self, dataview_name: str) -> DataView:
        if dataview_name in self.data_views:
            return self.data_views[dataview_name]

    def set_current_data_view(self, data_view_name: str):
        assert data_view_name in self.data_views
        self.current_data_view_name = data_view_name

    def get_current_data_view(self) -> DataView:
        return self.data_views[self.current_data_view_name]

    def get_local_file_name(self, data_view: DataView) -> str:
        for view_key in self.data_views:
            if self.data_views[view_key] == data_view:
                assert data_view.name == c_LOCALFILE_ID
                return view_key

    def get_current_data_stores(self) -> list[DataStore]:
        data_view = self.get_current_data_view()
        return data_view.get_data_stores()

    def acquire_data(self, data_view: DataView):
        if data_view.is_local_file():
            new_data_stores = data_view.load(self.get_local_file_name(data_view), self.data_stores)
            self.handle_new_data_stores(new_data_stores)
        else:
            for data_store in data_view.get_data_stores():
                try:
                    data = ServerRequests().get_data(data_store)
                except ConnectionError as err:
                    logging.debug(f"ConnectionError: {err}")
                    return
                data_store.set_data(data)

    def get_server_queries(self) -> list[str]:
        return ServerRequests().get_urls()

    def apply_query(self, path: str):
        return ServerRequests().apply_url(path)

    def init_dataview_from_local_file(self, filename: str):
        """
        Maakt een nieuwe data_view aan. De database hiervan is van het type c_LOCAL_FILE, de naam ervan is de filenaam.
        """
        data_view = DataView(c_LOCALFILE_ID, specified_names={}, all_data_stores=self.data_stores)
        self.data_views[filename] = data_view

    def get_time_range(self):
        return self.time_range

    def calc_derived_data(self, signals, time_range):
        return DerivedQuantities(Settings().get_derived_quantities()).get_values(self.get_current_data_stores(), signals, time_range)

    @staticmethod
    def handle_derived_data(data_store: DataStore):
        for derivedSignal in Settings().getDerivedSignals(data_store.data):
            if derived_data := derivedSignal.get():
                data_store.data[derivedSignal.name] = derived_data

    @staticmethod
    def get_derived_colors():
        return Settings().getDerivedSignalColors()

    @staticmethod
    def get_default_time_range(data_stores: list[DataStore]) -> tuple[float | None]:
        end_time = min(data_store.end_timestamp for data_store in data_stores)
        min_time = max(data_store.start_timestamp for data_store in data_stores)
        if end_time:
            start_time = datetime.timestamp(datetime.fromtimestamp(end_time) - timedelta(hours=Config().get_initial_plot_time_range_hours()))
            if start_time < min_time:
                start_time = min_time
        else:
            start_time = None
        return start_time, end_time

