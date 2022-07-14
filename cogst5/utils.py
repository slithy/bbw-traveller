from models.errors import *


def safe_conv(v, t):
    if t is None or t == type(v):
        return v

    try:
        return t(v)
    except ValueError:
        raise InvalidArgument(f"{v} of type {type(v).__name__} must be castable to {t.__name__}")
