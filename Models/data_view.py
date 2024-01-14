from typing import Dict, List
import json
from Models.data_store import DataStore, c_LOCALFILE_ID


class DataView:
    """
    Een view is een collectie van DataStores en een selectie van signals hiervan
    """

    def __init__(self, name: str, specified_names: Dict[str, List[str]], all_data_stores: list[DataStore]):
        self.name = name
        self.selection: dict[DataStore, List[str]] = self.evaluate(specified_names, all_data_stores)

    @classmethod
    def from_data_store(cls, data_store, all_data_stores: list[DataStore]):
        return cls(data_store.name, {data_store.name: data_store.signals}, all_data_stores)

    def evaluate(self, specified_names: dict[str, List[str]], data_stores: list[DataStore]) -> dict[DataStore, List[str]]:
        selection = {}
        for data_store_name in specified_names:
            handled = False  # check if data_store_name is present
            for sel_data_store in filter(lambda ds: ds.name == data_store_name, data_stores):
                assert handled is False  # only one item
                handled = True
                for signal in specified_names[data_store_name]:
                    if signal not in sel_data_store.signals:
                        raise RuntimeError
                selection[sel_data_store] = specified_names[data_store_name]
            if handled is False:
                raise RuntimeError
        return selection

    def get_data_stores(self) -> list[DataStore]:
        return [data_store for data_store in self.selection]

    def get_signals(self, data_store: DataStore) -> list[str]:
        return self.selection[data_store]

    def serialize(self, full_file_name: str, signals: list[str], idx_range=None):
        return {
            "view_name": self.name,
            "data_stores": {data_store.name: data_store.serialize(signals=[signal for signal in self.selection[data_store] if signals is None or signal in signals], time_range=idx_range, name=full_file_name) for data_store in self.selection}
        }

    def save(self, full_file_name: str, signals: list[str], time_range):
        with open(full_file_name, "w") as openfile:
            json.dump(self.serialize(full_file_name, signals, time_range), openfile)

    def load(self, full_file_name, all_data_stores):
        try:
            with open(full_file_name, 'r') as openfile:
                try:
                    stream = json.load(openfile)
                except json.decoder.JSONDecodeError:
                    return None
        except FileNotFoundError:  # als de naam van de file wordt veranderd tijdens het proces van fileselectie
            return None
        return self.unserialize(stream, full_file_name)

    def unserialize(self, stream: dict, full_file_name: str) -> list[DataStore]:
        new_data_stores = []
        specified_names: Dict[str, List[str]] = {}
        try:
            data_store_keys = [data_store_name for data_store_name in stream["data_stores"]]
            for data_store_key in data_store_keys:
                specified_names[data_store_key] = stream["data_stores"][data_store_key]["signals"]
                data_store = DataStore.unserialize(stream["data_stores"][data_store_key], data_store_key)
                data_store.set_data(DataStore.data_from_stream(stream["data_stores"][data_store_key], data_store))
                new_data_stores.append(data_store)
            self.name = stream["view_name"]
        except KeyError:
            raise RuntimeError("Invalid file format")
        self.selection = self.evaluate(specified_names, new_data_stores)
        return new_data_stores

    def is_local_file(self) -> bool:  # TODO documenteren
        if self.name == c_LOCALFILE_ID:
            return True
        else:
            return False

    def get_local_file_name(self) -> str:
        if self.is_local_file():
            names = [data_store.name for data_store in self.selection]
            name = names[0]
            assert all([data_store.name == name for data_store in self.selection])
            return name
