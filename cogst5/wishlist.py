from cogst5.base import *
from cogst5.utils import *


class BbwWishlist(BbwContainer):
    def __str__(self, detail_lvl=0):
        s = ""
        s += BbwUtils.print_table(self._str_table(detail_lvl), headers=self._header(detail_lvl), detail_lvl=detail_lvl)

        if detail_lvl != 0 and len(self.keys()):
            s += "\n"
            h = type(list(self.values())[0])._header(detail_lvl=1)

            vals = sorted(self.values(), key=lambda x: (x.TL(), x.value()))
            t = [i._str_table(detail_lvl=1) for i in vals]
            s += BbwUtils.print_table(t, headers=h, detail_lvl=1)

        return s
