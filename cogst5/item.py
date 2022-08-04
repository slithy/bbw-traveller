from cogst5.base import *


class BbwItem(BbwObj):
    def __init__(self, value=0, TL=0, *args, **kwargs):

        self.set_value(value)
        self.set_TL(TL)

        super().__init__(*args, **kwargs)

    def TL(self):
        return self._TL

    def value(self):
        return self._value

    def set_TL(self, v):
        v = int(v)
        test_geq("TL", v, 0)
        test_leq("TL", v, 30)
        self._TL = v

    def set_value(self, v):
        v = int(v)
        test_geq("value", v, 0)
        self._value = v

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name()]
        else:
            return [self.count(), self.name(), self.TL(), self.value(), self.status()]

    def __str__(self, is_compact=True):
        return print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["count", "name"]
        else:
            return ["count", "name", "TL", "value", "status"]


# class ctx:
#     @staticmethod
#     def send(msg):
#         print("---")
#         print(msg)
#
# def print_long_message(msg):
#     """Split long messages to workaround the discord limit"""
#     max_length = 10
#
#     if len(msg) <= max_length:
#         ctx.send(msg)
#     else:
#         s = msg.split("\n")
#
#         j = 0
#         l = 0
#         for i in range(len(s)):
#             newl = l + len(s[i])
#             if newl <= max_length:
#                 l = newl
#                 continue
#             ctx.send("\n".join(s[j:i]))
#             j = i
#             l = len(s[i])
#
#         last_line = "\n".join(s[j:])
#         if last_line:
#             ctx.send(last_line)
#
# print_long_message("aaaaaa\naaaa\naaaaaaaaa\naaaa")
