from cogst5.base import *
from cogst5.utils import *


class BbwWishlist(BbwContainer):
    def __str__(self, is_compact=True):
        s = ""
        s += BbwUtils.print_table(self._str_table(is_compact), headers=self._header(is_compact))

        if not is_compact and len(self.keys()):
            entries_is_compact = False
            s += "\n"
            h = type(list(self.values())[0])._header(is_compact=entries_is_compact)

            vals = sorted(self.values(), key=lambda x: (x.TL(), x.value()))
            t = [i._str_table(is_compact=entries_is_compact) for i in vals]
            s += BbwUtils.print_table(t, headers=h)

        return s
