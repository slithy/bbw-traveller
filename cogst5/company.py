from cogst5.models.errors import *

from cogst5.utils import *

class BbwCompany:
    _log_max_size = 100
    def __init__(self):
        self._money = 0
        self._log = []

    def add_log_entry(self, v, des="", t=None):
        self.add_money(v)
        self._log.append([int(v), str(des), int(t) if t is not None else None])
        if len(self._log) > self._log_max_size:
            self._log.pop(0)


    def money(self):
        return self._money

    def set_money(self, v):
        v = int(v)
        test_geq("money", v, 0)
        self._money = v

    def add_money(self, v):
        v = int(v)
        self.set_money(self.money()+v)


    @staticmethod
    def _header(is_compact=True):
        return ["in", "out", "description", "time"]

    def _str_table(self, log_lines = 10):
        return [
            [str(i[0]) if i[0] > 0 else "", str(i[0]) if i[0] < 0 else "", str(i[1]), str(i[2]) if i[2] else ""]
            for i in
            reversed(self._log[max(len(
                self._log)-log_lines, 0):])
        ]

    def __str__(self, log_lines=10):
        log_lines = int(log_lines)
        s = f"money: {self.money()}\n"
        if log_lines == 0:
            return s

        s+= tabulate(self._str_table(log_lines), headers=self._header())
        return s







