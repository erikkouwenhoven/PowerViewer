import json
from Utils.config import Config
from Algorithms.derived_signal import DerivedSignal


class Settings:
    """Leest en schrijft instellingen uit json-file"""

    def __init__(self):
        try:
            with open(Config().getSettingsFilename()) as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            self.settings = {}
            self.update()

    def update(self):
        with open(Config().getSettingsFilename(), 'w') as file:
            json.dump(self.settings, file, indent=4)

    def getSignalCheckState(self, datastore_name, signal):
        c_DEFAULT_STATE = True
        if "SignalCheckStates" in self.settings:
            if datastore_name in self.settings["SignalCheckStates"]:
                if signal in self.settings["SignalCheckStates"][datastore_name]:
                    return self.settings["SignalCheckStates"][datastore_name][signal]
                else:
                    self.settings["SignalCheckStates"][datastore_name][signal] = c_DEFAULT_STATE
                    self.update()
                    return c_DEFAULT_STATE
            else:
                self.settings["SignalCheckStates"][datastore_name] = {signal: c_DEFAULT_STATE}
                self.update()
                return c_DEFAULT_STATE
        else:
            self.settings["SignalCheckStates"] = {datastore_name: {signal: c_DEFAULT_STATE}}
            self.update()
            return c_DEFAULT_STATE

    def setSignalCheckStates(self, datastore_name: str, checks: dict[str, bool]):
        for signal in checks:
            self.settings["SignalCheckStates"][datastore_name][signal] = checks[signal]
        self.update()

    def getSignalCheckStates(self, datastore_name: str):
        try:
            return {signal: self.settings["SignalCheckStates"][datastore_name][signal] for signal in self.settings["SignalCheckStates"][datastore_name]}
        except KeyError:
            return None

    def set_visibilities(self, visibilities: dict[str, bool]):
        if "SignalVisibilities" not in self.settings:
            self.settings["SignalVisibilities"] = {}
        for signal in visibilities:
            self.settings["SignalVisibilities"][signal] = visibilities[signal]
        self.update()

    def get_visibilities(self):
        try:
            return {signal: self.settings["SignalVisibilities"][signal] for signal in self.settings["SignalVisibilities"]}
        except KeyError:
            return None

    def get_checked_visibilities(self, datastore_name: str):
        try:
            return {signal: self.settings["SignalVisibilities"][signal] for signal in self.settings["SignalVisibilities"] if
                    signal in self.settings["SignalCheckStates"][datastore_name] and self.settings["SignalCheckStates"][datastore_name][signal] is True}
        except KeyError:
            return None

    def getDerivedSignals(self, data):
        if "DerivedSignals" in self.settings:
            derivedSignals = []
            for name in self.settings["DerivedSignals"]:
                derivedSignal = DerivedSignal(name, self.settings["DerivedSignals"][name]["Formula"], data)
                derivedSignals.append(derivedSignal)
            return derivedSignals

    def getDerivedSignalColors(self):
        if "DerivedSignals" in self.settings:
            return {name: self.settings["DerivedSignals"][name]["Color"] for name in self.settings["DerivedSignals"]}

    def get_derived_quantities(self) -> dict[str, list]:
        if "DerivedQuantities" in self.settings:
            return {quantity: self.settings["DerivedQuantities"][quantity] for quantity in self.settings["DerivedQuantities"]}
