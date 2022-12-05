from cogst5.models.errors import *

from cogst5.base import *
from cogst5.utils import *


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwCalendar:
    _days_in_week = 7
    _days_in_month = 28
    _days_in_year = 365
    _nmonths_per_year = int((_days_in_year - 1) / _days_in_month)

    def __init__(self, t: int = 0):
        self.set_t(t)

    def set_t(self, v):
        self._t = v

    def set_date(self, day: int, year: int):
        self.set_t(BbwCalendar.date2t(day, year))

    def add_t(self, v: int):
        old_month = self.month()
        old_year = self.year()

        self.set_t(self.t() + v)
        if v < 0:
            return 0

        if self.year() == old_year:
            return self.month() - old_month

        return (
            BbwCalendar._nmonths_per_year
            - old_month
            + (self.year() - old_year - 1) * BbwCalendar._nmonths_per_year
            + self.month()
        )

    def t(self):
        return self._t

    def year(self):
        return int(self.t() / self._days_in_year)

    def month(self):
        if self.day() == 1:
            return 1

        return int(max(self.day() - 2, 0) / self._days_in_month) + 1

    def monthday(self):
        if self.day() == 1:
            return "-"

        return int(max(self.day() - 2, 0) % self._days_in_month) + 1

    def week(self):
        if self.day() == 1:
            return "-"
        return int(max(self.day() - 2, 0) / self._days_in_week) + 1

    def weekday(self):
        day = self.day()
        if day == 1:
            return "holiday"

        return f"{max(self.day()-2, 0)%self._days_in_week+1}day"

    def day(self):
        return self.t() % self._days_in_year + 1

    def date(self):
        return f"{self.day()}-{self.month()}-{self.year()}"

    @staticmethod
    def date2t(day, year):
        if day is None or year is None:
            return None

        day = int(day)
        year = int(year)
        return year * BbwCalendar._days_in_year + day - 1

    def __str__(self, detail_lvl=0):
        s = f"date: {self.date()}\n"
        if detail_lvl == 0:
            return s
        s += f"month: {self.month()}, {self.monthday()}\n"
        s += f"week: {self.week()}, {self.weekday()}\n"
        return s


# print(a)
# print(a.monthday())
# exit()
