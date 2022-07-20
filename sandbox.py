import json
import jsonpickle
from os.path import basename
from cogst5.game.utils import safe_conv
from cogst5.models.errors import *

jsonpickle.set_encoder_options('json', sort_keys=True)

# class Obj(object):
#     def __init__(self):
#         self.a = "a"
#         self.b = 3
#
# class Dummy(object):
#     def __init__(self):
#         self.a = "a"
#         self.data = {"a": "aaa", "b": 3, "c":Obj()}

#
# def save_load(filename = "test.json"):
#     """Save session data to a file in JSON format."""
#
#     a = Dummy()
#
#     enc_data = jsonpickle.encode(a)
#     with open(f"save/{basename(filename)}", "w") as f:
#         json.dump(json.loads(enc_data), f, indent=2)
#
#     with open(f"save/{basename(filename)}", "r") as f:
#         enc_data = json.dumps(json.load(f))
#         b = jsonpickle.decode(enc_data)
#     print(b)


# def safe_item():
#     a = Item()
#     a.set_attr("name", "AA")
#     print(a)
#     a.set_attr("name", 3)
#     print(type(a.name))
#     a.set_attr("value", 3.2)
#     a.set_attr("value", "AA")
#
#
#
#
#
# class Obj(SafeObj):
#     pass
#
# a = Obj()
#
# a.set_attr("a", 3, int)
# a.set_attr("a", 4.1)
# a.set_attr("a", "AA")
#
#
# print(a)





# if __name__ == '__main__':
#
#
#     # save_load()
#     # safe_item()
#     pass





