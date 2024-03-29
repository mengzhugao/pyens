import matplotlib.pyplot as plt
import numpy as np
from schemdraw import Drawing
import schemdraw.elements as elm
from pyens.elements import Base, Dynamical


class OCV(Base):
    def __init__(self, name, soc: list = None, ocv: list = None):
        Base.__init__(self, type="soc_ocv_curve", name=name)
        if soc is None and ocv is None:
            self.ocv = [3.3, 3.5, 3.55, 3.6, 3.65, 3.68, 3.70, 3.8, 3.95, 4.0, 4.1]
            self.soc = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        else:
            self.ocv = ocv
            self.soc = soc

    def display(self):
        plt.figure()
        plt.xlabel("soc")
        plt.ylabel("ocv")
        plt.title("curve")
        plt.plot(self.soc, self.ocv)
        plt.show()

    def soc2ocv(self, soc):
        return np.interp(soc, self.soc, self.ocv)


class EcmCell(Base, Dynamical):
    def __init__(self, name,
                 parameters: dict = None,
                 curve: OCV = OCV('default')):
        Base.__init__(self, type="EMC_Cell_Model", name=name)
        Dynamical.__init__(self)
        if parameters is None:
            parameters = {
                "R0": 0.05,
                "R1": 0.022,
                "C1": 1500,
                "R2": 0.019,
                "C2": 65000,
                "CAP": 1.1,
                "ce": .99,
                "v_limits": [2.5, 4.5],
                "SOC_RANGE": [-5., 105.0],
            }
        self.__parameters = parameters
        self.ocv_curve = curve

    def update_rpm(self, prm):
        self.__parameters = prm

    def prm(self, name):
        return self.__parameters[name]

    def ode(self, t, x, current_series):

        current = current_series(t)

        # dSoC/dt

        # SOC constrain

        if current > 0 and x[2] > self.prm("SOC_RANGE")[0]:
            dSoC = -1 / self.prm("CAP") * current / 36
        elif current < 0 and x[2] < self.prm("SOC_RANGE")[1]:
            dSoC = (
                    -1
                    / self.prm("CAP") * current * self.prm("ce")
                    / 36
            )
        else:
            dSoC = 0.

        # dU1/dt
        du1 = (
                1
                / self.prm("C1")
                * (current - 1 / self.prm("R1") * x[0])
        )
        # dU2/dt
        du2 = (
                1
                / self.prm("C2")
                * (current - 1 / self.prm("R2") * x[1])
        )

        return np.array([du1, du2, dSoC])

    def out(self, current, x):
        vt = (
                self.ocv_curve.soc2ocv(x[2])
                - x[0]
                - x[1]
                - current * self.prm("R0")
        )
        return vt

    def display(self):
        with Drawing() as d:
            d.push()
            d += elm.BatteryCell().up()
            d += (R0 := elm.Resistor().right().label(str(self.prm('R0'))))
            d += elm.CurrentLabel(top=False, length=1.0, ofst=.6).right().at(R0)
            d.push()
            d += elm.Resistor().right().label(str(self.prm('R1')))
            d.pop()
            d += elm.Line(l=1.5).down()
            d += elm.Capacitor().right().label(str(self.prm('C1')))
            d += elm.Line(l=1.5).up()
            d += elm.Line(l=1.5).right()
            d.push()
            d += elm.Resistor().right().label(str(self.prm('R2')))
            d.pop()
            d += elm.Line(l=1.5).down()
            d += elm.Capacitor().right().label(str(self.prm('C2')))
            d += elm.Line(l=1.5).up()
            d += elm.Line(l=1).right()
            d += elm.Dot().color('blue')
            d.pop()
            d += elm.Line(l=11.5).right()
            d += elm.Dot().color('blue')
