import json
from Utils.config import Config
from Application.derived_signal import DerivedSignal


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

    def getSignalCheckState(self, datastore, signal):
        c_DEFAULT_STATE = True
        if "SignalCheckStates" in self.settings:
            if datastore in self.settings["SignalCheckStates"]:
                if signal in self.settings["SignalCheckStates"][datastore]:
                    return self.settings["SignalCheckStates"][datastore][signal]
                else:
                    self.settings["SignalCheckStates"][datastore][signal] = c_DEFAULT_STATE
                    self.update()
                    return c_DEFAULT_STATE
            else:
                self.settings["SignalCheckStates"][datastore] = {signal: c_DEFAULT_STATE}
                self.update()
                return c_DEFAULT_STATE
        else:
            self.settings["SignalCheckStates"] = {datastore: {signal: c_DEFAULT_STATE}}
            self.update()
            return c_DEFAULT_STATE

    def setSignalCheckStates(self, datastore_name: str, checks: dict[str, bool]):
        for signal in checks:
            self.settings["SignalCheckStates"][datastore_name][signal] = checks[signal]
        self.update()

    def getSignalCheckStates(self, datastore_name: str):
        return {signal: self.settings["SignalCheckStates"][datastore_name][signal] for signal in self.settings["SignalCheckStates"][datastore_name]}

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
