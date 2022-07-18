from cogst5.base import *

class BbwPerson(BbwObj):
    def __init__(self, is_crew=False, *args, **kwargs):

        self.set_is_crew(is_crew)
        super().__init__(*args, **kwargs)

    def is_crew(self):
        return self._is_crew

    def set_is_crew(self, v):
        v = bool(v)

        self._is_crew = v

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name()]
        else:
            return [self.count(), self.name(), self.is_crew(), self.capacity()]

    def __str__(self, is_compact=True):
        return print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["count", "name"]
        else:
            return ["count", "name", "is crew", "capacity"]