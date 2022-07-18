from cogst5.models.errors import *

from cogst5.utils import *
from cogst5.base import *
from cogst5.calendar import *

class BbwDebt(BbwObj):
    def __init__(self, due_t, period=None, t_end=None, *args, **kwargs):
        self._due_t = 0
        self.set_t_end(t_end)
        self.set_due_t(due_t)
        self.set_period(period)
        super().__init__(*args, **kwargs)

    def set_due_t(self, v):
        v = int(v)
        test_geq("due t", v, 0)
        if self.t_end():
            test_leq("due t", v, self.t_end())
        self._due_t = v

    def due_t(self):
        return self._due_t

    def set_period(self, v):
        if v:
            v = int(v)
            test_g("period", v, 0)
        self._period = v

    def period(self):
        return self._period

    def set_t_end(self, v):
        if v:
            v = int(v)
            test_g("t end", v, self.due_t())
        self._t_end = v

    def t_end(self):
        return self._t_end

    @staticmethod
    def _header(is_compact=True):
        return ["name", "amount", "due date", "period", "end date"]

    def _str_table(self, is_compact=True):
        return [self.name(), self.count(), BbwCalendar(self.due_t()).date(), self.period(), BbwCalendar(
            self.t_end()).date() if self.t_end() else ""]


class BbwCompany:
    _log_max_size = 100
    def __init__(self):
        self._money = 0
        self._log = []
        self._debts = BbwContainer(name="debts", capacity=None)

    def add_log_entry(self, v, des="", t=None):
        self.add_money(v)
        self._log.append([int(v), str(des), int(t) if t is not None else None])
        if len(self._log) > self._log_max_size:
            self._log.pop(0)

    def debts(self):
        return self._debts


    def pay_debt(self, name, curr_t):
        debt = self.debts()[name]

        self.add_log_entry(-debt.count(), f"debt: {debt.name()}", curr_t)

        if not debt.period():
            del self.debts()[name]
            return

        due_t = debt.due_t()
        new_due_t = due_t + debt.period()
        new_due_t += (BbwCalendar(due_t).year() != BbwCalendar(new_due_t).year())

        if (debt.t_end() and new_due_t >= debt.t_end()):
            del self.debts()[name]
            return

        debt.set_due_t(new_due_t)

    def pay_debts(self, curr_t):
        debts = list(self.debts().keys())
        for i in debts:
            self.pay_debt(i, curr_t)


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
            [str(i[0]) if i[0] > 0 else "", str(i[0]) if i[0] < 0 else "", str(i[1]), str(BbwCalendar(i[2]).date()) if
            i[2] else ""]
            for i in
            reversed(self._log[max(len(
                self._log)-log_lines, 0):])
        ]

    def __str__(self, log_lines=10):
        log_lines = int(log_lines)
        s = f"money: {self.money()}\n"
        if log_lines != 0:
            s+= tabulate(self._str_table(log_lines), headers=self._header())
            s += "\n"
        s+= self.debts().__str__(is_compact=False)
        s += "\n"
        return s

#
# a = BbwCompany()
#
# new_debt = BbwDebt(name="spaceship mortgage", count=1000, due_t=BbwCalendar.date2t(29+28+1, 0), period=28, t_end=None)
# a.debts().add_item(new_debt)
# a.debts().del_item(new_debt.name(), c=5)
#
# print(a)
#
#
# exit()







