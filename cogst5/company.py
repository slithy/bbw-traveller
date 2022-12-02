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

    def set_attr(self, v, *args, **kwargs):
        if v == "name":
            raise NotAllowed(f"Setting the name in this way is not allowed! Use rename instead")

        f = getattr(self, f"set_{v}")
        f(*args, **kwargs)

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
    def _header(detail_lvl=0):
        return ["name", "amount", "due date", "period", "end date"]

    def _str_table(self, detail_lvl=0):
        return [
            self.name(),
            self.capacity(),
            BbwCalendar(self.due_t()).date(),
            self.period(),
            BbwCalendar(self.end_t()).date() if self.end_t() else "",
        ]


class BbwCompany:
    def __init__(self):
        self._money = 0
        self._debts = BbwContainer(name="debts")

    def debts(self):
        return self._debts

    def _pay_debt(self, log, curr_t, name):
        debt = self.debts().get_objs(name=name, only_one=True).objs()[0][0]

        log.add_entry(f"debt: {debt.name()}", curr_t, debt.capacity())

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

    def pay_debts(self, log, curr_t, name=None):
        if name is None:
            debts = list(self.debts().keys())
        else:
            debts = [name]
        for i in debts:
            self._pay_debt(log, curr_t, i)

    def pay_salaries(self, crew, log, time):
        tot = 0

        for i in crew:
            tot += i.salary_ticket()

        no_reinvest_crew = [i for i in crew if not i.reinvest()]
        tot_not_reinvested = 0
        for i in no_reinvest_crew:
            tot_not_reinvested += i.salary_ticket()

        crew_line = "\n".join([i.name() for i in crew])
        log.add_entry(f"salaries for:\n{crew_line}", time, tot)
        if tot_not_reinvested:
            crew_line = "\n".join([i.name() for i in no_reinvest_crew])
            log.add_entry(f"safeguard salaries for:\n{crew_line}", time, -tot_not_reinvested)

    def money(self):
        return self._money

    def set_money(self, v):
        v = int(v)
        BbwUtils.test_geq("money", v, 0)
        self._money = v

    def add_money(self, value):
        value = int(value)
        self.set_money(self.money() + value)

    def __str__(self, detail_lvl=0):
        s = f"money: `{self.money():,}`\n"

        if detail_lvl == 0:
            return s

        s += self.debts().__str__(detail_lvl=1)
        s += "\n"
        return s
