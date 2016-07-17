from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist

#####################################################################################
#                                                                                   #
# Exceptions we care about are three standard exception in Python/Django. They are: #
# - ValidationError: Useful when the spec is somehow wrong, or an instance has      #
#   become inconsistent somehow (e.g. node.course vs course_instance.course).       #
#   Associated with a 400 (or 422, but Django uses 400) error.                      #
# - PermissionDenied: Useful when trying to perform an action we don't have         #
#   permission to (actions include: create workflow, cancel workflow, triggering an #
#   action from an input node and either failing the permission on the input node   #
#   or on the chosen transition).                                                   #
#   Associated with a 403 error.                                                    #
# - RuntimeError: A non-specific error which would happen when trying to execute a  #
#   workflow operation in some way, or something was wrong in specific unforeseen   #
#   parts like user callables in nodes and transitions.                             #
#   Associated with a 500 error.                                                    #
# - LookupError: When a required code (e.g. course, or transition) cannot be found. #
#   Associated with a 404 error.                                                    #
#                                                                                   #
#####################################################################################


class WorkflowExceptionMixin(object):
    """
    A mix-in for workflow exceptions.
    """

    def __init__(self, raiser):
        self.raiser = raiser


class WorkflowInvalidState(WorkflowExceptionMixin, ValidationError):
    """
    Validation errors are useful on workflow-related checks.

    Methods like .clean() can raise this exception directly but
      most likely this exception will not be raised directly in
      a clean method but in a verifier method called inside such
      clean method.

    No wrapping is necessary since this is already a ValidationError.
    """

    def __init__(self, raiser, code, message, params=None):
        ValidationError.__init__(self, message, code, params)
        WorkflowExceptionMixin.__init__(self, raiser)


class WorkflowStandardInvalidState(WorkflowInvalidState):
    """
    This subclass of WorkflowInvalidState prepares the used code
      in the CODE class attribute.
    """

    CODE = 'invalid'

    def __init__(self, raiser, message, params=None):
        super(WorkflowStandardInvalidState, self).__init__(raiser, self.CODE, message, params)


class WorkflowActionDenied(WorkflowExceptionMixin, PermissionDenied):
    """
    This action is useful when a permission was denied. Permissions
      are denied when a user wants to create a workflow (and it does
      not has the permission stated by the workflow spec to create
      it) or execute a restricted action from an Input node.
    """

    def __init__(self, raiser, *args, **kwargs):
        PermissionDenied.__init__(self, *args, **kwargs)
        WorkflowExceptionMixin.__init__(self, raiser)


class WorkflowExecutionError(WorkflowExceptionMixin, RuntimeError):
    """
    Any unmatched exception happening not due to validation or permission
      but due an unfulfilled condition, will subclass from here.
    """

    def __init__(self, raiser, *args, **kwargs):
        RuntimeError.__init__(self, *args, **kwargs)
        WorkflowExceptionMixin.__init__(self, raiser)


class WorkflowNoSuchElement(WorkflowExceptionMixin, LookupError):
    """
    This exception will be triggered when trying to find a specific element
      related to a workflow execution (e.g. course code, transition code).
    """

    def __init__(self, raiser, *args, **kwargs):
        LookupError.__init__(self, *args, **kwargs)
        WorkflowExceptionMixin.__init__(self, raiser)


############################################################################
#                                                                          #
# Exception subclasses start here. Finally we will be using them directly. #
#                                                                          #
############################################################################

class WorkflowCreateDenied(WorkflowActionDenied):
    """
    This exception will be triggered when a user attempts to create a
      workflow instance, but does not have permission for that.
    """


class WorkflowCourseCancelDenied(WorkflowActionDenied):
    """
    This exception will be triggered when a user attempts to cancel a
      workflow course instance, but does not have permission for that.

    Two possible cases here:
      - The user did not satisfy the workflow permission for cancelling.
      - The user did not satisfy the (optional) course permission for
        cancelling.

    When trying to cancel a workflow, the actual attempt is -internally-
      to cancel the main course.
    """


class WorkflowCourseCancelDeniedByWorkflow(WorkflowCourseCancelDenied):
    pass


class WorkflowCourseCancelDeniedByCourse(WorkflowCourseCancelDenied):
    pass


class WorkflowCourseAdvanceDenied(WorkflowActionDenied):
    """
    This exception will be triggered when a user, which is on an Input
      node, is trying to execute a certain transition (action), but
      does not have permission for that.

    Two possible cases here:
      - The user did not satisfy the (optional) node permission.
      - The user did not satisfy the (optional) transition permission.
    """


class WorkflowCourseAdvanceDeniedByNode(WorkflowCourseAdvanceDenied):
    pass


class WorkflowCourseAdvanceDeniedByTransition(WorkflowCourseAdvanceDenied):
    pass


############################################################################
#                                                                          #
# Exception helpers go here. These exceptions are useful for verifiers.    #
#                                                                          #
############################################################################


def ensure(callable, message, klass=WorkflowStandardInvalidState, params=None,
           wrap_does_not_exist=True):
    """
    A standard verifier that triggers subclasses of WorkflowStandardInvalidState
      exceptions.
    :param callable: The condition to expect be true.
    :param message: The exception's message if the condition is false.
    :param klass: The exception's class if the condition is false.
    :param params: The exception's params if the condition is false.
    :param wrap_does_not_exist: If false, ObjectDoesNotExist exceptions are
      reraised. By default they are suppressed.
    :return:
    """

    try:
        if not callable():
            raise klass(message, params)
    except ObjectDoesNotExist:
        if not wrap_does_not_exist:
            raise
