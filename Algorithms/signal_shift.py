import math
from Utils.config import Config
from Models.data_store import Signal
from Algorithms.golden_section_search import gssrec


class SignalShift:

    def __init__(self, signal: Signal):
        self.signal = signal
        self.cross_corr = None

    def assess_shift(self, other_signal, kernel_size):
        assert len(self.signal) == len(other_signal)
        self.cross_corr = self.calc_cross_corr(self.signal, other_signal, kernel_size)
        peaked_signal = PeakedSignal({t - kernel_size: v for t, v in enumerate(self.cross_corr[1])})
        return peaked_signal.find_maximum(search_range=Config().getSearchRangeMaxCrossCorr())

    @staticmethod
    def calc_cross_corr(x_data, y_data, kernel_size):
        x_fix = [x_val if x_val else 0.0 for x_val in x_data]
        y_fix = [y_val if y_val else 0.0 for y_val in y_data]
        x_mean = sum(x_fix) / len(x_fix)
        y_mean = sum(y_fix) / len(y_fix)
        x_demean = [x_val - x_mean for x_val in x_fix]
        y_demean = [y_val - y_mean for y_val in y_fix]
        std_x = math.sqrt(sum([x**2 for x in x_demean]) / len(x_demean))
        std_y = math.sqrt(sum([y**2 for y in y_demean]) / len(y_demean))
        cc = [0.0] * (2*kernel_size + 1)
        t = [-kernel_size + i for i in range(2*kernel_size + 1)]
        for i, x_val in enumerate(x_demean):
            y_lims = max(0, i - kernel_size), min(len(x_demean)-1, i + kernel_size)
            y_range = range(y_lims[0], y_lims[1] + 1)
            if not (all([y_fix[i_y] == 0.0 for i_y in y_range]) and x_fix[i] == 0.0):
                for j in range(y_lims[0], y_lims[1] + 1):
                    cc[j + kernel_size - i] += x_val * y_demean[j]
        for i, cc_val in enumerate(cc):
            cc[i] /= (std_x * std_y * len(x_demean))
        return t, cc

    def do_shift(self, shift: float) -> list[float]:
        int_part = int(math.floor(shift))
        float_part = shift - int_part
        shifted = [0.0] * len(self.signal)
        for i in range(len(self.signal)):
            if i + int_part < 0:
                shifted[i] = self.signal[0]
            elif i + int_part > len(self.signal) - 1 - 1:
                shifted[i] = self.signal[len(self.signal) - 1]
            else:
                shifted[i] = (1 - float_part) * self.signal[i + int_part] + float_part * self.signal[i + int_part + 1]
        return shifted


class PeakedSignal:

    def __init__(self, signal: dict[int, float], delta: float = 0.0):
        self.signal = signal
        self.delta = delta  # shifts the signal horizontally; private to this class; x = index + delta

    def __getitem__(self, x: float):
        base = int(math.floor(x - self.delta))
        rem = x - self.delta - base
        try:
            value = (1 - rem) * self.signal[base] + rem * self.signal[base + 1]
            return value
        except KeyError:
            return None

    def in_xrange(self, x):
        base = int(math.floor(x - self.delta))
        if base >= min(self.signal.keys()) and base+1 <= max(self.signal.keys()):
            return True
        else:
            return False

    def get_symmetric_x(self, x_sym_axis: float):
        x_sym = []
        for index in self.signal:
            x = index + self.delta
            if x < x_sym_axis:
                counterpart = x_sym_axis + (x_sym_axis - x)
                if self.in_xrange(counterpart):
                    x_sym.append((x, counterpart))
        return x_sym

    def penalty(self, shift: float = 0):
        obj = 0.0
        cnt = 0
        for x in self.get_symmetric_x(shift):
            try:
                obj += (self[x[0]] - self[x[1]]) ** 2
                cnt += 1
            except TypeError:
                pass
        try:
            return obj / cnt
        except ZeroDivisionError:
            return 0.0

    def probe(self):
        for step in range(10):
            print(self.penalty(shift=-0.5 + step * 0.1))

    def find_maximum(self, search_range, init_est=None):
        if not init_est:
            i_max = max(self.signal, key=self.signal.get)  # het symmetriepunt zal in de buurt van het maximum liggen
            init_est = i_max + self.delta
        res = gssrec(self.penalty, init_est - search_range, init_est + search_range, tol=1e-3)
        print(f"res = {res}")
        opti = sum(res)/2.0
        for x in self.get_symmetric_x(opti):
            print(f"x: {x[0]}, {x[1]}: {self[x[0]]}, {self[x[1]]}")
        return opti



if __name__ == "__main__":
    signal = {
        -7: 5666403063.441576,
        -6: 5668677787.291723,
        -5: 5660514310.462496,
        -4: 5651056375.421531,
        -3: 5646310296.441126,
        -2: 5653537814.460731,
        -1: 5674071426.809031,
        0: 5715333458.689628,
        1: 5765690470.676269,
        2: 5825552411.130662,
        3: 5787909723.316826,
        4: 5717680321.974794,
        5: 5678911105.632735,
        6: 5664045693.490227,
        7: 5649971354.81946,
             }
    peakedSignal = PeakedSignal(signal, -2.0)
    peakedSignal.probe()
    peakedSignal.find_maximum(2, init_est=0.2)


    x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    sig = SignalShift(x)
    shift = 2
    print(f"shifted over {shift}: {sig.do_shift(shift)}")
    shift = -2
    print(f"shifted over {shift}: {sig.do_shift(shift)}")
    shift = -0.2
    print(f"shifted over {shift}: {sig.do_shift(shift)}")
    shift = 0.2
    print(f"shifted over {shift}: {sig.do_shift(shift)}")
