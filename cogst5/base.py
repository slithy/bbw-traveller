import copy

from cogst5.models.errors import *
from cogst5.utils import *


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwObj(dict):
    def __init__(self, name="", capacity=None, count=1, size=None, info=""):
        self._capacity = 0
        self._size = 0

        self.set_name(name)
        self.set_count(count)
        self.set_capacity(capacity)
        self.set_size(size)
        self.set_info(info)

    def set_info(self, v: str = ""):
        self._info = v

    @BbwUtils.set_if_not_present_decor
    def info(self):
        return self._info

    def _per_obj(self, v, is_per_obj):
        return v if is_per_obj else v * self.count()

    def set_size(self, v: float = None):
        if v is None:
            v = self._capacity

        if v == 0:
            self._size = v
            return

        BbwUtils.test_geq("size", self.free_space(size=v), 0.0)
        BbwUtils.test_geq("size", v, 0.0)

        self._size = v

    @BbwUtils.set_if_not_present_decor
    def size(self, is_per_obj: bool = False):
        return self._per_obj(self._size, is_per_obj)

    def set_capacity(self, v: float = None):
        if v is None:
            v = 0.0

        if v == float("inf"):
            self._capacity = v
            return

        BbwUtils.test_geq("size", self.free_space(capacity=v), 0.0)
        BbwUtils.test_geq("capacity", v, 0.0)
        self._capacity = v

    @BbwUtils.set_if_not_present_decor
    def capacity(self, is_per_obj=False):
        return self._per_obj(self._capacity, is_per_obj)

    def set_name(self, v: str = "new_name"):
        self._name = v

    @BbwUtils.set_if_not_present_decor
    def name(self):
        return self._name

    def set_count(self, v: float = 1):
        BbwUtils.test_g("count", v, 0)
        self._count = v

    @BbwUtils.set_if_not_present_decor
    def count(self):
        return int(self._count)

    def set_child_count(self, name: str, v: float):
        if int(v) <= 0:
            del self[name]
            return True

        new_cap = self[name].capacity(is_per_obj=True) * v
        free_space = self.free_space() + self[name].capacity()
        BbwUtils.test_leq("count", new_cap, free_space)
        self[name].set_count(v)

    def set_child_capacity(self, name: str, v: float):
        new_cap = self[name].count() * v
        free_space = self.free_space() + self[name].capacity()
        BbwUtils.test_leq("capacity", new_cap, free_space)
        self[name].set_capacity(v)

    def get_obj_capacity(self, i, is_per_obj=False):
        """Useful to add multipliers in derived classes"""
        return i.capacity(is_per_obj=is_per_obj)

    def free_space(self, capacity: float = None, size: float = None, is_per_obj=False):
        if capacity is None:
            capacity = self.capacity(is_per_obj=True)
        if size is None:
            size = self.size(is_per_obj=True)

        if capacity == float("inf"):
            return float("inf")

        return self._per_obj(capacity - size - self.used_space(), is_per_obj)

    def status(self):
        return f"({BbwUtils.pf(self.size()+self.used_space())}/{BbwUtils.pf(self.capacity())})"

    def used_space(self):
        return sum([self.get_obj_capacity(i) for i in self.values()])

    def get_children(self):
        return sorted(
            self.values(),
            key=lambda x: not BbwUtils.has_any_tags(x, {"main"}),
        )

    def rename_obj(self, name, new_name, cont=None, only_one=True, *args, **kwargs):
        if type(name) is not str:
            name = name.name()
        if type(new_name) is not str:
            new_name = new_name.name()

        res = BbwRes()

        if len(BbwUtils.get_objs([self], name=cont)):
            objs = BbwUtils.get_objs(self.values(), name=name, *args, **kwargs)
            if len(objs) > 1:
                raise SelectionException(
                    f"too many matches for container `{name}`: `{', '.join([i.name() for i in objs])}`"
                )
            if len(objs):
                obj = objs[0]
                old_name = obj.name()
                obj.set_name(new_name)
                self[obj.name()] = self.pop(old_name)

                res += BbwRes(count=obj.count(), objs=[(obj, self)])
                if only_one:
                    return res

        for i in self.get_children():
            if res.count() and only_one:
                return res
            res += i.rename_obj(name=name, new_name=new_name, cont=cont, *args, **kwargs)

        return res

    def del_obj(self, name=None, count=float("inf"), cont=None, *args, **kwargs):
        count = float(count)
        BbwUtils.test_geq("count", count, 0.0)

        ans = BbwRes()
        if len(BbwUtils.get_objs([self], name=cont)):
            objs = [i.name() for i in BbwUtils.get_objs(raw_list=self.values(), name=name, *args, **kwargs)]

            for i in objs:
                if ans.count() == count:
                    return ans

                nr = min(self[i].count(), count)
                if nr == self[i].count():
                    ans += BbwRes(count=nr, objs=[(copy.deepcopy(self[i]), self)])
                    del self[i]
                else:
                    self[i].set_count(self[i].count() - nr)
                    elimnated = copy.deepcopy(self[i])
                    elimnated.set_count(nr)
                    ans += BbwRes(count=nr, objs=[(elimnated, self)])

        for i in self.get_children():
            if ans.count() == count:
                return ans
            ans += i.del_obj(name=name, count=count - ans.count(), cont=cont, *args, **kwargs)

        return ans

    def free_slots(self, caps):
        ans = float("inf")
        for i, cont, with_any_tags in caps:
            ans = min(ans, self._free_slots(obj=i, recursive=True, cont=cont, with_any_tags=with_any_tags))
        return ans

    def _free_slots(self, obj, recursive: bool, cont: str = None, *args, **kwargs):
        cap = self.get_obj_capacity(obj, is_per_obj=True)
        BbwUtils.test_geq("cap", cap, 0)
        if cap == 0:
            return float("inf")

        ans = 0
        if len(BbwUtils.get_objs(raw_list=[self], name=cont, *args, **kwargs)):
            if self.free_space() == float("inf") or cap == 0:
                return float("inf")

            ans += int(self.free_space() / cap)

        if recursive:
            for i in self.get_children():
                ans += i._free_slots(obj, recursive, cont=cont, *args, **kwargs)
        return ans

    def dist_obj(self, obj, unbreakable: bool = False, cont: str = None, *args, **kwargs):
        ans = BbwRes()
        n = obj.count()

        if unbreakable and n > self._free_slots(obj=obj, recursive=True, cont=cont, *args, **kwargs):
            return ans

        if len(BbwUtils.get_objs([self], name=cont, *args, **kwargs)):
            ans += self._fit_obj(obj)

        for i in self.get_children():
            if ans.count() == n:
                break

            obj.set_count(n - ans.count())
            ans += i.dist_obj(obj, unbreakable=False, cont=cont, *args, **kwargs)

        obj.set_count(n)
        return ans

    def get_objs(self, name=None, recursive=True, self_included=False, only_one=False, cont=None, *args, **kwargs):
        ans = BbwRes()

        if len(BbwUtils.get_objs([self], name=cont)):
            l = sorted([i for i in self.values()], key=lambda x: not BbwUtils.has_any_tags(x, {"main"}))
            if self_included:
                l = [self, *l]

            objs = BbwUtils.get_objs(raw_list=l, name=name, *args, **kwargs)
            ans += BbwRes(count=sum([i.count() for i in objs]), objs=zip(objs, [self] * len(objs)))

        def only_one_ck(only_one, ans):
            if not only_one:
                return
            if len(ans) == 0:
                raise SelectionException(f"object `{name}` not found!")
            elif len(ans) > 1:
                raise SelectionException(f"too many matches for `{name}`: `{', '.join([o.name() for o in ans])}`")

        if not recursive:
            only_one_ck(only_one, ans)
            return ans

        for i in self.get_children():
            ans += i.get_objs(recursive=True, self_included=False, name=name, cont=cont, *args, **kwargs)

        only_one_ck(only_one, ans)
        return ans

    def _fit_obj(self, v):
        n = v.count()
        ns = self._free_slots(obj=v, recursive=False)

        if ns:
            nfitting = min(ns, n)
            v.set_count(nfitting)
            ans = self._add_obj(v)
            v.set_count(n)
            return ans
        v.set_count(n)
        return BbwRes()

    def _add_obj(self, v):
        k = v.name()

        if k in self:
            new_obj = copy.deepcopy(self[k])
            new_obj.set_count(new_obj.count() + v.count())
            delta_capacity, delta_count = self.get_obj_capacity(new_obj) - self.get_obj_capacity(self[k]), v.count()
        else:
            delta_capacity, delta_count = self.get_obj_capacity(v), v.count()
            new_obj = copy.deepcopy(v)

        BbwUtils.test_geq("final container capacity", self.free_space() - delta_capacity, 0.0)

        self[k] = new_obj

        return BbwRes(count=delta_count, objs=[(self[k], self)])

    def set_attr(self, v: str, *args, **kwargs):
        if v == "name":
            raise NotAllowed(f"Setting the name in this way is not allowed! Use rename instead")
        f = getattr(self, f"set_{v}")
        f(*args, **kwargs)

    def n_objs(self):
        return f"({len(self)}/{BbwUtils.pf(sum([i.count() for i in self.values()]))})"

    @staticmethod
    def _header(detail_lvl: int = 0):
        return ["count", "name", "status", "n objs", "info"]

    def _str_table(self, detail_lvl: int = 0):
        return [self.count(), self.name(), self.status(), self.n_objs(), self.info()]

    def name_GUI(self):
        return f"{self.count()}, {self.name()}, {self.status()}"

    def __str__(self, detail_lvl: int = 0, lsort=lambda x: x.name(), lname=None):
        s = ""
        if detail_lvl > 0:
            s += BbwUtils.print_table(
                self._str_table(detail_lvl),
                headers=BbwObj._header(detail_lvl=detail_lvl),
                tablefmt="plain",
                detail_lvl=detail_lvl,
            )

        if detail_lvl == 0 or not len(self.keys()):
            return s

        entry_detail_lvl = 1
        maxIndex, _ = max(
            enumerate([len(type(i)._header(detail_lvl=entry_detail_lvl)) for i in self.values()]), key=lambda v: v[1]
        )
        h = type(list(self.values())[maxIndex])._header(detail_lvl=entry_detail_lvl)

        t = sorted(BbwUtils.get_objs(raw_list=self.values(), name=lname), key=lsort)

        t = [i._str_table(detail_lvl=entry_detail_lvl) for i in t]

        s += BbwUtils.print_table(t, headers=h, detail_lvl=detail_lvl)
        return s


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwRes:
    """Count is a separate member because we can add to an item that is already there. Getting the count from that would give the total count of the items, not the delta
    """

    def __init__(self, count=0, objs=[]):
        self.set_count(count)
        if type(objs) is tuple:
            objs = [objs]
        self._objs = objs

    def __add__(self, o):
        if type(o) is not BbwRes:
            raise InvalidArgument(f"The obj `{o}` must be of type BbwRes!")
        count = self.count() + o.count()
        objs = [*self.objs(), *o.objs()]
        return BbwRes(count=count, objs=objs)

    def set_count(self, v: int = 0):
        BbwUtils.test_geq("count", v, 0)
        self._count = v

    @BbwUtils.set_if_not_present_decor
    def count(self):
        return self._count

    def capacity(self):
        if self.count() == 0:
            return 0

        return self.count() * self[0].capacity(is_per_obj=True)

    def value(self):
        if self.count() == 0:
            return 0

        return self.count() * self[0].value(is_per_obj=True)

    def total_cost(self):
        if self.count() == 0:
            return 0

        return self.value() * self[0].price_multi()

    def __getitem__(self, item):
        return self.objs()[item][0]

    def __len__(self):
        return len(self.objs())

    def objs(self):
        return self._objs

    def print_objs(self):
        return "\n".join([i.__str__(2) for i in self])

    def print_containers(self):
        return ", ".join([i.__str__(0) for _, i in self.objs()])

    def __str__(self, detail_lvl: int = 0):
        s = ""
        if detail_lvl == 1 and len(self) > 1:
            o = BbwObj("Results", capacity="inf", size=0)
            for i in self:
                o.dist_obj(i)

            s += o.__str__(detail_lvl=1)

            return s

        s += f"Results count: `{self.count()}`, len: `{len(self)}`\n"
        if detail_lvl == 0:
            return s

        for i in self:
            s += i.__str__(detail_lvl=detail_lvl)
            s += "\n"

        return s
