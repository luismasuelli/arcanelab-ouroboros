from django.core.exceptions import ValidationError
from django.test import TestCase


def dummy_joiner(*args):
    # This joiner is useless and will raise errors on last join.
    # Declared only for test (placeholder) purposes
    return None


def dummy_condition_a(*args):
    # This conditions is useless. Always returns False.
    # Declared only for test (placeholder) purposes
    return None


def dummy_condition_b(*args):
    # This conditions is useless. Always returns False.
    # Declared only for test (placeholder) purposes
    return None


def dummy_condition_c(*args):
    # This conditions is useless. Always returns False.
    # Declared only for test (placeholder) purposes
    return None


class ValidationErrorWrappingTestCase(TestCase):

    def unwrapValidationError(self, exception, field='__all__'):
        ed_items = exception.error_dict
        self.assertEqual(len(ed_items), 1, 'The raised ValidationError produces an invalid count of errors (expected 1)')
        self.assertIn(field, ed_items, 'The raised ValidationError produces errors for other fields than %s' % field)
        self.assertIsInstance(ed_items[field], list, 'The raised ValidationError has a non-list object in %s' % field)
        self.assertEqual(len(ed_items[field]), 1, 'The raised ValidationError has more than one error in %s' % field)
        self.assertIsInstance(ed_items[field][0], ValidationError, 'The raised ValidationError has a non-list object in'
                                                                   ' %s' % field)
        return ed_items[field][0]
