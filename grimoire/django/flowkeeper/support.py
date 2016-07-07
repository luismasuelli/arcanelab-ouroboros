from __future__ import unicode_literals
from collections import namedtuple
from contextlib import contextmanager
from django.core.exceptions import ValidationError, PermissionDenied
import sys


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


class WorkflowExceptionMixin(object):

    def __init__(self, raiser):
        self.raiser = raiser


class WorkflowInvalidState(WorkflowExceptionMixin, ValidationError):

    CODE = 'invalid-state'

    def __init__(self, raiser, message, params=None):
        ValidationError.__init__(self, message, self.CODE, params)
        WorkflowExceptionMixin.__init__(self, raiser)


class WorkflowOtherValidationError(WorkflowInvalidState):

    CODE = 'other-validation-error'


class WorkflowHasMultipleMainCourses(WorkflowInvalidState):

    CODE = 'workflow:has-multiple-main-courses'


class WorkflowHasNoMainCourse(WorkflowInvalidState):

    CODE = 'workflow:has-no-main-course'


class WorkflowInstanceHasMultipleMainCourses(WorkflowInvalidState):

    CODE = 'workflow-instance:has-multiple-main-courses'


class WorkflowInstanceHasNoMainCourse(WorkflowInvalidState):

    CODE = 'workflow-instance:has-no-main-course'


class WorkflowActionDenied(WorkflowExceptionMixin, PermissionDenied):

    def __init__(self, raiser, *args, **kwargs):
        PermissionDenied.__init__(self, *args, **kwargs)
        WorkflowExceptionMixin.__init__(self, raiser)


class WorkflowCannotInstantiate(WorkflowActionDenied):
    pass


class WorkflowInstanceTransitionDenied(WorkflowActionDenied):
    pass


class WorkflowMiscException(WorkflowExceptionMixin, Exception):

    def __init__(self, raiser, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        WorkflowExceptionMixin.__init__(self, raiser)


class WorkflowCourseCodeDoesNotExist(WorkflowMiscException):
    pass


class WorkflowMultiplexerChoseNoTransition(WorkflowMiscException):
    pass


class WorkflowSplitResolutionNeedsTransitionCodeMixin(WorkflowMiscException):
    pass


class WorkflowTransitionCodeDoesNotExist(WorkflowMiscException):
    pass


class WorkflowTransitionCodeNotUnique(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNotPending(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNotRunning(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNodeDoesNotHaveChildren(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNodeInconsistent(WorkflowMiscException):
    pass


@contextmanager
def wrap_validation_error(raiser):
    try:
        yield
    except WorkflowInvalidState:
        raise
    except ValidationError as error:
        raise WorkflowOtherValidationError, (raiser, error), sys.exc_info()[2]
