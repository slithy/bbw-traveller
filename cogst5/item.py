from cogst5.base import *


class BbwItem(BbwObj):
    def __init__(self, TL=0, value=0, *args, **kwargs):
        self.set_value(value)
        self.set_TL(TL)

        super().__init__(*args, **kwargs)

    def TL(self):
        return self._TL

    def value(self):
        return self._value * self.count()

    def set_TL(self, v):
        v = int(v)
        BbwUtils.test_geq("TL", v, 0)
        BbwUtils.test_leq("TL", v, 30)
        self._TL = v

    def set_value(self, v):
        v = int(v)
        BbwUtils.test_geq("value", v, 0)
        self._value = v

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name(), self.capacity() if self.capacity() else None]
        else:
            return [
                self.count(),
                self.name(),
                self.capacity() if self.capacity() else None,
                self.TL() if self.TL() else None,
                self.value() if self.value() else None,
            ]

    def __str__(self, is_compact=True):
        return BbwUtils.print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["count", "name", "capacity"]
        else:
            return ["count", "name", "capacity", "TL", "value"]

    _luggage_capacities = {"luggage, high": 0.1, "luggage, middle": 0.001}
    _freight_ticket = [1000, 1600, 2600, 4400, 8500, 32000]

    _freight_lot_ton_multi_dict = {"freight, major": 10, "freight, minor": 5, "freight, incidental": 1, "mail": 5}

    @staticmethod
    def factory(name, count, capacity=0, TL=0, value=0, n_sectors=1, only_std=False):
        if count == 0:
            return None

        if "passenger, high" in name:
            name = "luggage, high"
            return BbwItem(name=name, capacity=BbwItem._luggage_capacities[name], count=count, TL=0, value=0)
        if "passenger, middle" in name:
            name = "luggage, middle"
            return BbwItem(name=name, capacity=BbwItem._luggage_capacities[name], count=count, TL=0, value=0)
        if "mail" in name:
            return BbwItem(name=name, capacity=5, count=count, TL=0, value=25000)

        res = BbwUtils.get_objs(raw_list=BbwItem._freight_lot_ton_multi_dict.keys(), name=name)
        if len(res) == 1:
            name, lot_ton_multi = res[0], BbwItem._freight_lot_ton_multi_dict[res[0]]
            capacity = d20.roll("1d6").total * lot_ton_multi
            item = BbwItem(
                name=name, capacity=capacity, count=count, TL=0, value=BbwItem._freight_ticket[n_sectors - 1] * capacity
            )
            item.set_name(f"{item.name()} (ns: {n_sectors}, lot: {capacity} tons)")
            return item

        return BbwItem(name=name, capacity=capacity, count=count, TL=TL, value=value) if not only_std else None
