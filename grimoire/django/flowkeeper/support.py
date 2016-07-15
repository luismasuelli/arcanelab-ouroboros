from __future__ import unicode_literals
from collections import namedtuple
from contextlib import contextmanager
from cantrips.functions import is_function
from functools import wraps
from django.core.exceptions import ValidationError, PermissionDenied
from cantrips.decorators import customizable
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


class WorkflowCourseNodeCodeDoesNotExist(WorkflowMiscException):
    pass


class WorkflowCourseNodeTypeDoesNotExist(WorkflowMiscException):
    pass


class WorkflowCourseNodeTypeNotUnique(WorkflowMiscException):
    pass


class WorkflowInstanceCourseCodeDoesNotExist(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNodeCannotBeForeign(WorkflowMiscException):
    pass


class WorkflowInstanceCourseCodeMultipleTimes(WorkflowMiscException):
    pass


class WorkflowMultiplexerChoseNoTransition(WorkflowMiscException):
    pass


class WorkflowSplitResolutionNeedsTransitionCode(WorkflowMiscException):
    pass


class WorkflowSplitResolutionTransitionCodeDoesNotExist(WorkflowMiscException):
    pass


class WorkflowSplitResolutionTransitionCodeNotUnique(WorkflowMiscException):
    pass


class WorkflowSplitResolutionBadValue(WorkflowMiscException, TypeError):
    pass


class WorkflowTransitionCodeDoesNotExist(WorkflowMiscException):
    pass


class WorkflowTransitionCodeNotUnique(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNotPending(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNotRunning(WorkflowMiscException):
    pass


class WorkflowInstanceCourseAlreadyTerminated(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNodeDoesNotHaveChildren(WorkflowMiscException):
    pass


class WorkflowInstanceCourseInconsistent(WorkflowMiscException):
    pass


class WorkflowInstanceCourseNodeInconsistent(WorkflowMiscException):
    pass


def _default_exfactory(raiser, error):
    return WorkflowOtherValidationError, (raiser, error)


@contextmanager
def wrap_validation_error(raiser, exfactory=_default_exfactory):
    """
    This context manager catches any exception and, if being
      a plain validation error, it converts it to another type
      of exception, which will be given by the exfactory argument.

    This context manager takes the raiser into account (a workflow
      spec or workflow instance related to the exception).
    :param raiser: The related object
    :param exfactory: A function taking the related object and
      the already thrown ValidationError exception, that will
      return the parameters needed for the three-args raise.
    :return: A Context Generator.
    """
    try:
        yield
    except WorkflowInvalidState:
        raise
    except ValidationError as error:
        traceback = sys.exc_info()[2]
        klass, args = exfactory(raiser, error)
        raise klass, args, traceback


def _wraps_validation_error(function, wrapper):
    """
    This decorator wraps any **method** that will make the resulting
      function accept an additional keyword argument (keep) and
      will call -if such argument is used- `wrap_validation_error`
      wrapping the execution of the decorated function. Such wrapper
      takes the self into account, and that's the reason why this
      decorator is intended only for methods.

    This decorator is used either as:

        @wraps_validation_error
        def mymethod(self, foo, bar, ...):
            ...

    Or

        @wraps_validation_error(a_wrapper_function)
        def mymethod(self, foo, bar, ...):
            ...

    By default, @wraps_validation_error uses a wrapper function converting
      the ValidationError in a WorkflowInvalidState.

    By default, the resulting function will invoke the wrapping. To retrieve
      the original ValidationError, invoke the resulting function with
      argument keep=True,
    :param function:
    :return:
    """
    @wraps(function)
    def wrapper(self, *args, **kwargs):
        keep = kwargs.pop('keep', False)
        if keep:
            return function(self, *args, **kwargs)
        else:
            with wrap_validation_error(self, wrapper):
                return function(self, *args, **kwargs)
    return wrapper
wraps_validation_error = customizable(_wraps_validation_error, wrapper=_default_exfactory)