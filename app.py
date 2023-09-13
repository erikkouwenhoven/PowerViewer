import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from GUI.Tools.time_format import logging_fmt
from PyQt6.QtWidgets import QApplication
from Utils.config import Config
from GUI.gui_controller import GUIController


class Application:

    def __init__(self):
        app = QApplication(sys.argv)
        initializeLogging(Config().getLoggingPath())
        contr = GUIController()
        sys.exit(app.exec())


def initializeLogging(pathToFile):
    if pathToFile is None:
        pathToFile = '.'
    if not os.path.exists(pathToFile):
        os.makedirs(pathToFile)
        print('Directory {} aangemaakt'.format(pathToFile))  # Qt is nog niet in de lucht, dus geen QMessageBox
    filename = Config().getLoggingFilename()
    filepath = os.path.join(pathToFile, filename)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt=logging_fmt,
                        filename=filepath,
                        filemode='w')
    logging.getLogger().addHandler(RotatingFileHandler(filepath, maxBytes=100000, backupCount=10))
    logging.getLogger("PyQt6").setLevel(logging.CRITICAL)
    logging.getLogger('matplotlib').setLevel(logging.CRITICAL)
    logging.info('Start application')


if __name__ == "__main__":
    Application()
