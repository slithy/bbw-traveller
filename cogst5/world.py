from cogst5.base import *
from cogst5.utils import *


class BbwWorld(BbwObj):
    _zones = ["normal", "amber", "red"]

    def __init__(self, uwp, zone, hex, sector, *args, **kwargs):
        self.set_uwp(uwp)
        self.set_zone(zone)
        self.set_hex(hex)
        self.set_sector(sector)
        self.set_people()

        super().__init__(*args, **kwargs)

    def set_people(self):
        self._people = BbwContainer(name="people")

    def people(self):
        if not hasattr(self, "_people"):
            self.set_people()
        return self._people

    def uwp(self):
        return self._uwp

    def sector(self):
        return self._sector

    def set_sector(self, v):
        if type(v) is str:
            v = eval(v)

        self._sector = v

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

    def hex_x(self):
        return int(self._hex[0:2])

    def hex_y(self):
        return int(self._hex[2:4])

    def sec_x(self):
        return self.sector()[0]

    def sec_y(self):
        return self.sector()[1]

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
        x0, y0, xs0, ys0, x1, y1, xs1, ys1 = (
            w0.hex_x(),
            w0.hex_y(),
            w0.sec_x(),
            w0.sec_y(),
            w1.hex_x(),
            w1.hex_y(),
            w1.sec_x(),
            w1.sec_y(),
        )
        return BbwUtils.distance(
            *BbwUtils.hex_2_cube(*BbwUtils.local_2_global(x0, y0, xs0, ys0)),
            *BbwUtils.hex_2_cube(*BbwUtils.local_2_global(x1, y1, xs1, ys1)),
        )

    def _str_table(self, detail_lvl=0):
        if detail_lvl == 0:
            return [self.name(), self.uwp()]
        else:
            return [self.name(), self.uwp(), self.d_km(), self.zone(), self.hex(), str(self.sector())]

    def __str__(self, detail_lvl=0):
        s = BbwUtils.print_table(self._str_table(detail_lvl), headers=self._header(detail_lvl), detail_lvl=1)
        if detail_lvl == 0:
            return s

        s += self.people().__str__(1)
        return s

    @staticmethod
    def _header(detail_lvl=0):
        if detail_lvl == 0:
            return ["name", "uwp"]
        else:
            return ["name", "uwp", "d_km", "zone", "hex", "sector"]


# a = BbwWorld(name="feri", uwp="B384879-B", zone="normal", hex="1904", sector=(-4, 1))
# print(a.__str__(False))
# b = BbwWorld(name="regina", uwp="A788899-C", zone="normal", hex="2005", sector=(-4, 1))
#
# print(a.SIZE())
# print(a.d_km())
# #
# print(BbwWorld.distance(a, b))
# #
# exit()
