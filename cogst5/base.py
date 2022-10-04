import copy

from cogst5.models.errors import *
from cogst5.utils import *


class BbwObj:
    def __init__(self, name="", capacity=None, count=1, size=None):
        if size is None:
            size = capacity

        self.set_name(name)
        self.set_count(count)
        self.set_capacity(capacity)
        self.set_size(size)

    def set_size(self, v):
        if v is None:
            v = self._capacity

        v = float(v)
        if v != self._capacity:
            BbwUtils.test_geq("size", v, 0.0)
        BbwUtils.test_leq("size", v, self._capacity)
        self._size = v

    def set_capacity(self, v):
        if v is None:
            v = 0.0
        v = float(v)

        self._capacity = v

    def set_name(self, v):
        v = str(v)
        self._name = v

    def set_count(self, v):
        if v == float("inf"):
            self._count = v
            return

        v = int(v)
        BbwUtils.test_g("count", v, 0)
        self._count = v

    def count(self):
        return self._count

    def name(self):
        return self._name

    def _per_obj(self, v, is_per_obj):
        return v if is_per_obj else v * self.count()

    def size(self, is_per_obj=False):
        try:
            size = self._size
        except AttributeError:
            self._size = self._capacity
            size = self._size

        return self._per_obj(size, is_per_obj)

    def capacity(self, is_per_obj=False):
        return self._per_obj(self._capacity, is_per_obj)

    def status(self):
        return f"({self.size()}/{self.capacity()})"

    def set_attr(self, v, k):
        if v == "name":
            raise NotAllowed(f"Setting the name in this way is not allowed! Use rename instead")
        if v == "capacity":
            raise NotAllowed(f"Resetting the capacity is not allowed! You need to delete the obj and create it again")

        f = getattr(self, f"set_{v}")
        f(k)

    def _str_table(self, detail_lvl=0):
        if detail_lvl == 0:
            return [self.count(), self.name()]
        else:
            return [self.count(), self.name(), self.capacity()]

    def __str__(self, detail_lvl=0):
        return BbwUtils.print_table(
            self._str_table(detail_lvl), headers=self._header(detail_lvl), detail_lvl=detail_lvl
        )

    @staticmethod
    def _header(detail_lvl=0):
        if detail_lvl == 0:
            return ["count", "name"]
        else:
            return ["count", "name", "capacity"]


class BbwRes:
    def __init__(self, count=0, value=0.0, objs=[]):
        self._count = count
        self._value = value
        if type(objs) is tuple:
            objs = [objs]
        self._objs = objs

    def __add__(self, o):
        if type(o) is not BbwRes:
            raise InvalidArgument(f"The obj `{o}` must be of type BbwRes!")
        count = self.count() + o.count()
        objs = [*self.objs(), *o.objs()]
        return BbwRes(count=count, objs=objs)

    def count(self):
        return self._count

    def value(self):
        """This will fail of the first object does not have the value() member"""

        if self.count() == 0:
            return 0

        return self.count() * self.objs()[0][0].value(is_per_obj=True)

    def objs(self):
        return self._objs

    def print_objs(self):
        return "\n".join([i.__str__(2) for i, _ in self.objs()])

    def print_containers(self):
        return ", ".join([i.__str__(0) for _, i in self.objs()])

    def __str__(self):
        return f"count:`{self.count()}`, len objs: `{len(self.objs())}`"


class BbwContainer(dict):
    def __init__(self, name="", capacity=float("inf"), size=0.0):
        self.set_name(name)
        self.set_capacity(capacity)
        self.set_size(size)

    def set_attr(self, v, k):
        if v == "name":
            raise NotAllowed(f"Setting the name in this way is not allowed! Use rename instead")
        if v == "capacity":
            raise NotAllowed(f"Resetting the capacity is not allowed! You need to delete the obj and create it again")

        f = getattr(self, f"set_{v}")
        f(k)

    def count(self):
        return 1

    def set_size(self, v):
        v = float(v)
        BbwUtils.test_geq("size", v, 0.0)
        BbwUtils.test_leq("size", v, self._capacity)

        self._size = v

    def set_name(self, v):
        v = str(v)
        self._name = v

    def set_capacity(self, v):
        if v is not None:
            v = float(v)

        BbwUtils.test_geq("capacity", v, 0.0)
        self._capacity = v

    def name(self):
        return self._name

    def size(self):
        return sum([i.capacity() for i in self.values()]) + self._size

    def capacity(self):
        return self._capacity

    def free_space(self):
        c = self.capacity()
        s = self.size()
        if c == float("inf") and s == float("inf"):
            return float("inf")
        return self.capacity() - self.size()

    def status(self):
        if self.capacity() == float("inf"):
            return ""
        return f"{self.size()}/{self.capacity()}"

    def _get_children_containers(self):
        return sorted(
            [i for i in self.values() if issubclass(BbwContainer, type(i))],
            key=lambda x: not BbwUtils.has_any_tags(x, {"main"}),
        )

    def _get_children_objs(self):
        return sorted(
            [i for i in self.values() if not issubclass(BbwContainer, type(i))],
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
                obj = copy.deepcopy(objs[0])
                del self[obj.name()]
                obj.set_name(new_name)
                self[obj.name()] = obj
                res += BbwRes(count=obj.count(), objs=[(obj, self)])
                if only_one:
                    return res

        for i in self._get_children_containers():
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

        for i in self._get_children_containers():
            if ans.count() == count:
                return ans
            ans += i.del_obj(name=name, count=count - ans.count(), cont=cont, *args, **kwargs)

        return ans

    def free_slots(self, caps):
        ans = float("inf")
        for i, cont, with_any_tags in caps:
            ans = min(ans, self._free_slots(cap=i, recursive=True, cont=cont, with_any_tags=with_any_tags))
        return ans

    def _free_slots(self, cap, recursive, cont=None, *args, **kwargs):
        cap = float(cap)
        BbwUtils.test_geq("cap", cap, 0)
        if cap == 0:
            return float("inf")

        ans = 0
        if len(BbwUtils.get_objs(raw_list=[self], name=cont, *args, **kwargs)):
            if self.free_space() == float("inf") or cap == 0:
                return float("inf")
            ans += int(self.free_space() / cap)

        if recursive:
            for i in self._get_children_containers():
                ans += i._free_slots(cap, recursive, cont=cont, *args, **kwargs)
        return ans

    # def add_obj(self, obj, cont=None, *args, **kwargs):
    #     if len(BbwUtils.get_objs([self], name=cont, *args, **kwargs)):
    #         if type(obj) is not BbwContainer:
    #             old_count = self[obj.name()].count() if obj.name() in self else 0.0
    #             ans = self._add_obj(obj)
    #             return ans
    #         else:
    #             return self._add_obj(obj)
    #
    #     for i in self._get_children_containers():
    #         ans = i.add_obj(obj, cont=cont, *args, **kwargs)
    #         if ans.count():
    #             return ans
    #     return BbwRes()

    def dist_obj(self, obj, unbreakable=False, cont=None, *args, **kwargs):
        if type(obj) is BbwContainer:
            if len(BbwUtils.get_objs([self], name=cont, *args, **kwargs)):
                return self._add_obj(obj)
            else:
                return BbwRes()

        unbreakable = bool(int(unbreakable))
        ans = BbwRes()
        n = obj.count()

        if unbreakable and n > self._free_slots(
            cap=obj.capacity(is_per_obj=True), recursive=True, cont=cont, *args, **kwargs
        ):
            return ans

        if len(BbwUtils.get_objs([self], name=cont, *args, **kwargs)):
            ans += self._fit_obj(obj)

        for i in self._get_children_containers():
            if ans.count() == n:
                break

            obj.set_count(n - ans.count())
            ans += i.dist_obj(obj, unbreakable=False, cont=cont, *args, **kwargs)

        return ans

    def _fit_obj(self, v):
        n = v.count()
        ns = self._free_slots(cap=v.capacity(is_per_obj=True), recursive=False)

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
            delta_capacity, delta_count = new_obj.capacity() - self[k].capacity(), v.count()
        else:
            delta_capacity, delta_count = v.capacity(), v.count()
            new_obj = copy.deepcopy(v)

        BbwUtils.test_geq("final container capacity", self.free_space() - delta_capacity, 0.0)

        self[k] = new_obj

        return BbwRes(count=delta_count, objs=[(self[k], self)])

    @staticmethod
    def _header(detail_lvl=0):
        return ["", "name", "status"]

    def _str_table(self, detail_lvl=0):
        return [None, self.name(), self.status()]

    def __str__(self, detail_lvl=0, lsort=lambda x: x.name()):
        s = ""
        s += BbwUtils.print_table(self._str_table(detail_lvl), tablefmt="plain", detail_lvl=0)

        if detail_lvl == 0 or not len(self.keys()):
            return s

        entry_detail_lvl = max(1, detail_lvl)
        maxIndex, _ = max(
            enumerate([len(i._header(detail_lvl=entry_detail_lvl)) for i in self.values()]), key=lambda v: v[1]
        )
        h = type(list(self.values())[maxIndex])._header(detail_lvl=entry_detail_lvl)

        t = sorted(self.values(), key=lsort)
        t = [i._str_table(detail_lvl=entry_detail_lvl) for i in t]

        s += BbwUtils.print_table(t, headers=h, detail_lvl=entry_detail_lvl)
        return s

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
            if len(ans.objs()) == 0:
                raise SelectionException(f"object `{name}` not found!")
            elif len(ans.objs()) > 1:
                raise SelectionException(
                    f"too many matches for `{name}`: `{', '.join([i.name() for o, _ in ans.objs()])}`"
                )

        if not recursive:
            only_one_ck(only_one, ans)
            return ans

        for i in self._get_children_containers():
            ans += i.get_objs(recursive=True, self_included=False, name=name, cont=cont, *args, **kwargs)

        only_one_ck(only_one, ans)
        return ans


#
#
#
# a = BbwObj(name="aaa", capacity=0)
# b = BbwObj(name="bbb", capacity=10)
# c = BbwObj(name="ccc", count=30)
# d = BbwObj(name="ddd", count=2, capacity=15)
# # # # # # #
# cont = BbwContainer(name="fleet")
# # # # # #
# # cont2 = BbwContainer(name="cargo, main", capacity=23)
# # cont3 = BbwContainer(name="cargo2", capacity=6)
# # # # # # #
# # # # # # # # # cont3 = BbwContainer(name="cargo3", capacity=20)
# # # # # # # # # cont4 = BbwContainer(name="cargo4", capacity=10)
# # # #
# # cont.add_obj(cont3)
# # cont.add_obj(cont2)
# #
# b = BbwObj(name="bbb", capacity=5, count=5)
# cont.add_obj(b)
# cont.add_obj(b)
# # c = cont.dist_obj(obj=b, unbreakable=True, cont="cargo")
# print([i.count() for i, _ in cont.get_objs().objs()])
# exit()
# # print([(i.name(), i.count()) for i, _ in cont.get_objs().objs()])
# # print("AAA")
# # print([(i.name(), i.count()) for i, _ in cont.get_objs(cont="stateroom").objs()])
# exit()


#
# from cogst5.person import *
# new_person = BbwPerson.factory(name="high", n_sectors=1, count=10)
# print("AAAA")
# print(cont.dist_obj(obj=new_person, with_any_tags={"stateroom"}).count())
# new_person = BbwPerson.factory(name="middle", n_sectors=1, count=10)
# print("BBBB")
# print(cont.dist_obj(obj=new_person, with_any_tags={"stateroom"}).count())
# print("CCCC")
# print([(i.name(), i.count()) for i, _ in cont.get_objs().objs()])
#
# exit()

# #
# #
# #
# # #
# # #
# cont.dist_obj(b, cont="cargo")
# cont.dist_obj(b, cont="cargo")
# #
# print(cont.__str__(2))
# # # cont.add_obj(b, cont="state")
# # # cont.add_obj(b, cont="state")
# # # cont.add_obj(b, cont="state")
# # # # cont.add_obj(cont3, cont="state")
# # # cont.add_obj(b, cont="m3")
# # # cont.add_obj(b, cont="m3")
# # # cont.add_obj(b, cont="m3")
# # # # cont.add_obj(b, cont="state")
# # cont.rename_obj(name="3", new_name="bau")
# # # cont.del_obj(name="bb", count=2, cont="3")
# # print([(i.name(), i.status()) for i in cont.BbwUtils.get_objs(recursive=True)])
# exit()
# # cont.add_obj(cont3, name="state")
#
#
# # print(cont.__str__(False))
# # print(cont.__str__(False))
#
# #

# # print(cont.__str__(False))
# print(cont.dist_obj(obj=new_person, unbreakable=False, cont="state"))
#
# print([i.__str__(0) for i in cont.BbwUtils.get_objs()])
#
# exit()


# def del_objs(self, name, count=None, cont=None):
#     if type(count) is str:
#         count = int(count)
#         BbwUtils.test_geq("count", count, 0)
#
#     if type(count) is str:
#         count = int(count)
#
#     if count == 0:
#         return [], 0, []
#
#     container = self.get_objs(name=cont, type0=BbwContainer, self_included=True, only_one=True)[0] if cont else self
#
#     if type(name) is not str:
#         name = name.name()
#
#     to_be_del = [i.name() for i in container.BbwUtils.get_objs(name=name, recursive=False)]
#     ndels_tot = 0
#
#     names = []
#     for i in to_be_del:
#         if count is None:
#             ndels_tot += container[i].count()
#             names.append(container[i].name())
#             del container[i]
#         else:
#             ndels = min(count, container[i].count())
#             ndels_tot += ndels
#             if ndels < container[i].count():
#                 container[i].set_count(container[i].count() - ndels)
#             else:
#                 del container[i]
#             names.append(container[i].name())
#
#             if count == ndels_tot:
#                 return [container], ndels_tot, names
#
#     if cont is not None:
#         return [container], ndels_tot, names
#
#     containers = self.get_objs(type0=BbwContainer, recursive=False)
#
#     l = [] if ndels_tot == 0 else [container]
#     for c in containers:
#         cl, ndels, nms = c.del_objs(name, None if count is None else count - ndels_tot)
#         l.extend(cl)
#         names.extend(nms)
#         ndels_tot += ndels
#         if count is not None and count == ndels_tot:
#             return l, ndels_tot, names
#
#     return l, ndels_tot, names


# def dist_obj(self, obj, with_any_tags=set(),with_all_tags=set(), unbreakable=False, container_name=None):
#
#     unbreakable = bool(int(unbreakable))
#     if type(with_any_tags) is str:
#         with_any_tags = set(eval(with_any_tags))
#
#     containers = self.get_objs(name=container_name, with_all_tags=with_all_tags, with_any_tags=with_any_tags, type0=BbwContainer)
#     # return containers, 0
#     if obj.capacity() == 0:
#         containers[0].add_obj(obj)
#         return containers[0], obj.count()
#
#     n = obj.count()
#     obj.set_count(1)
#
#     counts = [min(n, int(i.free_space()/obj.capacity())) for i in containers]
#     sum0 = sum(counts)
#
#     if sum0 < n and unbreakable or sum0 == 0:
#         return [], 0
#
#     rem = n
#     for idx in range(len(containers)):
#         if rem == 0:
#             return [c for i, c in enumerate(containers[:idx]) if counts[i]], n
#         cont, count = containers[idx], counts[idx]
#         if count:
#             c = min(count, rem)
#             new_obj = copy.deepcopy(obj)
#             new_obj.set_count(c)
#             cont.add_obj(new_obj)
#             rem -= c
#
#     return [c for i, c in enumerate(containers) if counts[i]], min(sum0, n)

# def dist_obj(self, obj, with_any_tags=set(), with_all_tags=set(), unbreakable=False, container_name=None):
#
#     unbreakable = bool(int(unbreakable))
#     if type(with_any_tags) is str:
#         with_any_tags = set(eval(with_any_tags))
#     if type(with_all_tags) is str:
#         with_any_tags = set(eval(with_all_tags))
#
#     containers = self.get_objs(name=container_name, with_all_tags=with_all_tags, with_any_tags=with_any_tags, type0=BbwContainer)
#     # return containers, 0
#     if obj.capacity() == 0:
#         containers[0].add_obj(obj)
#         return containers[0], obj.count()
#
#     n = obj.count()
#     obj.set_count(1)
#
#     counts = [min(n, int(i.free_space()/obj.capacity())) for i in containers]
#     sum0 = sum(counts)
#
#     if sum0 < n and unbreakable or sum0 == 0:
#         return [], 0
#
#     rem = n
#     for idx in range(len(containers)):
#         if rem == 0:
#             return [c for i, c in enumerate(containers[:idx]) if counts[i]], n
#         cont, count = containers[idx], counts[idx]
#         if count:
#             c = min(count, rem)
#             new_obj = copy.deepcopy(obj)
#             new_obj.set_count(c)
#             cont.add_obj(new_obj)
#             rem -= c
#
#     return [c for i, c in enumerate(containers) if counts[i]], min(sum0, n)


# def get_containing_containers(self, name, only_one=False):
#     ans = [v for v in self.get_all_containers().values() if v.get_obj(name, False) is not None]
#     if only_one and len(ans) > 1:
#         raise SelectionException(f"there are multiple matches for {name.name()}! Be more specific or add the container name")
#     return ans[0] if only_one else ans


#

# new_person = BbwPerson.factory(role="middle", n_sectors=1, count=10)
# with_any_tags = {"lowberth"} if new_person.has_any_tags({"low"}) else {"stateroom"}
#
# print("low" in new_person.name())
# print("low" in new_person.name())
# print(with_any_tags)
# exit()
#
# print(with_any_tags)
# aaa = cont.dist_obj(new_person, with_any_tags=with_any_tags)
# print(aaa[0][0].__str__())
# # print(cont.del_objs(new_person.name()))
# print(cont.__str__(False))
# #
# exit()
#
# # cont.add_obj(cont2)
# # cont.add_obj(cont4)
# # cont2.add_obj(cont3)
# #
# l, n = cont.dist_obj("high")
# print(len(l), n)
# print(list((i.name(), i.status()) for i in l))
#
# # #
# print(list((i.name(), i.status()) for i in cont.BbwUtils.get_objs(type0=BbwContainer)))
# print(cont2.__str__(False))
# # cont.del_objs("aa")
#
# print(list((i.name(), i.count()) for i in cont.BbwUtils.get_objs()))
# # #
# # # print([i.name() for i in cont.get_all_containers().values()])
# # # print([i.name() for i in cont.get_containers_from_obj_name("aa").values()])
# # # # # print(cont.__str__(False))
# exit()


# def BbwUtils.get_objs(self, name=None, with_all_tags=set(), with_any_tags=set(), without_tags=set(), type0=None, recursive=True,
#               self_included=False, only_one=False):
#     containers = self.get_all_containers(True) if recursive else {self.name(): self}
#
#     def ck(with_all_tags, with_any_tags, without_tags, type0, val):
#         return val.has_all_tags(with_all_tags) and val.has_any_tags(with_any_tags) and not val.has_any_tags(
#             without_tags, False) and (type0 is None or issubclass(type0, type(val)))
#
#     ans = [val for cont in containers.values() for val in cont.values() if
#            ck(with_all_tags, with_any_tags, without_tags, type0, val)]
#     if self_included and ck(with_all_tags, with_any_tags, without_tags, type0, self):
#         ans = [self, *ans]
#
#     def sort_self_main_other(x):
#         return 0 if x is self else int(not x.has_all_tags({"main"})) + 1
#
#     ans = sorted(ans, key=lambda x: sort_self_main_other(x))
#     if name is None:
#         return ans
#
#     if type(name) is not str:
#         name = name.name()
#
#     ans_after_name = BbwUtils.get_objs(name, ans)
#     if only_one:
#         if len(ans_after_name) == 0:
#             opt = ans if len(ans) else containers.values()
#             raise SelectionException(
#                 f"container {name} not found! Optons: {', '.join([i.name() for i in opt])}")
#         if len(ans_after_name) > 1:
#             raise SelectionException(
#                 f"too many matches for container {name}: {', '.join([i.name() for i in ans_after_name])}")
#
#     return sorted(ans_after_name, key=lambda x: sort_self_main_other(x))
#
#
# def get_all_containers(self, self_included=False):
#     if self_included:
#         return {self.name(): self,
#                 **{k: v for list_obj in
#                    [i.get_all_containers(True) for i in self.values() if issubclass(type(i), BbwContainer)]
#                    for (k, v) in list_obj.objs()}}
#     else:
#         return {k: v for list_obj in
#                 [i.get_all_containers(True) for i in self.values() if issubclass(type(i), BbwContainer)] for (k, v) in
#                 list_obj.objs()}
