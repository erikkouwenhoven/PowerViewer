import os
import json
import logging
from datetime import datetime
from Utils.settings import Settings
from Utils.config import Config
from GUI.gui_view import GUIView
from GUI.gui_model import GUIModel
from GUI.Tools.time_format import filename_fmt
from Models.data_store import DataStore, c_LOCALFILE_ID
from Algorithms.signal_shift import SignalShift
from GUI.time_delay_controller import TimeDelayController


class GUIController:
    """ Controller voor het main screen """

    def __init__(self):
        self.view = GUIView()
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
            datastore_name = c_LOCALFILE_ID
        self.view.set_data_store_name(datastore_name=datastore_name)
        self.dataStoreSelected()

    def initialize(self):
        if Config().getDefaultSettingState() is True:
            self.activateSettings()
        else:
            self.deactivateSettings()
        self.view.show_data_stores(self.model.data_stores)
        self.view.set_visibility_change_notifier(self.visibility_changed)
        self.view.set_redraw_notifier(self.plot_redrawn)

    def deactivateSettings(self):
        self.view.hideSettings()

    def activateSettings(self):
        self.view.showSettings()

    def dataStoreSelected(self):
        if (datastore_name := self.view.get_data_store_name()) == c_LOCALFILE_ID:
            local_file_name = self.view.query_local_file()
            self.model.init_datastore_from_local_file(local_file_name)
            self.apply_data_store(local_file_name)
        else:
            self.apply_data_store(datastore_name)

    def apply_data_store(self, datastore_name: str):
        if (datastore := self.model.get_data_store(datastore_name)) is not None:
            self.model.set_current_datastore(datastore)
            if (signal_check_states := Settings().getSignalCheckStates(datastore_name)) is None:
                signal_check_states = {signal: True for signal in datastore.signals}
            self.view.show_signals_table(signal_check_states)
            self.acquire_and_show()
            self.view.set_date_range(datastore)

    def signalsTableChanged(self):
        datastore = self.model.get_current_data_store()
        checks = self.view.getSignalsTable(datastore.name)
        Settings().setSignalCheckStates(datastore.name, checks)
        self.model.update_data_stores()
        self.acquire_and_show()

    def visibility_changed(self):
        visibilities = self.view.get_visibilities()
        Settings().set_visibilities(visibilities)
        self.update_derived_quantities()

    def plot_redrawn(self):
        self.update_derived_quantities()

    def update_derived_quantities(self):
        self.view.show_derived_data(self.model.calc_derived_data(signals=self.view.plotter.get_displayed_signals(),
                                                                 time_range=self.view.plotter.time_range))

    def calcSolarDelay(self):
        datastore = self.model.get_current_data_store()
        if "SOLAR" in datastore.data and "CURRENT_PRODUCTION_PHASE3" in datastore.data:
            signal_shift = SignalShift(datastore.data["SOLAR"])
            shift_in_samples = signal_shift.assess_shift(datastore.data["CURRENT_PRODUCTION_PHASE3"], kernel_size=Config().getCrossCorrKernelSize())
            sampling_time = datastore.get_sampling_time()
            TimeDelayController(signal_shift.cross_corr, shift_in_samples, sampling_time)
            print(shift_in_samples)

    def reload(self):
        self.acquire_and_show()

    def save_data(self, signals: list[str] = None, time_range: tuple[float] = None):
        datastore = self.model.get_current_data_store()
        if not os.path.exists(path := Config().getDataFilesPath()):
            os.makedirs(path)
            logging.info(f"Created directory {path}")
        filename = datetime.now().strftime(filename_fmt)
        cnt = 0
        while os.path.exists(full_file_name := os.path.abspath(os.path.join(path, filename + ".json"))):
            cnt += 1
            if cnt == 1:  # First time
                filename += f"_{cnt}"
            else:
                filename = filename.split('_')[0] + f"_{cnt}"
        datastore.name = full_file_name
        with open(full_file_name, "w") as openfile:
            json.dump(datastore.serialize(signals, time_range), openfile)

    def acquire_and_show(self):
        datastore = self.model.get_current_data_store()
        self.model.acquire_data(datastore)
        self.model.handle_derived_data(datastore)
        self.view.append_colors(self.model.get_derived_colors())
        self.view.show_data(self.model.get_default_time_range(datastore), datastore)
