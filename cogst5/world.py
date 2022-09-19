from cogst5.base import *
from cogst5.utils import *


class BbwWorld(BbwObj):
    _zones = ["normal", "amber", "red"]

    def __init__(self, uwp, zone, hex, *args, **kwargs):
        self.set_uwp(uwp)
        self.set_zone(zone)
        self.set_hex(hex)

        super().__init__(*args, **kwargs)

    def uwp(self):
        return self._uwp

    def set_uwp(self, v):
        v = str(v)
        v = v.replace("-", "")
        BbwUtils.test_hexstr("uwp", v, [8])
        self._uwp = v

    def zone(self):
        return self._zone

    def set_zone(self, v):
        v = str(v)
        v = BbwUtils.get_objs(self._zones, v, only_one=True)[0]
        self._zone = v

    def d_km(self):
        return 1600 * self.SIZE()[1]

    def set_hex(self, v):
        v = str(v)
        if len(v) != 4:
            raise AttributeError(f"the hex location {v} must be 4 digits long!")

        col = int(v[0:2])
        row = int(v[2:4])
        self._hex = v

    def hex(self):
        return self._hex

    def col(self):
        return int(self._hex[0:2])

    def row(self):
        return int(self._hex[2:4])

    def SP(self):
        return self.uwp()[0], int(self.uwp()[0], 36)

    def SIZE(self):
        return self.uwp()[1], int(self.uwp()[1], 36)

    def ATM(self):
        return self.uwp()[2], int(self.uwp()[2], 36)

    def HYDRO(self):
        return self.uwp()[3], int(self.uwp()[3], 36)

    def POP(self):
        return self.uwp()[4], int(self.uwp()[4], 36)

    def GOV(self):
        return self.uwp()[5], int(self.uwp()[5], 36)

    def LAW(self):
        return self.uwp()[6], int(self.uwp()[6], 36)

    def TL(self):
        return self.uwp()[7], int(self.uwp()[7], 36)

    @staticmethod
    def distance(w0, w1):
        x0, x1, y0, y1 = w0.col(), w1.col(), w0.row(), w1.row()

        if (x1 < x0 and y1 > y0) or (x1 > x0 and y1 > y0):
            x0, x1, y0, y1 = x1, x0, y1, y0

        n_steps = 0
        while x0 != x1 and y0 != y1:
            n_steps += 1
            y0 -= x0 % 2
            x0 += 2 * (x1 > x0) - 1

        return n_steps + abs(y0 - y1) + abs(x0 - x1)

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.name(), self.uwp()]
        else:
            return [
                self.name(),
                self.uwp(),
                self.d_km(),
                self.zone(),
                self.hex(),
            ]

    def __str__(self, is_compact=True):
        return BbwUtils.print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["name", "uwp"]
        else:
            return [
                "name",
                "uwp",
                "d_km",
                "zone",
                "hex",
            ]


# a = BbwWorld(name="feri", uwp="B384879-B", zone="normal", hex="2005")
# print(a.__str__(False))
# b = BbwWorld(name="regina", uwp="A788899-C", zone="normal", hex="1923")
#
# print(a.SIZE())
# print(a.d_km())
# #
# # print(BbwWorld.distance(a, b))
# #
# exit()
