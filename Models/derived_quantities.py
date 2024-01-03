from typing import Optional
from Algorithms.binary_search import interval_to_range
from Models.data_store import DataStore


class DerivedQuantities:

    def __init__(self, parameters: dict[str, list]):
        self.parameters = parameters

    def get_values(self, data_stores: list[DataStore], signals: list[str], time_range: tuple[float]) -> dict[str, float]:
        res = {}
        for operation in self.parameters:
            if operation == "TotalEnergy":
                for signal_name in self.parameters[operation]:
                    for data_store in data_stores:
                        if data_store.data and signal_name in data_store.data and signal_name in signals:
                            res[signal_name] = self.total_energy(data_store, signal_name, time_range)
        return res

    @staticmethod
    def total_energy(data_store: DataStore, signal_name: str, time_range) -> Optional[float]:
        signal = data_store.data[signal_name].fix_signal()
        if time_range is not None:
            i_range = interval_to_range(data_store.data[DataStore.c_TIMESTAMP_ID].data, time_range[0], time_range[1])
            data = [signal[i] for i in i_range]
        else:
            data = signal.data
        conv_factor = data_store.get_sampling_time() / 3600.0 / 1000.0
        try:
            return sum(data) * conv_factor
        except TypeError:
            return None
