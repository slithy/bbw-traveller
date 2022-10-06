from cogst5.base import *


class BbwItem(BbwObj):
    def __init__(self, TL=None, value=None, *args, **kwargs):
        self.set_value(value)
        self.set_TL(TL)

        super().__init__(*args, **kwargs)

    def TL(self):
        return self._TL

    def value(self, is_per_obj=False):
        return self._per_obj(self._value, is_per_obj)

    def set_value(self, v):
        if v is None:
            v = 0
        v = int(v)
        BbwUtils.test_geq("value", v, 0)
        self._value = v

    def set_TL(self, v):
        if v is None:
            v = 0
        v = int(v)
        BbwUtils.test_geq("TL", v, 0)
        BbwUtils.test_leq("TL", v, 30)
        self._TL = v

    def _str_table(self, detail_lvl=0):
        if detail_lvl == 0:
            return [self.count(), self.name(), self.capacity() if self.capacity() else None]
        else:
            return [
                self.count(),
                self.name().replace("/", "\n"),
                self.capacity() if self.capacity() else None,
                self.TL() if self.TL() else None,
                self.value() if self.value() else None,
            ]

    def __str__(self, detail_lvl=0):
        return BbwUtils.print_table(self._str_table(detail_lvl), headers=self._header(detail_lvl))

    @staticmethod
    def _header(detail_lvl=0):
        if detail_lvl == 0:
            return ["count", "name", "capacity"]
        else:
            return ["count", "name", "capacity", "TL", "value"]


class BbwItemFactory:
    _tickets = [1000, 1600, 2600, 4400, 8500, 32000]

    _lib = [
        BbwItem(name="luggage, high", capacity=1, count=1, TL=0, value=0),
        BbwItem(name="luggage, middle", capacity=0.1, count=1, TL=0, value=0),
        BbwItem(name="mail", capacity=5, count=1, TL=0, value=25000),
        BbwItem(name="freight, major", capacity=10, count=1, TL=0, value=0),
        BbwItem(name="freight, minor", capacity=5, count=1, TL=0, value=0),
        BbwItem(name="freight, incidental", capacity=1, count=1, TL=0, value=0),
        BbwItem(name="fuel, refined", capacity=1, count=1, TL=0, value=500),
        BbwItem(name="fuel, unrefined", capacity=1, count=1, TL=0, value=100),
        BbwItem(name="common electronics", capacity=1, count=1, TL=0, value=20000),
        BbwItem(name="common industrial goods", capacity=1, count=1, TL=0, value=10000),
        BbwItem(name="common manufactured goods", capacity=1, count=1, TL=0, value=20000),
        BbwItem(name="common raw materials", capacity=1, count=1, TL=0, value=5000),
        BbwItem(name="common consumables", value=500, capacity=1, count=1, TL=0),
        BbwItem(name="common ore", value=1000, capacity=1, count=1, TL=0),
        BbwItem(name="advanced electronics", value=100000, capacity=1, count=1, TL=0),
        BbwItem(name="advanced machine parts", value=75000, capacity=1, count=1, TL=0),
        BbwItem(name="advanced manufactured goods", value=100000, capacity=1, count=1, TL=0),
        BbwItem(name="advanced weapons", value=150000, capacity=1, count=1, TL=0),
        BbwItem(name="advanced vehicles", value=180000, capacity=1, count=1, TL=0),
        BbwItem(name="biochemicals", value=50000, capacity=1, count=1, TL=0),
        BbwItem(name="crystals and gems", value=20000, capacity=1, count=1, TL=0),
        BbwItem(name="cybernetics", value=250000, capacity=1, count=1, TL=0),
        BbwItem(name="live animals", value=10000, capacity=1, count=1, TL=0),
        BbwItem(name="luxury consumables", value=20000, capacity=1, count=1, TL=0),
        BbwItem(name="luxury goods", value=200000, capacity=1, count=1, TL=0),
        BbwItem(name="medical supplies", value=50000, capacity=1, count=1, TL=0),
        BbwItem(name="petrochemicals", value=10000, capacity=1, count=1, TL=0),
        BbwItem(name="pharmaceuticals", value=100000, capacity=1, count=1, TL=0),
        BbwItem(name="polymers", value=7000, capacity=1, count=1, TL=0),
        BbwItem(name="precious metals", value=50000, capacity=1, count=1, TL=0),
        BbwItem(name="radioactives", value=1000000, capacity=1, count=1, TL=0),
        BbwItem(name="robots", value=400000, capacity=1, count=1, TL=0),
        BbwItem(name="spices", value=6000, capacity=1, count=1, TL=0),
        BbwItem(name="textiles", value=3000, capacity=1, count=1, TL=0),
        BbwItem(name="uncommon ore", value=5000, capacity=1, count=1, TL=0),
        BbwItem(name="uncommon raw materials", value=20000, capacity=1, count=1, TL=0),
        BbwItem(name="wood", value=1000, capacity=1, count=1, TL=0),
        BbwItem(name="vehicles", value=15000, capacity=1, count=1, TL=0),
        BbwItem(name="biochemicals, illegal", value=50000, capacity=1, count=1, TL=0),
        BbwItem(name="cybernetics, illegal", value=250000, capacity=1, count=1, TL=0),
        BbwItem(name="drugs, illegal", value=100000, capacity=1, count=1, TL=0),
        BbwItem(name="luxuries, illegal", value=50000, capacity=1, count=1, TL=0),
        BbwItem(name="weapons, illegal", value=150000, capacity=1, count=1, TL=0),
    ]

    @staticmethod
    def make(name, n_sectors=1, count=None, TL=None, value=None, capacity=None):
        if count == 0:
            return None

        item = copy.deepcopy(BbwUtils.get_objs(raw_list=BbwItemFactory._lib, name=name, only_one=True)[0])
        if "luggage" in item.name():
            item.set_name(f"{item.name()} (ns: {n_sectors})")

        if "freight" in item.name():
            item.set_capacity(d20.roll("1d6").total * item.capacity())
            item.set_value(BbwItemFactory._tickets[int(n_sectors) - 1] * item.capacity())
            item.set_size(item.capacity())
            item.set_name(f"{item.name()} (ns: {n_sectors}, lot: {item.capacity()} tons)")

        if value is not None:
            item.set_value(value)
        if TL is not None:
            item.set_TL(TL)
        if capacity is not None:
            item.set_capacity(capacity)
            item.set_size(item.capacity())
        if count is not None:
            item.set_count(count)

        return item
