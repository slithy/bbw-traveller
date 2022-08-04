from cogst5.utils import *
from cogst5.models.errors import *
import copy


class BbwObj:
    def __init__(self, name="", size=0.0, capacity=0.0, count=1):
        self.set_name(name)
        self.set_count(count)
        self.set_capacity(capacity)
        self.set_size(size)

    def set_size(self, v):
        v = float(v)

        test_geq("size", v, 0.0)
        test_leq("size", v, self._capacity)
        self._size = v

    def set_capacity(self, v):
        v = float(v)

        test_geq("capacity", v, 0.0)
        self._capacity = v

    def set_name(self, v):
        v = str(v)
        self._name = v

    def set_count(self, v):
        v = int(v)
        test_g("count", v, 0)

        self._count = v

    def count(self):
        return self._count

    def name(self):
        return self._name

    def size(self):
        return self._size * self._count

    def capacity(self):
        if self._capacity is None:
            return None
        return self._capacity * self._count

    def status(self):
        return f"{self._size}/{self._capacity}"

    def set_attr(self, v, k):
        if v == "name":
            raise NotAllowed(f"Setting the name in this way is not allowed! Use rename instead")
        if v == "capacity":
            raise NotAllowed(f"Resetting the capacity is not allowed! You need to delete the item and create it again")

        f = getattr(self, f"set_{v}")
        f(k)

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name()]
        else:
            return [self.count(), self.status(), self.name()]

    def __str__(self, is_compact=True):
        return print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["count", "name"]
        else:
            return ["count", "status", "name"]


class BbwContainer(dict):
    def __init__(self, name="", capacity=None, d={}):
        self.set_name(name)
        self.set_capacity(capacity)
        for k, v in d.items():
            self.set_item(k, v)

    def set_name(self, v):
        v = str(v)
        self._name = v

    def set_capacity(self, v):
        if v is not None:
            v = float(v)

            test_geq("capacity", v, 0.0)
        self._capacity = v

    def name(self):
        return self._name

    def size(self):
        return sum([i.capacity() for i in self.values()])

    def capacity(self):
        return self._capacity

    def free_space(self):
        if self.capacity() is None:
            return ""
        return self.capacity() - self.size()

    def status(self):
        if self.capacity() is None:
            return ""
        return f"{self.size()}/{self.capacity()}"

    def rename_item(self, item, new_name):
        if new_name in self:
            NotAllowed(
                f"You cannot rename {item.name()} into {new_name} because another item with that name already "
                f"exists! Delete it first"
            )

        self.del_item(item.name(), item.count())
        item.set_name(new_name)
        self.add_item(item)

    def add_item(self, v):
        if v.name() not in self:
            self.set_item(v)
            return

        old_item = copy.deepcopy(self[v.name()])
        old_item.set_count(old_item.count() + v.count())

        self.set_item(old_item)

    def set_item(self, v):
        k = v.name()
        old_capacity = self[k].capacity() if k in self else 0.0

        if self.capacity() is not None:
            if v.capacity() is None:
                raise NotAllowed("Container without capacity inside a container with capacity is not allowed!")
            test_geq("final container capacity", self.free_space() - v.capacity() + old_capacity, 0.0)

        self[k] = v

    def del_item(self, k, c=1):
        k = str(k)
        c = int(c)
        test_g("Count", c, 0)

        if k not in self:
            raise InvalidArgument(f"Item {k} not found. Possible options: {', '.join(self.keys())}")

        if isinstance(self[k], BbwContainer):
            del self[k]
            return

        new_count = self[k].count() - c
        test_geq(f"{k} count", new_count, 0)
        if new_count == 0:
            del self[k]
            return

        self[k].set_count(new_count)

    def get_item(self, key):
        ans = check_get_item_list(key, [(k, v) for k, v in self.items() if key == k])
        if ans:
            return ans
        ans = check_get_item_list(key, [(k, v) for k, v in self.items() if key.lower() == k.lower()])
        if ans:
            return ans
        # If we want to check by prefix, reenable this
        # ans = self.check_getitem_list(key, [(k, v) for k, v in self.items() if k.startswith(key)])
        # if ans:
        #     return ans
        # ans = self.check_getitem_list(key, [(k, v) for k, v in self.items() if k.lower().startswith(key.lower())])
        # if ans:
        #     return ans
        ans = check_get_item_list(key, [(k, v) for k, v in self.items() if key in k])
        if ans:
            return ans
        ans = check_get_item_list(key, [(k, v) for k, v in self.items() if key.lower() in k.lower()])
        if ans:
            return ans

        raise SelectionException(f"Unknown key: {key}. Possible options: {', '.join(self.keys())}")

    @staticmethod
    def _header(is_compact=True):
        return ["name", "status"]

    def _str_table(self, is_compact=True):
        return [self.name(), self.status()]

    def __str__(self, is_compact=True):

        s = ""
        s += print_table(self._str_table(is_compact), headers=self._header(is_compact))

        if not is_compact and len(self.keys()):
            entries_is_compact = False
            s += "\n"
            h = type(list(self.values())[0])._header(is_compact=entries_is_compact)

            t = [i._str_table(is_compact=entries_is_compact) for i in self.values()]
            s += print_table(t, headers=h)

        return s
