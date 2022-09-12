from cogst5.base import *


class BbwPlanet(BbwObj):
    def __init__(self, uwp, *args, **kwargs):
        self.set_uwp(uwp)

        super().__init__(*args, **kwargs)

    def uwp(self):
        return self._uwp

    def set_uwp(self, v):
        v = str(v)
        test_geq("TL", v, 0)
        test_leq("TL", v, 30)
        self._TL = v
