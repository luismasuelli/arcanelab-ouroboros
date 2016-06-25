from __future__ import unicode_literals
from collections import namedtuple


class CallableReference(namedtuple('Reference', ('path',))):

    def __call__(self, *args, **kwargs):
        """
        Imports and invokes the callable.
        :param args:
        :param kwargs:
        :return:
        """

        try:
            path, variable = self.path.rsplit('.', 1)
        except ValueError:
            raise ImportError('Import path should involve both a path and an object reference. '
                              'Given: %s' % self.path)
        except AttributeError:
            raise TypeError('Attribute type should be a string')

        return getattr(__import__(path), variable)(*args, **kwargs)
