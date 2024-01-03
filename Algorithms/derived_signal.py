from Models.signal import Signal


class DerivedSignal:

    def __init__(self, name: str, formula_text: str, data: dict[str, Signal]):
        self.name = name
        self.formula = Formula(formula_text, data)  # bijv. SOLAR - CURRENT_PRODUCTION_PHASE1 + CURRENT_USAGE_PHASE1
        self.data = data

    def get(self) -> Signal:
        op = self.formula.evaluate()
        if self.data and all((operand in self.data for operand in op.all_operands())) is True:
            return op.exec()



class Operation:
    """
    Holder for binary operation such as '+', '-'
    """

    def __init__(self, operator, operand1, operand2, data: dict[str, Signal]):
        self.operator = operator
        self.operand1 = operand1
        self.operand2 = operand2
        self.data = data

    def next_level(self, operator, operand2):
        self.operand1 = Operation(self.operator, self.operand1, self.operand2, self.data)
        self.operator = operator
        self.operand2 = operand2

    def exec(self) -> Signal:
        if type(self.operand1) == Operation:
            result = self.operand1.exec()
        else:
            result = self.data[self.operand1]
        result = result.fix_signal()
        signal2 = self.data[self.operand2].fix_signal()
        if self.operator == '+':
            return Signal(name="sum", data=[result[i] + signal2[i] for i in range(len(result))], unit=result.unit)
        elif self.operator == '-':
            return Signal(name="diff", data=[result[i] - signal2[i] for i in range(len(result))], unit=result.unit)

    def all_operands(self) -> list[str]:
        if type(self.operand1) == Operation:
            return self.operand1.all_operands() + [self.operand2]
        else:
            return [self.operand1, self.operand2]


class Formula:
    """
    Holds a formule such as 'A + B - C'.
    Converts into a possibly stacked operation.
    """

    def __init__(self, formula_text: str, data: dict[str, Signal]):
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

    def words(self) -> list[str]:
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
