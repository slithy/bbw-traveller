from models.errors import *
from utils import safe_conv


class SafeObj:
    def set_attr(self, key, value, t=None):
        if t is None:
            try:
                t = type(self.__dict__[key])
            except KeyError:
                raise NotAllowed(f"Assigning a new attribute to {type(self).__name__} is not allowed!")

        value = safe_conv(value, t)
        setattr(self, key, value)

    def __str__(self):
        return "\n".join([f"{k}: {getattr(self, k)}" for k in self.__dict__])

    @classmethod
    def check_type(cls, obj):
        if type(obj) is not cls:
            raise InvalidArgument(f"{obj} must be a {cls.__name__} instance")


class SafeDict(SafeObj):
    def __init__(self, kt, vt, *args, **kwargs):
        self.kt = None
        if kt:
            self.set_attr("kt", kt, type)
        self.vt = None
        if vt:
            self.set_attr("vt", vt, type)

        self.d = {}
        self.d.__init__(*args, **kwargs)

    def __str__(self):
        return "\n".join([str(i) for i in self.values()])

    def __setitem__(self, k, v):
        k = safe_conv(k, self.kt)
        v = safe_conv(v, self.vt)

        return self.d.__setitem__(k, v)

    def __getitem__(self, k):
        return self.d.__getitem__(k)

    def __delitem__(self, v):
        return self.d.__delitem__(v)

    def __contains__(self, item):
        return self.d.__contains__(item)

    def values(self):
        return self.d.values()

    def keys(self):
        return self.d.keys()

    def items(self):
        return self.d.items()

    def _check_getitem_list(self, key, l):
        if len(l) == 1:
            return l[0][1]
        if len(l) > 0:
            keys, _ = zip(*l)
            raise SelectionException(f"Multiple matches for key {key}: {keys}")
        return None

    def get_item(self, key):
        ans = self._check_getitem_list(key, [(k, v) for k, v in self.items() if key == k])
        if ans:
            return ans
        ans = self._check_getitem_list(key, [(k, v) for k, v in self.items() if key.lower() == k.lower()])
        if ans:
            return ans
        # If we want to check by prefix, reenable this
        # ans = self._check_getitem_list(key, [(k, v) for k, v in self.items() if k.startswith(key)])
        # if ans:
        #     return ans
        # ans = self._check_getitem_list(key, [(k, v) for k, v in self.items() if k.lower().startswith(key.lower())])
        # if ans:
        #     return ans
        ans = self._check_getitem_list(key, [(k, v) for k, v in self.items() if key in k])
        if ans:
            return ans
        ans = self._check_getitem_list(key, [(k, v) for k, v in self.items() if key.lower() in k.lower()])
        if ans:
            return ans

        raise SelectionException(f"Unknown key: {key}")
