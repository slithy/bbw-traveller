from ..models.errors import *

def safe_conv(v, t):
    if t is None:
        return v
    try:
        return t(v)
    except ValueError:
        raise InvalidArgument(f"{v} of type {type(v).__name__} must be castable to {t.__name__}")

class SafeDict(dict):
    def __init__(self, kt, vt, *args, **kwargs):
        self.kt = kt
        self.vt = vt
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "\n".join([f"{k}: {self[k]}" for k in self])

    def __setitem__(self, key, value):
        key = safe_conv(key, self.kt)
        value = safe_conv(value, self.vt)

        super().__setitem__(key, value)

    def _check_getitem_list(self, key, l):
        if len(l) == 1:
            return l[0][1]
        if len(l) > 0:
            keys, _ = zip(*l)
            raise SelectionException(f"Multiple matches for key {key}: {keys}")
        return None

    def __getitem__(self, key):
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