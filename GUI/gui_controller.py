import uuid
import json
from datetime import datetime
from Utils.settings import Settings
from Utils.config import Config
from GUI.gui_view import GUIView
from GUI.gui_model import GUIModel
from Models.data_store import DataStore
from Algorithms.signal_shift import SignalShift
from GUI.time_delay_controller import TimeDelayController


class GUIController:
    """ Controller voor het main screen """

    def __init__(self):
        self.view = GUIView(Settings().get_visibilities())
        self.model = GUIModel()
        self.view.connectEvents(
            {
                'settingsDeactivated': self.deactivateSettings,
                'showSettings': self.activateSettings,
                'dataStoreSelected': self.dataStoreSelected,
                'signalsTableChanged': self.signalsTableChanged,
                'calcSolarDelay': self.calcSolarDelay,
                'reload': self.reload,
                'saveData': self.save_data,
            }
        )
        self.initialize()
        self.view.show()
        if (datastore_name := Config().getDefaultDataStoreName()) not in [data_store.name for data_store in self.model.data_stores]:
            datastore_name = self.model.c_MOCK_DATASTORE_NAME
        self.view.set_data_store_name(datastore_name=datastore_name)

    def initialize(self):
        if Config().getDefaultSettingState() is True:
            self.activateSettings()
        else:
            self.deactivateSettings()
        self.view.show_data_stores(self.model.data_stores)
        self.view.set_change_notifier(self.visibility_changed)

    def deactivateSettings(self):
        self.view.hideSettings()

    def activateSettings(self):
        self.view.showSettings()

    def dataStoreSelected(self):
        datastore_name = self.view.get_data_store_name()
        self.apply_data_store(datastore_name)

    def apply_data_store(self, datastore_name: str):
        if (signal_check_states := Settings().getSignalCheckStates(datastore_name)) is None:
            signal_check_states = {signal: True for signal in self.model.get_data_store(datastore_name).signals}
        self.view.show_signals_table(signal_check_states)
        datastore = self.model.get_data_store(datastore_name)
        self.acquire_and_show(datastore)
        self.view.set_date_range(datastore)

    def signalsTableChanged(self):
        datastore_name = self.view.get_data_store_name()
        checks = self.view.getSignalsTable(datastore_name)
        Settings().setSignalCheckStates(datastore_name, checks)
        self.model.update_data_stores()
        datastore = self.model.get_data_store(datastore_name)
        self.acquire_and_show(datastore)

    def visibility_changed(self):
        visibilities = self.view.get_visibilities()
        Settings().set_visibilities(visibilities)

    def calcSolarDelay(self):
        datastore_name = self.view.get_data_store_name()
        datastore = self.model.get_data_store(datastore_name)
        if "SOLAR" in datastore.data and "CURRENT_PRODUCTION_PHASE3" in datastore.data:
            signal_shift = SignalShift(datastore.data["SOLAR"])
            shift_in_samples = signal_shift.assess_shift(datastore.data["CURRENT_PRODUCTION_PHASE3"], kernel_size=Config().getCrossCorrKernelSize())
            sampling_time = datastore.get_sampling_time()
            TimeDelayController(signal_shift.cross_corr, shift_in_samples, sampling_time)
            print(shift_in_samples)

    def reload(self):
        datastore_name = self.view.get_data_store_name()
        datastore = self.model.get_data_store(datastore_name)
        self.acquire_and_show(datastore)

    def save_data(self):
        datastore_name = self.view.get_data_store_name()
        datastore = self.model.get_data_store(datastore_name)
        with open(f"data{uuid.uuid4()}.json", "w") as openfile:
            json.dump(str(datastore.data), openfile)

    def acquire_and_show(self, datastore: DataStore):
        self.model.acquire_data(datastore)
        self.model.handle_derived_data(datastore)
        self.view.append_colors(self.model.get_derived_colors())
        self.view.show_data(self.model.get_default_time_range(datastore), datastore)

