from Utils.config import Config


class UnitStandardizer:
    """
    """

    c_UNITS = ({'W': 1, 'kW': 1000}, {'Wh': 1, 'kWh': 1000})

    def __init__(self):
        pass

    def execute(self, signal_units, data, signals):
        for signal in signals:
            unit = signal_units[signal]
            if self.must_convert(unit):
                data[signal] = self.convert(data[signal], unit)

    def must_convert(self, unit):
        """True if the given unit should be converted to a preferred unit, i.e.,
        it is a defined unit but not preferred"""
        if self.is_defined_unit(unit):
            return unit not in Config().getPreferredUnits()

    def is_defined_unit(self, unit):
        for unit_type in self.c_UNITS:
            for defined_unit in unit_type:
                if unit == defined_unit:
                    return True
        return False

    def convert(self, signal, unit):
        conv_fac = self.get_conversion_factor(unit)
        return [item * conv_fac if item is not None else 0.0 for item in signal]

    def get_conversion_factor(self, unit):
        for unit_type in self.c_UNITS:
            for defined_unit in unit_type:
                if unit == defined_unit:
                    for pref_unit in Config().getPreferredUnits():
                        if pref_unit in unit_type:
                            return unit_type[unit] / unit_type[pref_unit]
