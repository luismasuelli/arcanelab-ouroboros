from __future__ import unicode_literals
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

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

    def __init__(self, raiser, message, code=None, params=None):
        ValidationError.__init__(self, message, code, params)
        WorkflowExceptionMixin.__init__(self, raiser)


class WorkflowStandardInvalidState(WorkflowInvalidState):
    """
    This subclass of WorkflowInvalidState prepares the used code
      in the CODE class attribute.
    """

    CODE = 'invalid'

    def __init__(self, raiser, message, params=None):
        super(WorkflowStandardInvalidState, self).__init__(raiser, message, self.CODE, params)


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


# WorkflowActionDenied subclasses


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


class WorkflowCourseAdvanceDeniedByWrongNodeType(WorkflowCourseAdvanceDenied):
    pass


# WorkflowInvalidState subclasses


class WorkflowModelFieldMustBeNull(WorkflowStandardInvalidState):
    CODE = 'non-null'


class WorkflowModelFieldMustNotBeNull(WorkflowStandardInvalidState):
    CODE = 'null'


class WorkflowModelFieldMustBeBlank(WorkflowStandardInvalidState):
    CODE = 'non-blank'


class WorkflowModelFieldMustNotBeBlank(WorkflowStandardInvalidState):
    CODE = 'blank'


class WorkflowSpecHasNoMainCourse(WorkflowStandardInvalidState):
    CODE = 'workflow-spec:no-main-course'


class WorkflowSpecHasMultipleMainCourses(WorkflowStandardInvalidState):
    CODE = 'workflow-spec:multiple-main-courses'


class WorkflowSpecHasCircularDependentCourses(WorkflowStandardInvalidState):
    CODE = 'workflow-spec:circular-dependent-courses'


class WorkflowCourseSpecHasNoRequiredNode(WorkflowStandardInvalidState):
    CODE = 'course-spec:no-required-node'


class WorkflowCourseSpecMultipleRequiredNodes(WorkflowStandardInvalidState):
    CODE = 'course-spec:multiple-required-nodes'


class WorkflowCourseSpecHasInvalidCallers(WorkflowStandardInvalidState):
    CODE = 'course-spec:invalid-callers'


class WorkflowCourseNodeHasInbounds(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-inbounds'


class WorkflowCourseNodeHasOutbounds(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-outbounds'


class WorkflowCourseNodeHasNoInbound(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-no-inbound'


class WorkflowCourseNodeHasNoOutbound(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-no-outbound'


class WorkflowCourseNodeHasMultipleOutbounds(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-multiple-outbounds'


class WorkflowCourseNodeHasOneOutbound(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-one-outbound'


class WorkflowCourseNodeHasBranches(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-branches'


class WorkflowCourseNodeHasNotEnoughBranches(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-not-enough-branches'


class WorkflowCourseNodeHasNoBranches(WorkflowStandardInvalidState):
    CODE = 'node-spec:node-has-no-branches'


class WorkflowCourseNodeInconsistentBranches(WorkflowStandardInvalidState):
    CODE = 'node-spec:inconsistent-branches'


class WorkflowCourseNodeInconsistentJoiner(WorkflowStandardInvalidState):
    CODE = 'node-spec:inconsistent-joiner'


class WorkflowCourseTransitionInconsistent(WorkflowStandardInvalidState):
    CODE = 'transition-spec:inconsistent'


class WorkflowCourseTransitionPriorityNotUnique(WorkflowStandardInvalidState):
    CODE = 'transition-spec:priority-not-unique'


class WorkflowCourseTransitionActionNameNotUnique(WorkflowStandardInvalidState):
    CODE = 'transition-spec:action-name-not-unique'


class WorkflowInstanceDoesNotAcceptDocument(WorkflowStandardInvalidState):
    CODE = 'workflow-instance:does-not-accept-document'


class WorkflowInstanceHasNoMainCourse(WorkflowStandardInvalidState):
    CODE = 'workflow-instance:no-main-course'


class WorkflowInstanceHasMultipleMainCourses(WorkflowStandardInvalidState):
    CODE = 'workflow-instance:multiple-main-courses'


class WorkflowCourseInstanceInconsistent(WorkflowStandardInvalidState):
    CODE = 'course-instance:inconsistent'


class WorkflowCourseNodeInstanceInconsistent(WorkflowStandardInvalidState):
    CODE = 'node-instance:inconsistent'


class WorkflowCourseNodeInstanceNonSplitAndHasBranches(WorkflowStandardInvalidState):
    CODE = 'node-instance:non-split-and-has-branches'


class WorkflowCourseNodeInstanceIncompleteSplitBranchReferences(WorkflowStandardInvalidState):
    CODE = 'node-instance:incomplete-split-branch-references'


# WorkflowNoSuchElement subclasses


class WorkflowInstanceDoesNotExist(WorkflowNoSuchElement):
    pass


class WorkflowCourseDoesNotExist(WorkflowNoSuchElement):
    pass


class WorkflowCourseNodeDoesNotExist(WorkflowNoSuchElement):
    pass


class WorkflowCourseInstanceDoesNotExist(WorkflowNoSuchElement):
    pass


class WorkflowCourseNodeTransitionDoesNotExist(WorkflowNoSuchElement):
    pass


# WorkflowExecutionError subclasses


class WorkflowCourseNodeMultiplexerDidNotSatisfyAnyCondition(WorkflowExecutionError):
    pass


class WorkflowCourseNodeNoTransitionResolvedAfterCompleteSplitJoin(WorkflowExecutionError):
    pass


class WorkflowCourseNodeInvalidSplitResolutionCode(WorkflowExecutionError, TypeError):
    pass


class WorkflowCourseNodeBadTransitionActionNamesAfterSplitNode(WorkflowExecutionError):
    pass


class WorkflowCourseNodeBadTransitionActionNamesForInputNode(WorkflowExecutionError):
    pass


class WorkflowCourseInstanceDoesNotAllowForeignNodes(WorkflowExecutionError):
    pass


class WorkflowCourseInstanceNotJoinable(WorkflowExecutionError):
    pass


class WorkflowCourseInstanceNotPending(WorkflowExecutionError):
    pass


class WorkflowCourseInstanceNotWaiting(WorkflowExecutionError):
    pass


class WorkflowCourseInstanceAlreadyTerminated(WorkflowExecutionError):
    pass


############################################################################
#                                                                          #
# Exception helpers go here. These exceptions are useful for verifiers.    #
#                                                                          #
############################################################################


def ensure(callable, obj, message, klass=WorkflowStandardInvalidState, params=None,
           wrap_does_not_exist=True):
    """
    A standard verifier that triggers subclasses of WorkflowStandardInvalidState
      exceptions.
    :param callable: The condition to expect be true.
    :param obj: Object to raise the exception from and evaluate the callable.
    :param message: The exception's message if the condition is false.
    :param klass: The exception's class if the condition is false.
    :param params: The exception's params if the condition is false.
    :param wrap_does_not_exist: If false, ObjectDoesNotExist exceptions are
      reraised. By default they are suppressed.
    :return:
    """

    try:
        if not callable(obj):
            raise klass(obj, message, params)
    except ObjectDoesNotExist:
        if not wrap_does_not_exist:
            raise


def ensure_field(field, obj, null=False, blank=False):
    """
    Ensures some field is present or not according to specified rulings.
    :param field: Field to query.
    :param obj: Model object to query the field.
    :param null: If the field is expected to be null.
    :param blank: If the field is expected to be blank (ignored if null=True).
    :return:
    """

    value = getattr(obj, field)
    if null and value is not None:
        raise WorkflowModelFieldMustBeNull(obj, {field: [_('This field must be null.')]})
    elif not null and value is None:
        raise WorkflowModelFieldMustNotBeNull(obj, {field: [_('This field cannot be null.')]})
    if blank is True and value:
        raise WorkflowModelFieldMustBeBlank(obj, {field: [_('This field must be blank.')]})
    elif blank is False and not value:
        raise WorkflowModelFieldMustNotBeBlank(obj, {field: [_('This field cannot be blank.')]})
