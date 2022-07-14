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

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            pm = [i for i in self.keys() if i.startswith(key)]
            if len(pm) == 1:
                return pm[0]
            elif len(pm) > 0:
                raise SelectionException(f"Multiple matches for key {key}: {pm}")
            else:
                pm = [i for i in self.keys() if key in i]
                if len(pm) == 1:
                    return pm[0]
                elif len(pm) > 0:
                    raise SelectionException(f"Multiple matches for key {key}: {pm}")
                else:
                    raise SelectionException(f"Unknown key: {key}")
