from cogst5.models.errors import *

from cogst5.base import *
from cogst5.utils import *

class BbwCalendar:
    _days_in_week = 7
    _days_in_month = 28
    _days_in_year = 365

    def __init__(self, t=0):
        self.set_t(t)

    def set_t(self, v):
        v = int(v)
        test_geq("integral time", v, 0)
        self._t = v

    def set_date(self, day, year):
        day = int(day)
        year = int(year)
        self.set_t(BbwCalendar.date2t(day, year))

    def add_t(self, v):
        v = int(v)
        test_g("advance", v, 0)
        self.set_t(self.t()+v)

    def t(self):
        return self._t

    def year(self):
        return int(self.t()/self._days_in_year)

    def month(self):
        if self.day() == 1:
            return "-"

        return int(max(self.day()-2, 0)/self._days_in_month)+1

    def week(self):
        if self.day() == 1:
            return "-"
        return int(max(self.day()-2, 0)/self._days_in_week)+1

    def weekday(self):
        day = self.day()
        if day == 1:
            return "holiday"

        return f"{max(self.day()-2, 0)%self._days_in_week+1}day"


    def day(self):
        return self.t()%self._days_in_year+1

    def date(self):
        return f"{self.day()}-{self.month()}-{self.year()}"

    @staticmethod
    def date2t(day, year):
        if not day or not year:
            return None

        day = int(day)
        year = int(year)
        return year*BbwCalendar._days_in_year+day-1


    def __str__(self, is_compact=True):
        s = f"date: {self.date()}\n"
        if is_compact:
            return s
        s += f"week: {self.week()}, {self.weekday()}\n"
        return s


# a = BbwCalendar(1)
# print(a)
# exit()


