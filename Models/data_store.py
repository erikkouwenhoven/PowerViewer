from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from Models.signal import Signal
from Algorithms.binary_search import interval_to_range
from Utils.unit_standardizer import UnitStandardizer


c_LOCALFILE_ID = "Local_file"


@dataclass
class DataStore:

    c_TIMESTAMP_ID: ClassVar[str] = "timestamp"

    name: str
    database: str  # Bij local file wordt dit c_LOCALFILE_ID
    signals: list[str] = None
    derived_signals: list[str] = None
    data: dict[str, Signal] = None
    start_timestamp: float = None
    end_timestamp: float = None

    def set_data(self, data: dict[str, list[float] | list[str]]):
        if data:
            self.signals = [signal for signal in data if signal != "units" and signal != DataStore.c_TIMESTAMP_ID]
            units = data["units"]
            self.data = {k: Signal(name=k, data=v, unit=units[k] if k in units else "") for k, v in data.items() if k != "units" and k in self.signals or k == DataStore.c_TIMESTAMP_ID}
            UnitStandardizer().execute(units, self.data, self.signals)
            try:
                self.end_timestamp = max(self.data[DataStore.c_TIMESTAMP_ID])
                self.start_timestamp = min(self.data[DataStore.c_TIMESTAMP_ID])
            except ValueError:
                pass  # geen data

    def get_sampling_time(self):
        cum_delta = 0.0
        count_delta = 0
        prev_t = None
        for t in self.data[self.c_TIMESTAMP_ID]:
            if prev_t is not None:
                cum_delta += t - prev_t
                count_delta += 1
            prev_t = t
        return cum_delta / count_delta

    def signals_comma_separated(self) -> str:
        return ",".join(self.signals)

    def get_signals_grouped_unit(self) -> dict[str, list[Signal]]:
        if self.data:
            result = {}
            units = {self.data[signal].unit for signal in self.data if signal != self.c_TIMESTAMP_ID}
            for unit in units:
                signals = [signal for signal in self.data.values() if signal.unit == unit]
                result[unit] = signals
            return result

    def combine_signals_grouped_units(self, group: dict[str, list[Signal]]) -> dict[str, list[Signal]]:
        new_group = self.get_signals_grouped_unit()
        if group:
            for unit in group:
                if unit in new_group:
                    new_group[unit] += group[unit]
                else:
                    new_group[unit] = group[unit]
        return new_group

    def serialize(self, signals, time_range, name=None):
        if time_range is not None:
            i_range = interval_to_range(self.data[DataStore.c_TIMESTAMP_ID].data, time_range[0], time_range[1])
            data = [self.data[signal].serialize(i_range) for signal in self.data if signals is None or signal in signals or signal == DataStore.c_TIMESTAMP_ID]
        else:
            data = [self.data[signal].serialize() for signal in self.data]
        return {
            "name": self.name if name is None else name,
            "database": c_LOCALFILE_ID,
            "signals": [signal for signal in self.signals if signals is None or signal in signals],
            "data": data
        }

    @staticmethod
    def data_from_stream(stream: dict, data_store: DataStore) -> dict[str, list[float] | list[str]]:
        """
        converteer naar lijst van signals
        creeer lijstje van units
        geef dict van floats terug
        """
        signals = [Signal.unserialize(elem) for elem in stream["data"]]
        data = {"units": {signal.name: signal.unit for signal in signals}}
        for signal in signals:
            data[signal.name] = signal.data
        return data

    @classmethod
    def unserialize(cls, stream: dict, name: str):
        return cls(name=name, database=c_LOCALFILE_ID, signals=stream["signals"])

    def __hash__(self):
        return hash(self.name)
