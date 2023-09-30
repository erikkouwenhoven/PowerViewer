from Algorithms.binary_search import b_search
from Models.data_store import DataStore


class DerivedQuantities:

    def __init__(self, parameters: dict[str, list]):
        self.parameters = parameters

    def get_values(self, data_store: DataStore, signals: list[str], time_range: tuple[float]) -> dict[str, float]:
        res = {}
        for operation in self.parameters:
            if operation == "TotalEnergy":
                for signal_name in self.parameters[operation]:
                    if signal_name in data_store.data and signal_name in signals:
                        res[signal_name] = self.total_energy(data_store, signal_name, time_range)
        return res

    @staticmethod
    def total_energy(data_store: DataStore, signal_name: str, time_range) -> float:
        signal = data_store.data[signal_name].fix_signal()
        if time_range is not None:
            i_range = (b_search(data_store.data[DataStore.c_TIMESTAMP_ID].data, time_range[0]),
                       b_search(data_store.data[DataStore.c_TIMESTAMP_ID].data, time_range[1]))
            data = [signal[i] for i in range(i_range[0], i_range[1])]
        else:
            data = signal.data
        conv_factor = data_store.get_sampling_time() / 3600.0 / 1000.0
        try:
            return sum(data) * conv_factor
        except TypeError:
            return None
