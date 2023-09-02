import os
import configparser


class Config:
    """Betrekt configuratie-instellingen uit config.ini"""

    def __init__(self):
        self.config = configparser.ConfigParser()
        currDir = os.path.dirname(os.path.dirname(__file__))
        configFilePath = os.path.join(currDir, 'config.ini')
        self.config.read(configFilePath)

    def server(self):
        return self.config.get('CONNECTION', 'server')

    def port(self):
        return self.config.get('CONNECTION', 'port')

    def adapter(self):
        return self.config.get('CONNECTION', 'adapter')

    def get_data_url(self):
        return self.config.get('CONNECTION', 'get_data_url')

    def get_data_stores_url(self):
        return self.config.get('CONNECTION', 'get_data_stores_url')

    def get_data_store_info_url(self, data_store):
        return self.config.get('CONNECTION', 'get_data_store_info_url') + f'?{data_store}'

    def getUiDirName(self):
        return self.config.get('PATHS', 'ui')

    def getLoggingPath(self):
        return self.config.get('PATHS', 'logging')

    def getLoggingFilename(self):
        return self.config.get('FILES', 'logfile')

    def getSettingsFilename(self):
        return self.config.get('FILES', 'settings')

    def getMainScreenFileName(self):
        return self.config.get('UI', 'mainscreen')

    def getTimeDelayDialogFileName(self):
        return self.config.get('UI', 'timedelay')

    def getAppName(self):
        return self.config.get('APPINFO', 'appname')

    def getVersion(self):
        return self.config.get('APPINFO', 'version')

    def getAppInfo(self):
        return self.config.get('APPINFO', 'info')

    def getDefaultSettingState(self):
        return True if self.config.get('DEFAULTS', 'settings') == "ON" else False

    def getDefaultDataStoreName(self):
        return self.config.get('DEFAULTS', 'dataStore_name')

    def getPreferredUnits(self):
        """spaces separated, convert to list"""
        return self.config.get('DOMAIN', 'preferred_units').split()
