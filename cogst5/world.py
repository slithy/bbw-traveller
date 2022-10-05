from cogst5.base import *
from cogst5.utils import *


class WorldCodes:
    def __init__(self, name, description, restrictions):
        self._name = name
        self._description = description
        self._restrictions = restrictions

    def __eq__(self, other):
        for k, v in self.restrictions().items():
            if getattr(other, k)()[1] not in v:
                return False

        return True

    def restrictions(self):
        return self._restrictions

    def name(self):
        return self._name

    def description(self):
        return self._description

    def __str__(self, detail_lvl=0):
        if detail_lvl == 0:
            return self.name
        return f"{self.description()} (`{self.name()}`)"


class BbwWorld(BbwObj):
    _zones = ["normal", "amber", "red"]
    _trade_code_table = BbwUtils.gen_dict(
        [
            WorldCodes(
                "Ag", "agricultural", {"ATM": list(range(4, 10)), "HYDRO": list(range(4, 9)), "POP": list(range(5, 8))}
            ),
            WorldCodes("As", "asteroid", {"SIZE": [0], "ATM": [0], "HYDRO": [0]}),
            WorldCodes("Ba", "barren", {"GOV": [0], "POP": [0], "LAW": [0]}),
            WorldCodes("De", "desert", {"ATM": list(range(2, 10)), "HYDRO": [0]}),
            WorldCodes("Fl", "fluid oceans", {"ATM": list(range(10, 37)), "HYDRO": list(range(1, 37))}),
            WorldCodes("Ga", "garden", {"SIZE": list(range(6, 9)), "ATM": [5, 6, 8], "HYDRO": list(range(5, 8))}),
            WorldCodes(
                "Hi",
                "high population",
                {
                    "POP": list(range(9, 37)),
                },
            ),
            WorldCodes(
                "Ht",
                "high technology",
                {
                    "TL": list(range(12, 37)),
                },
            ),
            WorldCodes("Ic", "ice-capped", {"ATM": [0, 1], "HYDRO": list(range(1, 37))}),
            WorldCodes("In", "industrial", {"ATM": [0, 1, 2, 4, 7, 9, 10, 11, 12], "POP": list(range(9, 37))}),
            WorldCodes(
                "Ln",
                "low population",
                {
                    "POP": [1, 2, 3],
                },
            ),
            WorldCodes("Lt", "low technology", {"POP": list(range(1, 37)), "TL": list(range(0, 6))}),
            WorldCodes(
                "Na",
                "non-agricultural",
                {"ATM": list(range(0, 4)), "HYDRO": list(range(0, 4)), "POP": list(range(6, 37))},
            ),
            WorldCodes("Ni", "non-industrial", {"POP": list(range(4, 7))}),
            WorldCodes("Po", "poor", {"ATM": list(range(2, 6)), "HYDRO": list(range(0, 4))}),
            WorldCodes(
                "Ri",
                "rich",
                {
                    "ATM": [6, 8],
                    "POP": [6, 7, 8],
                    "GOV": list(range(4, 10)),
                },
            ),
            WorldCodes("Va", "vacuum", {"ATM": [0]}),
            WorldCodes("Wa", "waterworld", {"HYDRO": list(range(10, 37)), "ATM": [*range(3, 10), *range(13, 37)]}),
        ]
    )

    def __init__(self, uwp, zone, hex, sector, *args, **kwargs):
        self.set_uwp(uwp)
        self.set_zone(zone)
        self.set_hex(hex)
        self.set_sector(sector)
        self.set_people()
        self.set_trade_codes()
        self.set_suppliers()

        super().__init__(*args, **kwargs)

    def set_suppliers(self):
        self._suppliers = BbwContainer(name="suppliers")

    def set_supply(self, bbwtrade, t, names=""):
        obj = [i for i, _ in self.suppliers().get_objs(name=names).objs()]
        for i in obj:
            i.set_supply(bbwtrade, self, t)

    def suppliers(self):
        if not hasattr(self, "_suppliers"):
            self.set_suppliers()
        return self._suppliers

    def set_people(self):
        self._people = BbwContainer(name="people")

    def people(self):
        if not hasattr(self, "_people"):
            self.set_people()
        return self._people

    def uwp(self):
        return self._uwp

    def set_trade_codes(self, d=None):
        if d is not None:
            if type(d) is not set:
                d = eval(d)

            self._trade_codes = set()
            for k in d:
                self.set_trade_code(k, 1)
            return

        self._trade_codes = set()
        for k, v in self._trade_code_table.items():
            if v == self:
                self.set_trade_code(k, 1)

    def set_trade_code(self, name, value=None):
        if value is None:
            name, value = eval(name)

        if name not in BbwWorld._trade_code_table:
            raise InvalidArgument(
                f"Unknown trade code `{name}`. Possible options: `{', '.join(BbwWorld._trade_code_table.keys())}`"
            )
        if value is None:
            self.trade_codes().discard(name)
            return

        self.trade_codes().add(name)

    def trade_codes(self):
        if not hasattr(self, "_trade_codes"):
            self.set_trade_codes()
        return self._trade_codes

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
        s = BbwUtils.print_table(self._str_table(detail_lvl), headers=self._header(detail_lvl), detail_lvl=detail_lvl)
        if detail_lvl == 0:
            return s

        h = ["starport", "atm", "hydro", "pop", "gov", "law", "TL"]
        t = [self.SP()[0], self.ATM()[1], self.HYDRO()[1], self.POP()[1], self.GOV()[1], self.LAW()[1], self.TL()[1]]
        s += BbwUtils.print_table(t, headers=h, detail_lvl=1)

        if len(self.people()):
            s += self.people().__str__(1)

        s += f"trade codes: " + ", ".join([BbwWorld._trade_code_table[i].__str__(1) for i in self.trade_codes()])
        s += "\n"
        s += self.suppliers().__str__(detail_lvl=1)

        return s

    @staticmethod
    def _header(detail_lvl=0):
        if detail_lvl == 0:
            return ["name", "uwp"]
        else:
            return ["name", "uwp", "d_km", "zone", "hex", "sector"]


# a = BbwWorld(name="feri", uwp="B384879-B", zone="normal", hex="1904", sector=(-4, 1))
# a.set_trade_code("('Ri', 1)")
#
#
# exit()
# b = BbwWorld(name="regina", uwp="A788899-C", zone="normal", hex="2005", sector=(-4, 1))
# print(b.__str__(1))
# exit()
#
# print(a.SIZE())
# print(a.d_km())
# #
# print(BbwWorld.distance(a, b))
# #
# exit()
