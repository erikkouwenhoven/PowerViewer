from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Signal:
    name: str
    data: list[float]
    unit: str
    num: int = -1  # iterator

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

    def __str__(self):
        return f"{self.name}: {self.data}"


@dataclass
class DataStore:

    c_TIMESTAMP_ID: ClassVar[str] = "timestamp"

    name: str
    database: str
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
