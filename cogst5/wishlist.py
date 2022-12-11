from cogst5.base import *
from cogst5.utils import *


class BbwWishlist(BbwObj):
    def __str__(self, detail_lvl=0, lname=None):
        return super().__str__(detail_lvl=detail_lvl, lsort=lambda x: (x.TL(), x.value(is_per_obj=True)), lname=lname)
