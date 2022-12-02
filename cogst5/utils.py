from cogst5.models.errors import *
from tabulate import tabulate

import bisect
import lorem
import random
import d20
import re

import json
import jsonpickle


class BbwUtils:
    @staticmethod
    def set_if_not_present_decor(func):
        """We assume that the variable is _{func_name} and the setter is set_{func_name}"""

        def wrapper(self, *args, **kwargs):
            if not hasattr(self, f"_{func.__name__}"):
                getattr(self, f"set_{func.__name__}")()
            return func(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def type_sanitizer_decor(func):
        def wrapper(*args, **kwargs):
            def convert(t, val):
                if t is None or val is None or t is type(val):
                    return val

                if t is int:
                    return int(val)
                if t is float:
                    return float(val)
                if t is bool:
                    if val is str:
                        if val.lower() == "true":
                            return True
                        if val.lower() == "false":
                            return False
                    return bool(int(val))

                if type(val) is str:
                    return eval(val)

                return val

            args = [
                convert(func.__annotations__.get(var, None), arg) for arg, var in zip(args, func.__code__.co_varnames)
            ]
            kwargs = {k: convert(func.__annotations__.get(k, None), v) for k, v in kwargs.items()}
            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def for_all_methods(decorator):
        def decorate(cls):
            for attr in cls.__dict__:  # there's propably a better way to do this
                if callable(getattr(cls, attr)):
                    setattr(cls, attr, decorator(getattr(cls, attr)))
            return cls

        return decorate

    @staticmethod
    def test_g(k, v, tr):
        if v <= tr:
            raise InvalidArgument(f"`{k}`: `{v}` must be > `{tr}`!")

    @staticmethod
    def test_l(k, v, tr):
        if v >= tr:
            raise InvalidArgument(f"`{k}`: `{v}` must be < `{tr}`!")

    @staticmethod
    def test_leq(k, v, tr):
        if v >= tr:
            raise InvalidArgument(f"`{k}`: `{v}` must be <= `{tr}`!")

    @staticmethod
    def test_in_range(k, v, range):
        BbwUtils.test_geq(k, v, range[0])
        BbwUtils.test_leq(k, v, range[1])

    @staticmethod
    def test_in_list(k, v, l):
        if v not in l:
            raise InvalidArgument(f"{k}: {v} must be in `{', '.join(l)}`!")

    @staticmethod
    def test_hexstr(k, v, n):
        if type(v) is not str:
            raise InvalidArgument(f"{k}: {v} must be a str!")

        if len(v) not in n:
            raise InvalidArgument(f"{k}: {v} len must be {','.join(n)}!")

        for i in v:
            BbwUtils.test_geq(k, int(i, 36), 0)
            BbwUtils.test_leq(k, int(i, 36), 36)

    @staticmethod
    def test_geq(k, v, tr):
        if v < tr:
            raise InvalidArgument(f"{k}: {v} must be >= {tr}!")

    @staticmethod
    def test_leq(k, v, tr):
        if v > tr:
            raise InvalidArgument(f"{k}: {v} must be <= {tr}!")

    @staticmethod
    def int_or_float(v):
        try:
            int(v)
            t = int
        except ValueError:
            float(v)
            t = float
        return t

    @staticmethod
    def conv_days_2_time(d):
        days = int(d)
        d = d % 1
        hours = int(24 * d)
        d = (24 * d) % 1
        minutes = int(60 * d)
        d = (60 * d) % 1

        ans = []
        if days:
            ans.append(f"{days}d")
        if hours or len(ans):
            ans.append(f"{hours}h")
        ans.append(f"{minutes}m")

        return "-".join(ans)

    @staticmethod
    def print_code(i):
        if int(i, 36) >= 10:
            return f"{i} ({int(i, 36)})"
        else:
            return str(i)

    @staticmethod
    def smart_append(ans, res):
        for idx, i in enumerate(res):
            if i is None:
                continue
            if type(ans[idx]) is list:
                if type(i) is list:
                    ans[idx].extend(i)
                else:
                    ans[idx].append(i)
            else:
                ans[idx] = i + ans[idx]

    @staticmethod
    def has_all_tags(name, tags, base_case=True):
        if len(tags) == 0:
            return base_case
        if type(tags) is str:
            tags = {tags}
        if type(name) is tuple:
            name = name[0]
        elif type(name) is not str:
            name = name.name()
        return all(i in name for i in tags)

    @staticmethod
    def has_any_tags(name, tags, base_case=True):
        if len(tags) == 0:
            return base_case
        if type(tags) is str:
            tags = {tags}
        if type(name) is tuple:
            name = name[0]
        elif type(name) is not str:
            name = name.name()
        return any(i in name for i in tags)

    @staticmethod
    def get_objs(
        raw_list, name=None, with_all_tags=set(), with_any_tags=set(), without_tags=set(), type0=None, only_one=False
    ):
        if type(with_any_tags) is str:
            with_any_tags = set(with_any_tags)
        if type(with_all_tags) is str:
            with_any_tags = set(with_all_tags)
        if type(without_tags) is str:
            with_any_tags = set(without_tags)
        only_one = bool(int(only_one))
        if name is not None and type(name) is not str:
            name = name.name()

        def ck(with_all_tags, with_any_tags, without_tags, type0, val):
            return (
                BbwUtils.has_all_tags(val, with_all_tags)
                and BbwUtils.has_any_tags(val, with_any_tags)
                and not BbwUtils.has_any_tags(val, without_tags, False)
                and (type0 is None or issubclass(type0, type(val)))
            )

        def get_name(v):
            if type(v) is str:
                return v
            if type(v) is tuple:
                return v[0]
            return v.name()

        names = [get_name(i) for i in raw_list]
        ans = list(zip(names, raw_list))
        ans = [(name, val) for name, val in ans if ck(with_all_tags, with_any_tags, without_tags, type0, val)]

        def custom_sort(x):
            return int(not BbwUtils.has_all_tags(x[0], {"main"}))

        ans = sorted(ans, key=lambda q: custom_sort(q))

        if name is None:
            return [i for _, i in ans]
        if type(name) is not str:
            name = name.name()

        def _get_objs(k, zl):
            ans = [(n, v) for n, v in zl if n == k]
            if len(ans):
                return ans

            ans = [(n, v) for n, v in zl if n.lower() == k.lower()]
            if len(ans):
                return ans
            # If we want to check by prefix, reenable this
            # ans = self.check_getitem_list(key, [(k, v) for k, v in self.items() if k.startswith(key)])
            # if ans:
            #     return k, v
            # ans = self.check_getitem_list(key, [(k, v) for k, v in self.items() if k.lower().startswith(key.lower())])
            # if ans:
            #     return k, v

            ans = [(n, v) for n, v in zl if k in n]
            if len(ans):
                return ans

            ans = [(n, v) for n, v in zl if k.lower() in n.lower()]
            return ans

        ans = _get_objs(name, ans)
        if only_one:
            if len(ans) == 0:
                raise SelectionException(f"object `{name}` not found! Optons: `{', '.join(names)}`")
            if len(ans) > 1:
                raise SelectionException(f"too many matches for object `{name}`: `{', '.join([i for i, _ in ans])}`")

        ans = sorted(ans, key=lambda q: custom_sort(q))
        return [i for _, i in ans]

    @staticmethod
    def get_modifier(key, ll):
        return ll[1][bisect.bisect_left(ll[0], key)]

    @staticmethod
    def lore_ipsum_md(ns, m):
        def li16():
            return "\n".join([lorem.sentence() for _ in range(d20.roll("1d6").total)])

        sb = ["```\n" + li16() + "\n```" for _ in range(m)]

        s = [*[lorem.sentence() for _ in range(ns)], *sb]
        random.shuffle(s)
        return "\n".join(s)

    @staticmethod
    def split_md_compatible(msg):
        limit = 1900

        # q = [t, headers]
        # with open('/save/debug.json', 'w') as file:
        #     enc_data = jsonpickle.encode(q)
        #     json.dump(json.loads(enc_data), file, indent=2)

        if len(msg) <= limit:
            return [msg]

        s = [i.split("\n") if not idx % 2 else ["```" + i + "```"] for idx, i in enumerate(msg.split("```"))]
        s = [val for sublist in s for val in sublist if len(val)]

        ans = ["\n".join(i) for i in BbwUtils.greedy_splitter(s, lambda x: len(x) + 1, limit=limit)]

        # return ", ".join(str(len(i)) for i in s)
        return ans

    @staticmethod
    def greedy_splitter(l, fn_counter, limit=10):
        ans = []
        cc, j = 0, 0

        for i in range(len(l)):
            nc = fn_counter(l[i])
            if nc + cc > limit:
                ans.append(l[j:i])
                j = i
                cc = nc
            else:
                cc += nc
        ans.append(l[j:])

        return ans

    @staticmethod
    def print_table(t, headers=(), tablefmt="simple", detail_lvl=0):
        limit = 10

        if len(t) and not isinstance(t[0], list):
            t = [t]

        b = ""
        if detail_lvl:
            b = "```"

        def fn_counter(x):
            s = 1 + sum([str(j).count("\n") for j in x])
            return s

        st = BbwUtils.greedy_splitter(t, fn_counter, limit=limit)

        return "\n".join([b + tabulate(i, headers=headers, tablefmt=tablefmt) + b + "\n" for i in st])

    @staticmethod
    def local_2_global(x, y, xs, ys):
        return xs * 32 + x, -ys * 40 + y

    @staticmethod
    def hex_2_cube(x1, y1):
        x = x1
        y = y1 - (x1 + x1 % 2) / 2
        z = y1 + (x1 - (x1) % 2) / 2
        return x, y, z

    @staticmethod
    def distance(x0, y0, z0, x1, y1, z1):
        d = [abs(x0 - x1), abs(y0 - y1), abs(z0 - z1)]
        return int(max(d))

    @staticmethod
    def avg_min_max(s):
        l = re.findall(r"\d+", s)
        l = [int(i) for i in l]
        multi = 1 if len(l) == 2 else l[2]
        min0 = l[0] * multi
        max0 = l[0] * l[1] * multi
        avg0 = (min0 + max0) / 2
        return avg0, min0, max0

    @staticmethod
    def gen_dict(l):
        return {i.name(): i for i in l}


# q = []
# with open(f"../save/debug.json", "r") as f:
#     enc_data = json.dumps(json.load(f))
#     q = jsonpickle.decode(enc_data)
#
#
#     pt = BbwUtils.print_table(q[0], q[1])
#     print(len(BbwUtils.split_md_compatible(pt)[0]), len(BbwUtils.split_md_compatible(pt)[1]))
# exit()


# h = ['a', 'b', 'c']
# t = [[1, tabulate([["a", 1]]*20, tablefmt="plain"), 1]]*4
# print(BbwUtils.print_table(t, headers=h, limit=30))
#
# exit()

# l = [1, 3, 4, 6, 5, 3, 2, 1, 4, 11, 3, 2, 5, 4, 20, 1, 3]
#
# print([sum(i) for i in greedy_splitter(l, lambda x: x, limit=10)])
# exit()

# l2 = [5, 4, 2, 1]

# zl = zip(l, l2)
# def custom_sort(x):
#     return x[1]
# a = sorted(zl, key=lambda x: custom_sort(x))
# print(a)
#
# exit()
# msg = lore_ipsum_md(20, 5)
# #
# print(msg)
# print("----------")
# print([len(i) for i in split_md_compatible(msg, 200)])
# exit()
