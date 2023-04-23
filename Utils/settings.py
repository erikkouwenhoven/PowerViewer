import os
import configparser


class Settings:
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

    def getUiDirName(self):
        return self.config.get('PATHS', 'ui')

    def getLoggingPath(self):
        return self.config.get('PATHS', 'logging')

    def getLoggingFilename(self):
        return self.config.get('FILES', 'logfile')

    def getMainScreenFileName(self):
        return self.config.get('UI', 'mainscreen')

    def getAppName(self):
        return self.config.get('APPINFO', 'appname')

    def getVersion(self):
        return self.config.get('APPINFO', 'version')

    def getAppInfo(self):
        return self.config.get('APPINFO', 'info')
