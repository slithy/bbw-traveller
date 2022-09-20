from cogst5.models.errors import *

from cogst5.utils import *
from cogst5.base import *
from cogst5.calendar import *


class BbwDebt(BbwObj):
    def __init__(self, due_t, period=None, end_t=None, *args, **kwargs):
        self._due_t = 0
        self.set_end_t(end_t)
        self.set_due_t(due_t)
        self.set_period(period)
        super().__init__(*args, **kwargs)

    def set_attr(self, v, k):
        if v == "name":
            raise NotAllowed(f"Setting the name in this way is not allowed! Use rename instead")

        f = getattr(self, f"set_{v}")
        f(k)

    def set_due_t(self, v):
        v = int(v)
        BbwUtils.test_geq("due t", v, 0)
        if self.end_t():
            BbwUtils.test_leq("due t", v, self.end_t())
        self._due_t = v

    def due_t(self):
        return self._due_t

    def set_period(self, v):
        if v:
            v = int(v)
            BbwUtils.test_g("period", v, 0)
        self._period = v

    def period(self):
        return self._period

    def set_end_t(self, v):
        if v:
            v = int(v)
            BbwUtils.test_g("t end", v, self.due_t())
        self._end_t = v

    def end_t(self):
        return self._end_t

    @staticmethod
    def _header(is_compact=True):
        return ["name", "amount", "due date", "period", "end date"]

    def _str_table(self, is_compact=True):
        return [
            self.name(),
            self.capacity(),
            BbwCalendar(self.due_t()).date(),
            self.period(),
            BbwCalendar(self.end_t()).date() if self.end_t() else "",
        ]


class BbwCompany:
    _log_max_size = 100

    def __init__(self):
        self._money = 0
        self._log = []
        self._debts = BbwContainer(name="debts")

    def add_log_entry(self, v, des="", t=None):
        self.add_money(v)
        self._log.append([int(v), str(des), int(t) if t is not None else None])
        if len(self._log) > self._log_max_size:
            self._log.pop(0)

    def debts(self):
        return self._debts

    def _pay_debt(self, curr_t, name):
        debt = self.debts().get_objs(name=name, only_one=True).objs()[0][0]

        self.add_log_entry(debt.capacity(), f"debt: {debt.name()}", curr_t)

        if not debt.period():
            self.debts().del_obj(name=debt.name())
            return

        due_t = debt.due_t()
        new_due_t = due_t + debt.period()
        new_due_t += BbwCalendar(new_due_t).year() - (BbwCalendar(due_t).year())

        if debt.end_t() and new_due_t >= debt.end_t():
            self.debts().del_obj(name=debt.name())
            return

        debt.set_due_t(new_due_t)

    def pay_debts(self, curr_t, name=None):
        if name is None:
            debts = list(self.debts().keys())
        else:
            debts = [name]
        for i in debts:
            self._pay_debt(curr_t, i)

    def pay_salaries(self, crew, time):
        tot = 0

        for i in crew:
            tot += i.salary_ticket()

        no_reinvest_crew = [i for i in crew if not i.reinvest()]
        tot_not_reinvested = 0
        for i in no_reinvest_crew:
            tot_not_reinvested += i.salary_ticket()

        self.add_log_entry(tot, f"salaries for: {', '.join([i.name() for i in crew])}", time)
        if tot_not_reinvested:
            self.add_log_entry(
                -tot_not_reinvested, f"safeguard salaries for: {', '.join([i.name() for i in no_reinvest_crew])}", time
            )

    def money(self):
        return self._money

    def set_money(self, v):
        v = int(v)
        BbwUtils.test_geq("money", v, 0)
        self._money = v

    def add_money(self, v):
        v = int(v)
        self.set_money(self.money() + v)

    @staticmethod
    def _header(is_compact=True):
        return ["in", "out", "description", "time"]

    def _str_table(self, log_lines=10):
        return [
            [
                str(i[0]) if i[0] > 0 else "",
                str(i[0]) if i[0] < 0 else "",
                str(i[1]),
                str(BbwCalendar(i[2]).date()) if i[2] is not None else "",
            ]
            for i in reversed(self._log[max(len(self._log) - log_lines, 0) :])
        ]

    def __str__(self, log_lines=10):
        log_lines = int(log_lines)
        s = f"money: `{self.money()}`\n"
        if log_lines != 0:
            s += BbwUtils.print_table(self._str_table(log_lines), headers=self._header())
            s += "\n"
        s += self.debts().__str__(is_compact=False)
        s += "\n"
        return s
