class DerivedSignal:

    def __init__(self, name: str, formula_text: str, data: dict[str, list[float]]):
        self.name = name
        self.formula = Formula(formula_text, data)  # bijv. SOLAR - CURRENT_PRODUCTION_PHASE1 + CURRENT_USAGE_PHASE1

    def get(self):
        op = self.formula.evaluate()
        return op.exec()


class Operation:
    """
    Holder for binary operation such as '+', '-'
    """

    def __init__(self, operator, operand1, operand2, data):
        self.operator = operator
        self.operand1 = operand1
        self.operand2 = operand2
        self.data = data

    def next_level(self, operator, operand2):
        self.operand1 = Operation(self.operator, self.operand1, self.operand2, self.data)
        self.operator = operator
        self.operand2 = operand2

    def exec(self):
        if type(self.operand1) == Operation:
            result = self.operand1.exec()
        else:
            result = self.data[self.operand1]
        result = self.fix_signal(result)
        signal2 = self.fix_signal(self.data[self.operand2])
        if self.operator == '+':
            return [result[i] + signal2[i] for i in range(len(result))]
        elif self.operator == '-':
            return [result[i] - signal2[i] for i in range(len(result))]\

    @staticmethod
    def fix_signal(signal: list[float]) -> list[float]:  # TODO deze functie hier niet hier
        fixed = len(signal) * [0.0]
        for i, value in enumerate(signal):
            if value:
                fixed[i] = value
            else:
                if 0 < i < len(signal) - 1:
                    if signal[i - 1] is not None and signal[i + 1] is not None:
                        fixed[i] = (signal[i - 1] + signal[i + 1]) / 2.0
                    elif signal[i - 1] is not None:
                        fixed[i] = signal[i - 1]
                    elif signal[i + 1] is not None:
                        fixed[i] = signal[i + 1]
                    else:
                        fixed[i] = 0.0
                        # raise RuntimeError("fix_signal")
                else:
                    if i > 0:
                        if signal[len(signal) - 1] is None:
                            fixed[i] = 0.0
                            # raise RuntimeError("fix_signal")
                        fixed[i] = signal[len(signal) - 1]
                    else:
                        if signal[0] is None:
                            fixed[i] = 0.0
                            # raise RuntimeError("fix_signal")
                        fixed[i] = signal[0]
        return fixed


class Formula:
    """
    Holds a formule such as 'A + B - C'.
    Converts into a possibly stacked operation.
    """

    def __init__(self, formula_text: str, data):
        self.formula_text = formula_text
        self.data = data
        self.num = 0  # iterator

    def check_syntax(self):
        pass  # TODO

    def evaluate(self) -> Operation:
        binary_fragment = next(self)
        op = Operation(binary_fragment[1], binary_fragment[0], binary_fragment[2], self.data)
        try:
            while next_binary_fragment := next(self):
                op.next_level(next_binary_fragment[0], next_binary_fragment[1])
        except StopIteration:
            return op

    def words(self):
        return self.formula_text.split()

    def __iter__(self):
        return self

    def __next__(self):
        if self.num >= len(self.words()):
            raise StopIteration
        else:
            if self.num == 0:
                self.num = 3
                return self.words()[0], self.words()[1], self.words()[2]
            else:
                self.num += 2
                return self.words()[self.num - 2], self.words()[self.num - 2 + 1]


if __name__ == "__main__":
    data = {"SOLAR": [1, 1, 1], "CURRENT_PRODUCTION_PHASE1": [6, 6, 6], "CURRENT_USAGE_PHASE1": [3, 3, 3], "NOG_IETS": [12, 12, 12]}
    derivedSignal = DerivedSignal("verbruik", "SOLAR - CURRENT_PRODUCTION_PHASE1 + CURRENT_USAGE_PHASE1 -  NOG_IETS", data)
    print(derivedSignal.get())
