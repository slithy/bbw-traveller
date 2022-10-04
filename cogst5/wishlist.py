from cogst5.base import *
from cogst5.utils import *


class BbwWishlist(BbwContainer):
    pass

    def __str__(self, detail_lvl=0):
        return super().__str__(detail_lvl=detail_lvl, lsort=lambda x: (x.TL(), x.value(is_per_obj=True)))
