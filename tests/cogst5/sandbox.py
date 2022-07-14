import json
import jsonpickle
from os.path import basename

jsonpickle.set_encoder_options('json', sort_keys=True)

class Obj(object):
    def __init__(self):
        self.a = "a"
        self.b = 3

class Dummy(object):
    def __init__(self):
        self.a = "a"
        self.data = {"a": "aaa", "b": 3, "c":Obj()}


def save_load(filename = "test.json"):
    """Save session data to a file in JSON format."""

    a = Dummy()

    enc_data = jsonpickle.encode(a)
    with open(f"../../save/{basename(filename)}", "w") as f:
        json.dump(json.loads(enc_data), f, indent=2)

    with open(f"../../save/{basename(filename)}", "r") as f:
        enc_data = json.dumps(json.load(f))
        b = jsonpickle.decode(enc_data)
    print(b)



if __name__ == '__main__':
    save_load()







