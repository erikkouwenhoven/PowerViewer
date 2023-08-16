from dataclasses import dataclass


@dataclass
class DataStore:
    name: str
    database: str
    signals: list[str]
    derived_signals: list[str] = None
    data: dict[str, list[float]] = None
    start_timestamp: float = None
    end_timestamp: float = None
