from Utils.settings import Settings
from Utils.config import Config
from GUI.gui_view import GUIView
from GUI.gui_model import GUIModel
from Models.data_store import DataStore


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
            }
        )
        self.initialize()
        self.view.show()
        self.view.set_data_store_name(Config().getDefaultDataStoreName())

    def initialize(self):
        if Config().getDefaultSettingState() is True:
            self.activateSettings()
        else:
            self.deactivateSettings()
        self.view.show_data_stores(self.model.data_stores)

    def deactivateSettings(self):
        self.view.hideSettings()

    def activateSettings(self):
        self.view.showSettings()

    def dataStoreSelected(self):
        datastore_name = self.view.get_data_store_name()
        self.apply_data_store(datastore_name)

    def apply_data_store(self, datastore_name: str):
        self.view.show_signals_table(Settings().getSignalCheckStates(datastore_name))
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

    def acquire_and_show(self, datastore: DataStore):
        self.model.acquire_data(datastore)
        self.model.handle_derived_data(datastore)
        self.view.set_colors(self.model.get_derived_colors())
        self.view.show_data(datastore.data, self.model.get_default_time_range(datastore), datastore)

