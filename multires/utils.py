from __future__ import unicode_literals, print_function


class AttrDict(dict):
    def __init__(self, data):
        super(AttrDict, self).__init__(data)
        self._convert(self, self.items())
        self.__dict__ = self

    def _convert(self, root, items):
        for k, v in items:
            if isinstance(v, dict):
                root[k] = AttrDict(v)
            elif isinstance(v, (list, tuple)):
                self._convert(v, enumerate(v))
