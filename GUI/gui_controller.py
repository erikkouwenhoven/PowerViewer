import os
import json
import logging
from datetime import datetime
from Utils.settings import Settings
from Utils.config import Config
from GUI.gui_view import GUIView
from Models.model import Model
from GUI.Tools.time_format import filename_fmt
from Models.data_store import c_LOCALFILE_ID
from Algorithms.signal_shift import SignalShift
from GUI.time_delay_controller import TimeDelayController


class GUIController:
    """ Controller voor het main screen """

    def __init__(self):
        self.view = GUIView()
        self.model = Model()
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
        self.view.show_data_views(self.model.data_views)
        self.view.set_visibility_change_notifier(self.visibility_changed)
        self.view.set_redraw_notifier(self.plot_redrawn)

    def deactivateSettings(self):
        self.view.hideSettings()

    def activateSettings(self):
        self.view.showSettings()

    def dataStoreSelected(self):
        if (datastore_name := self.view.get_data_store_name()) == c_LOCALFILE_ID:
            local_file_name = self.view.query_local_file()
            self.model.init_dataview_from_local_file(local_file_name)
            self.apply_data_store(local_file_name)
        else:
            self.apply_data_store(datastore_name)

    def apply_data_store(self, dataview_name: str):
        self.model.set_current_data_view(dataview_name)
        signal_check_states = []
        for data_store in self.model.get_current_data_stores():
            if (signal_check_states_this_data_store := Settings().getSignalCheckStates(data_store.name)) is None:
                signal_check_states_this_data_store = {signal: True for signal in data_store.signals}
            else:
                signal_check_states_this_data_store = dict(filter(lambda x: x[0] in self.model.get_current_data_view().get_signals(data_store), signal_check_states_this_data_store.items()))
            signal_check_states = signal_check_states | signal_check_states_this_data_store if signal_check_states else signal_check_states_this_data_store
        self.view.show_signals_table(signal_check_states)
        self.acquire_and_show()
        self.view.set_date_range(self.model.get_current_data_stores())

    def signalsTableChanged(self):
        for data_store in self.model.get_current_data_stores():
            checks = self.view.getSignalsTable(data_store.name)
            Settings().setSignalCheckStates(data_store.name, checks)
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
        for data_store in self.model.get_current_data_stores():
            signals = self.model.get_current_data_view().get_signals(data_store)
            if "SOLAR" in signals and "CURRENT_PRODUCTION_PHASE3" in signals:
                signal_shift = SignalShift(data_store.data["SOLAR"])
                shift_in_samples = signal_shift.assess_shift(data_store.data["CURRENT_PRODUCTION_PHASE3"], kernel_size=Config().getCrossCorrKernelSize())
                sampling_time = data_store.get_sampling_time()
                TimeDelayController(signal_shift.cross_corr, shift_in_samples, sampling_time)
                print(shift_in_samples)

    def reload(self):
        self.apply_data_store(self.model.get_current_data_view().name)

    def save_data(self, signals: list[str] = None, time_range: tuple[float] = None):  # TODO signal selectie
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
        self.model.get_current_data_view().save(full_file_name, time_range)

    def acquire_and_show(self):
        if data_view := self.model.get_current_data_view():
            self.model.acquire_data(data_view)
            for data_store in self.model.get_current_data_stores():
                Model.handle_derived_data(data_store)
            self.view.append_colors(Model.get_derived_colors())
            self.view.show_data(Model.get_default_time_range(self.model.get_current_data_stores()), data_view)
