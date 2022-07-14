from utils import safe_conv
from models.errors import *

from safe_objects import SafeObj, SafeDict


class Item(SafeObj):
    def __init__(self, name="", count=1, vol=0.0, value=0):
        self.set_attr("name", name, str)
        self.set_attr("count", count, int)
        self.set_attr("vol", vol, float)
        self.set_attr("value", value, int)

    def vol_total(self):
        return self.count * self.vol

    @staticmethod
    def __str_header__():
        return f"{'count':<8}| {'vol':<8}| {'value':<8}| name\n"

    def __str__(self):
        return f"{self.count:<8}| {self.vol:<8}| {self.value:<8}| {self.name}"

    def set_attr(self, key, value, t=None):
        if key == "count" and value <= 0:
            raise InvalidArgument(f"The item count must be positive")

        if key == "vol" and value < 0:
            raise InvalidArgument(f"The item vol must be non-negative")

        if key == "value" and value < 0:
            raise InvalidArgument(f"The item value must be non-negative")

        super().set_attr(key, value, t)


class Inventory(SafeDict):
    def __init__(self, vol_max, *args, **kwargs):
        self.set_attr("vol_max", vol_max, float)

        super().__init__(str, Item, *args, **kwargs)

    def vol_current(self):
        return sum([i.vol_total() for i in self.values()])

    def vol_status(self):
        return f"{self.vol_current()}/{self.vol_max}"

    def __str__(self):
        s = Item.__str_header__()
        s += super().__str__()
        return s

    def set_attr(self, key, value, t=None):
        if key == "vol_max" and value <= 0:
            raise InvalidArgument("Max vol_max must be positive!")
        super().set_attr(key, value, t)

    def get_item(self, key):
        return super().get_item(key)

    def add_item(self, item):
        Item.check_type(item)

        future_vol = self.vol_current() + item.vol_total()

        if future_vol > self.vol_max:
            raise NotAllowed(
                f"The Item {item.name} is too big for this inventory! Its total volume is: "
                f"{item.vol_total()}. "
                f"The inventory status is: {self.vol_status()}"
            )

        if item.name in self:
            self[item.name].set_attr(item.count + self[item.name].count)
        else:
            self[item.name] = item

    def remove_item(self, item, count=-1):
        if type(count) is not int or count >= 0:
            raise InvalidArgument(f"Count must be a negative number!")

        Item.check_type(item)

        if item.name not in self:
            raise InvalidArgument(f"The item {item.name} is not present in the inventory")

        new_count = self[item.name].count + count
        if new_count == 0:
            del self[item.name]
        else:
            self[item.name].set_attr("count", new_count)

#
# a = Inventory(vol_max=5)
#
# a.add_item(Item("a", vol=2))
# a.add_item(Item("b", vol=3.0))
# # a.add_item("a")
# print(a)
# a.remove_item(Item("a"), -1)
#
# # a.add_item("A")
# q = {"q": Item("q")}
# a = Inventory(5, q)
# print(a)
#
#
# # a["bbb"] = Item("bbb")
# # a["aaa"] = Item("ccc")
#
# # print(a["aaa"])
#
# # q = Item("aaa")
# # print(q)
# # print(a)
