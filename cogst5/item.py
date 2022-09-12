from cogst5.base import *


class BbwItem(BbwObj):
    def __init__(self, value=0, TL=0, *args, **kwargs):
        self.set_value(value)
        self.set_TL(TL)

        super().__init__(*args, **kwargs)

    def TL(self):
        return self._TL

    def value(self):
        return self._value * self.count()

    def set_TL(self, v):
        v = int(v)
        test_geq("TL", v, 0)
        test_leq("TL", v, 30)
        self._TL = v

    def set_value(self, v):
        v = int(v)
        test_geq("value", v, 0)
        self._value = v

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name()]
        else:
            return [self.count(), self.name(), self.TL(), self.value(), self.capacity()]

    def __str__(self, is_compact=True):
        return print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["count", "name"]
        else:
            return ["count", "name", "TL", "value", "capacity"]
