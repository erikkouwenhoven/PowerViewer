from dataclasses import dataclass


@dataclass
class Signal:
    name: str
    data: list[float]
    unit: str
    num: int = -1  # iterator

    def fix_signal(self):
        fixed = Signal(name=self.name, data=len(self) * [0.0], unit=self.unit)
        for i, value in enumerate(self):
            if value:
                fixed[i] = value
            else:
                if 0 < i < len(self) - 1:
                    if self[i - 1] is not None and self[i + 1] is not None:
                        fixed[i] = (self[i - 1] + self[i + 1]) / 2.0
                    elif self[i - 1] is not None:
                        fixed[i] = self[i - 1]
                    elif self[i + 1] is not None:
                        fixed[i] = self[i + 1]
                    else:
                        fixed[i] = 0.0
                else:
                    if i > 0:
                        if self[len(self) - 1] is None:
                            fixed[i] = 0.0
                        else:
                            fixed[i] = self[len(self) - 1]
                    else:
                        if self[0] is None:
                            fixed[i] = 0.0
                        else:
                            fixed[i] = self[0]
        return fixed

    def __iter__(self):
        return self

    def __next__(self):
        if self.num + 1 >= len(self.data):
            self.num = -1
            raise StopIteration
        else:
            self.num += 1
            return self.data[self.num]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def min(self):
        return min(self.data)

    def max(self):
        return max(self.data)

    def serialize(self, idx_range=None):
        return {
            "name": self.name,
            "data": self.data if idx_range is None else [self.data[i] for i in idx_range],
            "unit": self.unit
        }

    @classmethod
    def unserialize(cls, stream: dict):
        return cls(name=stream["name"], data=stream["data"], unit=stream["unit"])

    def __str__(self):
        return f"{self.name}: {self.data}"
