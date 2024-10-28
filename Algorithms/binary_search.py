from enum import Enum, auto

"""
Binary search algorithm

Given an array of floats and a value, the index in the array corresponding to the nearest value is returned.
The array should be in increasing order.
"""


class Rounding(Enum):

    UP = auto()
    DOWN = auto()
    NEAR = auto()


def b_search(array: list[float], value: float, rounding: Rounding = Rounding.NEAR) -> int:
    lo = 0
    hi = len(array) - 1
    while lo < hi:
        m = int((lo + hi) / 2)
        if array[m] < value:
            lo = m
        elif array[m] > value:
            hi = m
        elif array[m] == value:
            return m
        if hi - lo <= 1:
            if rounding is Rounding.NEAR:
                return lo if value - array[lo] < array[hi] - value else hi
            elif rounding is Rounding.UP:
                return hi
            elif rounding is Rounding.DOWN:
                return lo


def interval_to_range(data: list[float], low_value: float, hi_value: float) -> range:
    if (lo := b_search(data, low_value, Rounding.DOWN)) is not None:
        if (hi := b_search(data, hi_value, Rounding.UP)) is not None:
            return range(lo, hi + 1)


if __name__ == "__main__":
    array = [1, 3, 4, 5, 6, 7, 8]
    value = 3
    print(f"value {value} is found at position {b_search(array, value)} in array {array}")

    array = [1, 3, 4, 5, 6, 7, 8]
    value = 2
    print(f"value {value} is found at position {b_search(array, value)} in array {array}")

    array = [1, 3, 4, 5, 6, 7, 8]
    value = 0
    print(f"value {value} is found at position {b_search(array, value)} in array {array}")

    array = [1, 3, 4, 5, 6, 7, 8]
    value = 9
    print(f"value {value} is found at position {b_search(array, value)} in array {array}")

    array = [1, 3, 4, 5, 6, 7, 8]
    value = 4.2
    print(f"value {value} is found at position {b_search(array, value)} in array {array}")

    array = [1, 3, 4, 5, 6, 7, 8]
    value = 4.8
    print(f"value {value} is found at position {b_search(array, value)} in array {array}")

    array = [8, 7, 6, 5, 4, 3, 1]
    value = 0
    print(f"value {value} is found at position {b_search(array, value)} in array {array}")
