from dataclasses import dataclass
from typing import ClassVar
from Algorithms.binary_search import b_search


c_LOCALFILE_ID = "Local_file"


@dataclass
class Signal:
    name: str
    data: list[float]
    unit: str
    num: int = -1  # iterator

    def fix_signal(self):
        fixed = Signal(name=self.name, data=len(self) * [0.0], unit=self.unit)
        for i, value in enumerate(self):
            if value:
                fixed[i] = value
            else:
                if 0 < i < len(self) - 1:
                    if self[i - 1] is not None and self[i + 1] is not None:
                        fixed[i] = (self[i - 1] + self[i + 1]) / 2.0
                    elif self[i - 1] is not None:
                        fixed[i] = self[i - 1]
                    elif self[i + 1] is not None:
                        fixed[i] = self[i + 1]
                    else:
                        fixed[i] = 0.0
                else:
                    if i > 0:
                        if self[len(self) - 1] is None:
                            fixed[i] = 0.0
                        else:
                            fixed[i] = self[len(self) - 1]
                    else:
                        if self[0] is None:
                            fixed[i] = 0.0
                        else:
                            fixed[i] = self[0]
        return fixed

    def __iter__(self):
        return self

    def __next__(self):
        if self.num + 1 >= len(self.data):
            self.num = -1
            raise StopIteration
        else:
            self.num += 1
            return self.data[self.num]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def min(self):
        return min(self.data)

    def max(self):
        return max(self.data)

    def serialize(self, idx_range=None):
        return {
            "name": self.name,
            "data": self.data if idx_range is None else [self.data[i] for i in range(idx_range[0], idx_range[1])],
            "unit": self.unit
        }

    @classmethod
    def unserialize(cls, stream: dict):
        return cls(name=stream["name"], data=stream["data"], unit=stream["unit"])

    def __str__(self):
        return f"{self.name}: {self.data}"


@dataclass
class DataStore:

    c_TIMESTAMP_ID: ClassVar[str] = "timestamp"

    name: str
    database: str  # Bij local file wordt dit c_LOCALFILE_ID
    signals: list[str]
    derived_signals: list[str] = None
    data: dict[str, Signal] = None
    start_timestamp: float = None
    end_timestamp: float = None

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

    def get_dominant_unit(self):
        units = [self.data[signal].unit for signal in self.data if signal != self.c_TIMESTAMP_ID]
        if len(units) > 0:
            if all(unit == units[0] for unit in units) is True:
                return units[0]

    def serialize(self, signals, time_range):
        if time_range is not None:
            i_range = (b_search(self.data[DataStore.c_TIMESTAMP_ID].data, time_range[0]),
                       b_search(self.data[DataStore.c_TIMESTAMP_ID].data, time_range[1]))
            data = [self.data[signal].serialize(i_range) for signal in self.data if signals is None or signal in signals or signal == DataStore.c_TIMESTAMP_ID]
        else:
            data = [self.data[signal].serialize() for signal in self.data]
        return {
            "name": self.name,
            "database": c_LOCALFILE_ID,
            "signals": [signal for signal in self.signals if signals is None or signal in signals],
            "data": data
        }

    @staticmethod
    def data_from_stream(stream: dict):
        """
        converteer naar lijst van signals
        creeer lijstje van units
        geef dict van floats terug
        """
        # data = {elem["name"]: Signal.unserialize(elem) for elem in stream["data"]}
        data = {}
        signals = [Signal.unserialize(elem) for elem in stream["data"]]
        data["units"] = {signal.name: signal.unit for signal in signals}
        for signal in signals:
            data[signal.name] = signal.data
        return data

    @classmethod
    def unserialize(cls, stream: dict, name: str):
        return cls(name=name, database=c_LOCALFILE_ID, signals=stream["signals"])
