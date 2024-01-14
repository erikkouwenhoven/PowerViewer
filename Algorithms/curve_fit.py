from abc import ABC, abstractmethod
import math
import numpy as np


class CurveFit(ABC):
    """
    De abstract superclass voor niet-lineaire 1-D curvefitting met Newton-Gauss.

    Concrete subclasses moeten de functies implementeren
        func            : de functiebeschrijving
        parmDeriv       : afgeleide naar de parameters
        initEstimation  : beginschatting
        NAME            : naam van de functie
    """

    MIN_STEP = 1.0E-9
    MAX_ITER = 20
    NAME = ""  # defined in subclass

    def __init__(self, xdata, ydata):
        self.xdata = xdata
        self.ydata = ydata
        self.parms = []

    @staticmethod
    @abstractmethod
    def func(x, parms):
        return

    @abstractmethod
    def parmDeriv(self, x):
        return

    @abstractmethod
    def initEstimation(self):
        return

    def residualVector(self):
        return np.array([self.ydata[i] - self.func(self.xdata[i], self.parms) for i in range(len(self.xdata))])

    def jacobian(self):
        return -np.array([self.parmDeriv(x) for x in self.xdata])

    def solve(self):
        self.parms = self.initEstimation()
        stopCondition = False
        nIter = 0
        while stopCondition is False:
            J = self.jacobian()
            r = self.residualVector()
            A = np.matmul(J.T, J)
            b = np.matmul(-J.T, r)
            try:
                step = np.linalg.solve(A, b)
            except np.linalg.LinAlgError:
                self.parms = []
                return
            self.parms += step
            nIter += 1
            if np.linalg.norm(step) < self.MIN_STEP or nIter == self.MAX_ITER:
                stopCondition = True
            print("iteration {}: norm step {}".format(nIter, np.linalg.norm(step)))

    def getParameters(self):
        return self.parms


class CurveFitFloatingExponent(CurveFit):
    """
    Implementation of Newton-Gauss algorithm for the function

        y = a.e**(b.x) + c

    """

    NAME = 'a.e**(b.x) + c'

    def __init__(self, xdata, ydata):
        super().__init__(xdata, ydata)

    @staticmethod
    def func(x, parms):
        return parms[0]*math.exp(parms[1] * x) + parms[2]

    def parmDeriv(self, x):
        fac = math.exp(self.parms[1] * x)
        return [fac, self.parms[0] * fac * x, 1]

    def initEstimation(self):
        xmin = min(self.xdata)
        imin = self.xdata.index(xmin)
        xmax = max(self.xdata)
        imax = self.xdata.index(xmax)
        parms = [0.0] * 3
        parms[2] = self.ydata[imax] - 0.1*(self.ydata[imin] - self.ydata[imax])  # het level; de 0.1 is om ervoor te zorgen dat je verderop geen divzero krijgt
        parms[1] = math.log((self.ydata[imax] - parms[2])/(self.ydata[imin] - parms[2])) / (self.xdata[imax] - self.xdata[imin])
        parms[0] = sum([(self.ydata[imax] - parms[2]) / math.exp(parms[1] * self.xdata[imax]),
                        (self.ydata[imin] - parms[2]) / math.exp(parms[1] * self.xdata[imin])]) / 2.0
        return parms

    def half_value_time(self):
        return -math.log(2.0)/self.parms[1]


if __name__ == "__main__":
    curveFit = CurveFitFloatingExponent([142, 127, 108, 92, 81, 59, 39, 29], [60, 118.82, 232.27, 391.48, 546.09, 1095.3, 2184.4, 3252])
    curveFit.solve()
    print("{}".format(curveFit.parms))
