from django.core.exceptions import ValidationError
from django.test import TestCase
from sample.models import Task


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


def approve_audit_joiner(task, branches, reached):
    if branches.get('approval') == 102:
        return 'rejected'
    elif 'approval' in branches and 'audit' in branches:
        return 'satisfied'
    else:
        return None


def invoice_control_joiner(task, branches, reached):
    if branches.get('control') == 100:
        return 'on-reject'
    elif 'control' in branches and 'invoice' in branches:
        return 'on-accept'
    else:
        return None


def is_deliverable(document, user):
    return document.service_type == Task.DELIVERABLE


def is_non_deliverable(document, user):
    return document.service_type == Task.NON_DELIVERABLE


def is_service(document, user):
    return document.service_type == Task.SERVICE


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
