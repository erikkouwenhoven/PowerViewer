from PyQt6 import QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


class MplCanvas(FigureCanvas):

    def __init__(self):
        self.fig, self.ax = plt.subplots(layout="constrained")
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        FigureCanvas.updateGeometry(self)


class MplWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QtWidgets.QHBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.vbl.setSpacing(0)
        self.setLayout(self.vbl)
