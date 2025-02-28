from cogst5.base import *
from cogst5.calendar import *
from cogst5.utils import *


class BbwLog(list):
    _max_size = 100

    def __init__(self, name=""):
        self.set_name(name)

    def set_name(self, v):
        self._name = v

    def name(self):
        return self._name

    def add_entry(self, description="", t=None, value=0):
        if t is not None:
            t = int(t)

        if value is not None:
            value = int(value)

        self.append([value, description, t])
        if len(self) > BbwLog._max_size:
            self.pop(0)

    def undo(self):
        self.pop()

    @staticmethod
    def _header(detail_lvl=0):
        return ["in", "out", "description", "time"]

    def _str_table(self, log_lines=10, name="", transactions=0):
        log_lines = int(log_lines)
        transactions = int(transactions)

        def filter(val, des):
            if name not in des:
                return False
            if transactions == 0:
                return True
            if transactions == 1:
                return bool(val) or "buy" in des or "sell" in des
            if transactions == 2:
                return not (bool(val) or "buy" in des or "sell" in des)
            return True

        t = [
            [
                str(i[0]) if i[0] > 0 else "",
                str(i[0]) if i[0] < 0 else "",
                str(i[1]),
                str(BbwCalendar(i[2]).date()) if i[2] is not None else "",
            ]
            for i in self
            if filter(i[0], i[1])
        ]

        if len(t) < log_lines:
            return t

        return t[-log_lines:]

    def __str__(self, detail_lvl=1, log_lines=10, name="", transactions=0):
        return BbwUtils.print_table(
            self._str_table(log_lines=log_lines, name=name, transactions=transactions),
            self._header(),
            detail_lvl=detail_lvl,
        )


# a = BbwLog("log")
# a.add_entry("aieie")
# a.add_entry("aieie")
# a.add_entry("aieie1", 3)
# a.add_entry("aieie2", 3, 8)
# a.undo()
# print(a)
#
# exit()
