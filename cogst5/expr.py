import d20


class BbwExpr:
    def __init__(self, l=[], q=None):
        if q is not None:
            l = [(l, q)]
        self._l = []
        if type(l) is list:
            self._l = l
        else:
            self._l = (BbwExpr() + l)._l

    def __add__(self, o):
        if type(o) is BbwExpr:
            return BbwExpr([*self._l, *o._l])
        if type(o) is tuple:
            return BbwExpr([*self._l, o])
        if type(o) is d20.dice.RollResult:
            return BbwExpr([*self._l, (o, o.total)])
        raise ValueError(f"{o} must be of type tuple, BbwExpr or d20.dice.RollResult")

    def __sub__(self, o):
        return self + (o * -1)

    def __gt__(self, o):
        if type(o) is BbwExpr:
            if len(self._l) == 0:
                return False
            if len(o._l) == 0:
                return True
            return int(self) > int(o)

    def __lt__(self, o):
        if type(o) is BbwExpr:
            if len(self._l) == 0:
                return True
            if len(o._l) == 0:
                return False
            return int(self) < int(o)

    def __mul__(self, o):
        if type(o) is float or type(o) is int:
            return BbwExpr([(d, i * o) for d, i in self._l])

    def __rmul__(self, o):
        return self.__mul__(o)

    def __int__(self):
        return sum(i for _, i in self._l)

    def __str__(self, is_compact=False):
        if len(self._l) == 0:
            return ""

        def affix(idx, v, i):
            s = " " if idx else ""
            if idx and v >= 0:
                s += "+ "
            if type(i) is d20.dice.RollResult:
                s += i.__str__()
            else:
                s += f"{v} [{i}]"
            return s if not is_compact else s.replace(" ", "").replace("`", "")

        s = "".join([f"{affix(idx, v, i)}" for idx, (i, v) in enumerate(self._l)])
        if len(self._l) == 1:
            return s if not is_compact else s.replace(" ", "").replace("`", "")

        s += f" = {int(self)}"
        return s if not is_compact else s.replace(" ", "").replace("`", "")
