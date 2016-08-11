from __future__ import unicode_literals
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from grimoire.django.tracked.models import TrackedLive
from . import exceptions, fields


#   since this pkg is not yet released.


def valid_document_type(value):
    if value:
        poop = False
        try:
            if not issubclass(ContentType.objects.get(pk=value).model_class(), Document):
                poop = True
        except ContentType.DoesNotExist:
            poop = True
        if poop:
            raise ValidationError(_('The `document_type` field must reference a subclass of Document'))


class Document(models.Model):
    """
    Base class for any model accepting a workflow
    """

    class Meta:
        abstract = True


class WorkflowManager(models.Manager):

    def get_by_natural_key(self, code):
        return self.get(code=code)


class WorkflowSpec(models.Model):
    """
    Workflow class. Defines itself, and the document type it can associate to.
    """

    document_type = models.ForeignKey(ContentType, null=False, blank=False, on_delete=models.CASCADE,
                                      validators=[valid_document_type], verbose_name=_('Document Type'),
                                      help_text=_('Accepted related document class'))
    code = models.SlugField(max_length=30, null=False, blank=False, unique=True, verbose_name=_('Code'),
                            help_text=_('Internal (unique) code'))
    name = models.CharField(max_length=60, null=False, blank=False, verbose_name=_('Name'))
    description = models.TextField(max_length=1023, null=False, blank=True, verbose_name=_('Description'))
    create_permission = models.CharField(max_length=201, blank=True, null=True, verbose_name=_('Create Permission'),
                                         help_text=_('Permission code (as <application>.<permission>) to test against '
                                                     'when a workflow instance is created. The user who intends to '
                                                     'create a workflow instance must satisfy this permission against '
                                                     'the associated document.'))
    cancel_permission = models.CharField(max_length=201, blank=True, null=True, verbose_name=_('Cancel Permission'),
                                         help_text=_('Permission code (as <application>.<permission>) to test against '
                                                     'when a course instance is cancelled. The user who intends to '
                                                     'cancel a course instance in this workflow must satisfy this '
                                                     'permission against the associated document.'))
    objects = WorkflowManager()

    def natural_key(self):
        return self.code

    def verify_exactly_one_parent_course(self):
        """
        Verifies only one course for the workflow.
        :return:
        """

        try:
            return self.course_specs.get(callers__isnull=True)
        except CourseSpec.DoesNotExist:
            raise exceptions.WorkflowSpecHasNoMainCourse(self, _('No main course is defined for the workflow '
                                                                 '(expected one)'))
        except CourseSpec.MultipleObjectsReturned:
            raise exceptions.WorkflowSpecHasMultipleMainCourses(self, _('Multiple main courses are defined for the '
                                                                        'workflow (expected one)'))

    def verify_acyclic_courses(self):
        """
        Verifies the whole courses set is acyclic in dependencies. This verification was
          moved from courses to workflow.
        :return:
        """

        traversed_courses = set()
        exploring_courses = set()
        root = self.verify_exactly_one_parent_course()

        def set_exploring(courses):
            # Set the new nodes being explored.
            # Also add these new nodes to the traversed ones.
            codes = set(course.code for course in courses)
            traversed_courses.update(codes)
            exploring_courses.clear()
            exploring_courses.update(courses)
            return courses

        def get_traversable_children(courses):
            return set(branch for course in courses
                              for node in course.node_specs.all()
                              for branch in node.branches.all()
                              if set(caller.course_spec.code for caller in branch.callers.all()) <= traversed_courses)

        children = set_exploring([root])
        while True:
            children = set_exploring(get_traversable_children(children))
            if not children:
                break

        if self.course_specs.exclude(code__in=traversed_courses).exists():
            raise exceptions.WorkflowSpecHasCircularDependentCourses(
                self, _('This workflow has at least one circular dependent course')
            )

    def clean(self):
        """
        A workflow must validate by having:
        - Exactly one parent Course.
        """

        if self.pk:
            self.verify_acyclic_courses()

    class Meta:
        verbose_name = _('Workflow Spec')
        verbose_name_plural = _('Workflow Specs')


class CourseManager(models.Manager):

    def get_by_natural_key(self, wf_code, code):
        return self.get(workflow_spec__code=wf_code, code=code)


class CourseSpec(models.Model):
    """
    Workflow action course.
    """

    workflow_spec = models.ForeignKey(WorkflowSpec, null=False, blank=False, on_delete=models.CASCADE,
                                      related_name='course_specs', verbose_name=_('Workflow Spec'),
                                      help_text=_('Workflow spec this course spec belongs to'))
    code = models.SlugField(max_length=30, null=False, blank=True, verbose_name=_('Code'),
                            help_text=_('Internal (unique) code'))
    name = models.CharField(max_length=60, null=False, blank=False, verbose_name=_('Name'))
    description = models.TextField(max_length=1023, null=False, blank=True, verbose_name=_('Description'))
    cancel_permission = models.CharField(max_length=201, blank=True, null=True, verbose_name=_('Cancel Permission'),
                                         help_text=_('Permission code (as <application>.<permission>) to test against '
                                                     'when this course instance is cancelled. The user who intends to '
                                                     'cancel this course instance must satisfy this permission against '
                                                     'the associated document.'))
    objects = CourseManager()

    def natural_key(self):
        return self.workflow.code, self.code

    def _verify_has_node_of_type(self, node_type, msg):
        try:
            return self.node_specs.get(type=node_type)
        except NodeSpec.DoesNotExist:
            raise exceptions.WorkflowCourseSpecHasNoRequiredNode(self, msg)
        except NodeSpec.MultipleObjectsReturned:
            raise exceptions.WorkflowCourseSpecMultipleRequiredNodes(self, msg)

    def verify_has_cancel_node(self):
        return self._verify_has_node_of_type(NodeSpec.CANCEL, _('A workflow course is expected to have exactly one '
                                                                'cancel node'))

    def verify_has_joined_node(self):
        if not self.callers.exclude(joiner__isnull=True).exists():
            return
        return self._verify_has_node_of_type(NodeSpec.JOINED, _('A non-root workflow course is expected to have '
                                                                'one joined node when having at least one calling '
                                                                'split with a joiner callable'))

    def verify_has_enter_node(self):
        return self._verify_has_node_of_type(NodeSpec.ENTER, _('A workflow course is expected to have exactly one '
                                                               'enter node'))

    def verify_has_exit_nodes(self):
        try:
            return self.node_specs.get(type=NodeSpec.EXIT)
        except NodeSpec.DoesNotExist:
            raise exceptions.WorkflowCourseSpecHasNoRequiredNode(self, _('A workflow course is expected to have at '
                                                                         'least one exit node'))
        except NodeSpec.MultipleObjectsReturned:
            # We forgive this case, since it shows many exit nodes exist.
            pass

    def verify_hierarchy(self):
        if self.callers.exists():
            self.verify_has_joined_node()
            if self.callers.exclude(type=NodeSpec.SPLIT).exists():
                raise exceptions.WorkflowCourseSpecHasInvalidCallers(
                    self, _('A child workflow course is expected to have only SPLIT type calling nodes')
                )

    def clean(self):
        """
        A course must validate by having:
        - Exactly one enter node.
        - Exactly one "cancel" exit node.
        - At least one non-"cancel" exit node.
        """

        if self.pk:
            self.verify_has_enter_node()
            self.verify_has_cancel_node()
            self.verify_has_exit_nodes()
            self.verify_hierarchy()
            if (self.code == '') == (self.callers.exists()):
                raise ValidationError(_('A course should have an empty code if, and only if, it is the root'))

    class Meta:
        verbose_name = _('Course Spec')
        verbose_name_plural = _('Course Specs')
        unique_together = (('workflow_spec', 'code'),)


class NodeSpec(models.Model):
    """
    Workflow action course node.
    """

    ENTER = 'enter'
    EXIT = 'exit'
    CANCEL = 'cancel'
    JOINED = 'joined'
    INPUT = 'input'
    STEP = 'step'
    MULTIPLEXER = 'multiplexer'
    SPLIT = 'split'

    TYPES = (
        (ENTER, _('Enter')),
        (EXIT, _('Exit')),
        (CANCEL, _('Cancel')),
        (JOINED, _('Joined')),
        (INPUT, _('Input')),
        (STEP, _('Step')),
        (MULTIPLEXER, _('Multiplexer')),
        (SPLIT, _('Split'))
    )

    type = models.CharField(max_length=15, null=False, blank=False, choices=TYPES,
                            verbose_name=_('Type'), help_text=_('Node type'))
    course_spec = models.ForeignKey(CourseSpec, null=False, blank=False, on_delete=models.CASCADE,
                                    related_name='node_specs', verbose_name=_('Course Spec'),
                                    help_text=_('Course spec this node spec belongs to'))
    code = models.SlugField(max_length=30, null=False, blank=False, verbose_name=_('Code'),
                            help_text=_('Internal (unique) code'))
    name = models.CharField(max_length=60, null=False, blank=False, verbose_name=_('Name'))
    description = models.TextField(max_length=1023, null=False, blank=True, verbose_name=_('Description'))
    landing_handler = fields.CallableReferenceField(blank=True, null=True, verbose_name=_('Landing Handler'),
                                                    help_text=_('A callable that will triggered when this node is '
                                                                'reached. The expected signature is (document, user) '
                                                                'since no interaction is expected to exist with the '
                                                                'workflow instance, but the handlers should perform '
                                                                'actions in the document'))
    # Exit nodes will have an exit value
    exit_value = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('Exit Value'),
                                                  help_text=_('Exit value. Expected only for exit nodes'))
    # Only for split nodes
    joiner = fields.CallableReferenceField(blank=True, null=True, verbose_name=_('Joiner'),
                                           help_text=_('A callable that will be triggered every time a split\'s branch '
                                                       'reaches an end. The split\'s branch will trigger this callable '
                                                       'which must return a valid transition name (existing action as '
                                                       'outbound in this node) to leave the split and take an action, '
                                                       'or None to remain in the split and wait for other branches (an '
                                                       'exception will be raised if None is returned but no branch is '
                                                       'still to finish). Its contract is (document, statuses, last) '
                                                       'being the associated document, a dictionary of branch codes '
                                                       'and their exit values (None: running; -1: cancelled or joined,'
                                                       '>= 0: terminated by exit node), and the code of the branch '
                                                       'being joined (such code will be present in the dictionary)'))
    # Only for input nodes
    execute_permission = models.CharField(max_length=201, blank=True, null=True, verbose_name=_('Cancel Permission'),
                                          help_text=_('Permission code (as <application>.<permission>) to test against '
                                                      'when an action on this node is executed. The user who intends '
                                                      'to execute the action in this node must satisfy this permission '
                                                      'against the associated document'))
    branches = models.ManyToManyField(CourseSpec, blank=True, related_name='callers', verbose_name=_('Branches'),
                                      help_text=_('Courses this node branches to. Expected only for split nodes'))

    def verify_node_has_no_inbounds(self):
        exceptions.ensure(lambda obj: not obj.inbounds.exists(), self, _('This node must not have inbounds'),
                          exceptions.WorkflowCourseNodeHasInbounds)

    def verify_node_has_no_outbounds(self):
        exceptions.ensure(lambda obj: not obj.outbounds.exists(), self, _('This node must not have outbounds'),
                          exceptions.WorkflowCourseNodeHasOutbounds)

    def verify_node_has_inbounds(self):
        exceptions.ensure(lambda obj: obj.inbounds.exists(), self, _('This node must have inbounds'),
                          exceptions.WorkflowCourseNodeHasNoInbound)

    def verify_node_has_outbounds(self):
        exceptions.ensure(lambda obj: obj.outbounds.exists(), self, _('This node must have outbounds'),
                          exceptions.WorkflowCourseNodeHasNoOutbound)

    def verify_node_has_one_outbound(self):
        try:
            return self.outbounds.get()
        except TransitionSpec.DoesNotExist:
            raise exceptions.WorkflowCourseNodeHasNoOutbound(self, _('This node must have exactly one outbound'))
        except TransitionSpec.MultipleObjectsReturned:
            raise exceptions.WorkflowCourseNodeHasMultipleOutbounds(self, _('This node must have exactly one outbound'))

    def verify_node_has_many_outbounds(self):
        try:
            self.outbounds.get()
            raise exceptions.WorkflowCourseNodeHasOneOutbound(self, _('This node must have more than one outbound'))
        except TransitionSpec.DoesNotExist:
            raise exceptions.WorkflowCourseNodeHasNoOutbound(self, _('This node must have more than one outbound'))
        except TransitionSpec.MultipleObjectsReturned:
            return self.outbounds.all()

    def verify_node_has_many_branches(self):
        exceptions.ensure(lambda obj: obj.branches.count() > 1, self, _('This node must have at least two branches'),
                          exceptions.WorkflowCourseNodeHasNotEnoughBranches)
        try:
            if self.branches.exclude(workflow_spec=self.course_spec.workflow_spec).exists():
                raise exceptions.WorkflowCourseNodeInconsistentBranches(self, _('Split nodes must branch to courses in '
                                                                                'the same workflow'))
        except CourseSpec.DoesNotExist:
            pass
        if not self.joiner and (self.outbounds.count() > 1):
            raise exceptions.WorkflowCourseNodeInconsistentJoiner(self, _('Split nodes with many outbounds must have '
                                                                          'joiner'))

    def verify_node_has_no_branches(self):
        exceptions.ensure(lambda obj: not obj.branches.exists(), self, _('This node must have no branches'),
                          exceptions.WorkflowCourseNodeHasBranches)

    def verify_enter_node(self):
        self.verify_node_has_no_inbounds()
        self.verify_node_has_one_outbound()
        self.verify_node_has_no_branches()
        exceptions.ensure_field('exit_value', self, True, True)
        exceptions.ensure_field('joiner', self, True, True)
        exceptions.ensure_field('execute_permission', self, True, True)

    def verify_exit_node(self):
        self.verify_node_has_no_outbounds()
        self.verify_node_has_inbounds()
        self.verify_node_has_no_branches()
        exceptions.ensure_field('exit_value', self)
        exceptions.ensure_field('joiner', self, True, True)
        exceptions.ensure_field('execute_permission', self, True, True)

    def verify_isolated_node(self):
        self.verify_node_has_no_inbounds()
        self.verify_node_has_no_outbounds()
        self.verify_node_has_no_branches()
        exceptions.ensure_field('exit_value', self, True, True)
        exceptions.ensure_field('joiner', self, True, True)
        exceptions.ensure_field('execute_permission', self, True, True)

    def verify_split_node(self):
        self.verify_node_has_inbounds()
        self.verify_node_has_outbounds()
        self.verify_node_has_many_branches()
        exceptions.ensure_field('exit_value', self, True, True)
        exceptions.ensure_field('execute_permission', self, True, True)

    def verify_step_node(self):
        self.verify_node_has_inbounds()
        self.verify_node_has_one_outbound()
        self.verify_node_has_no_branches()
        exceptions.ensure_field('exit_value', self, True, True)
        exceptions.ensure_field('joiner', self, True, True)
        exceptions.ensure_field('execute_permission', self, True, True)

    def verify_multiplexer_node(self):
        self.verify_node_has_inbounds()
        self.verify_node_has_many_outbounds()
        self.verify_node_has_no_branches()
        exceptions.ensure_field('exit_value', self, True, True)
        exceptions.ensure_field('joiner', self, True, True)
        exceptions.ensure_field('execute_permission', self, True, True)

    def verify_input_node(self):
        self.verify_node_has_inbounds()
        self.verify_node_has_outbounds()
        self.verify_node_has_no_branches()
        exceptions.ensure_field('exit_value', self, True, True)
        exceptions.ensure_field('joiner', self, True, True)

    def clean(self):
        """
        Validations must be done according to node type. This call will validate the bounds and
          additional fields like the joiner.
        """

        if self.pk:
            if self.type == self.ENTER:
                self.verify_enter_node()
            if self.type in (self.CANCEL, self.JOINED):
                self.verify_isolated_node()
            if self.type == self.EXIT:
                self.verify_exit_node()
            if self.type == self.STEP:
                self.verify_step_node()
            if self.type == self.MULTIPLEXER:
                self.verify_multiplexer_node()
            if self.type == self.INPUT:
                self.verify_input_node()
            if self.type == self.SPLIT:
                self.verify_split_node()

    class Meta:
        verbose_name = _('Node')
        verbose_name_plural = _('Nodes')
        unique_together = (('course_spec', 'code'),)


def valid_origin_types(obj):
    try:
        if obj and NodeSpec.objects.get(pk=obj).type in (NodeSpec.EXIT, NodeSpec.CANCEL, NodeSpec.JOINED):
            raise ValidationError(_('Origin node cannot be of type "exit", "joined" or "cancel"'))
    except NodeSpec.DoesNotExist:
        pass


def valid_destination_types(obj):
    try:
        if obj and NodeSpec.objects.get(pk=obj).type in (NodeSpec.ENTER, NodeSpec.CANCEL, NodeSpec.JOINED):
            raise ValidationError(_('Destination node cannot be of type "enter", "joined" or "cancel"'))
    except NodeSpec.DoesNotExist:
        pass


class TransitionSpec(models.Model):
    """
    Workflow transition.
    """

    origin = models.ForeignKey(NodeSpec, null=False, blank=False, on_delete=models.CASCADE, related_name='outbounds',
                               validators=[valid_origin_types], verbose_name=_('Origin'), help_text=_('Origin node'))
    destination = models.ForeignKey(NodeSpec, null=False, blank=False, on_delete=models.CASCADE,
                                    related_name='inbounds', validators=[valid_destination_types],
                                    verbose_name=_('Destination'), help_text=_('Destination node'))
    # These fields are only allowed for split and input
    action_name = models.SlugField(max_length=30, blank=True, null=True, verbose_name=_('Action Name'),
                                   help_text=_('Action name for this transition. Unique with respect to the origin '
                                               'node. Expected only for split and input nodes'))
    name = models.CharField(max_length=60, null=False, blank=False, verbose_name=_('Name'))
    description = models.TextField(max_length=1023, null=False, blank=True, verbose_name=_('Description'))
    # These fields are only allowed for input
    permission = models.CharField(max_length=201, blank=True, null=True, verbose_name=_('Permission'),
                                  help_text=_('Permission code (as <application>.<permission>) to test against. It is '
                                              'not required, but only allowed if coming from an input node'))
    # These fields are only allowed for multiplexer
    condition = fields.CallableReferenceField(blank=True, null=True, verbose_name=_('Condition'),
                                              help_text=_('A callable evaluating the condition. Expected only for '
                                                          'multiplexer nodes. The condition will evaluate with '
                                                          'signature (document, user) and will return a value that '
                                                          'will be treated as boolean.'))
    priority = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('Priority'),
                                                help_text=_('A priority value used to order evaluation of condition. '
                                                            'Expected only for multiplexer nodes'))

    def verify_consistency(self):
        exceptions.ensure(lambda obj: obj.origin.course_spec == obj.destination.course_spec, self,
                          _('Connected nodes by a transition must belong to the same course'),
                          exceptions.WorkflowCourseTransitionInconsistent)

    def verify_unique_priority(self):
        if self.origin.outbounds.exclude(pk=self.pk).filter(priority=self.priority).exists():
            raise exceptions.WorkflowCourseTransitionPriorityNotUnique(
                self, {'priority': [_('This field must be unique among transitions in multiplexer nodes.')]}
            )

    def verify_unique_action_name(self):
        if self.origin.outbounds.exclude(pk=self.pk).filter(action_name=self.action_name).exists():
            raise exceptions.WorkflowCourseTransitionActionNameNotUnique(
                self, {'action_name': [_('This field must be unique among transitions in multiplexer nodes.')]}
            )

    def verify_enter_origin(self):
        exceptions.ensure_field('condition', self, True, True)
        exceptions.ensure_field('priority', self, True, True)
        exceptions.ensure_field('action_name', self, True, True)
        # permission is allowed here, but not required

    def verify_split_origin(self):
        exceptions.ensure_field('condition', self, True, True)
        exceptions.ensure_field('priority', self, True, True)
        exceptions.ensure_field('action_name', self)
        exceptions.ensure_field('permission', self, True, True)
        self.verify_unique_action_name()

    def verify_step_origin(self):
        exceptions.ensure_field('condition', self, True, True)
        exceptions.ensure_field('priority', self, True, True)
        exceptions.ensure_field('action_name', self, True, True)
        exceptions.ensure_field('permission', self, True, True)

    def verify_multiplexer_origin(self):
        exceptions.ensure_field('condition', self)
        exceptions.ensure_field('priority', self, False, None)
        exceptions.ensure_field('action_name', self, True, True)
        exceptions.ensure_field('permission', self, True, True)
        self.verify_unique_priority()

    def verify_input_origin(self):
        exceptions.ensure_field('condition', self, True, True)
        exceptions.ensure_field('priority', self, True, True)
        exceptions.ensure_field('action_name', self)
        # permission is allowed here, but not required
        self.verify_unique_action_name()

    def clean(self):
        """
        Transitions must validate:
        - origin and destination must have the same action course.
        - condition and priority must be present for multiplexer origin, but absent for any other origin.
        - action_name must be present for input and split origins, but absent for any other origin.
        - action_name must be unique for given origin for input and split origins.
        - permission can be present only for input and split origins.
        - priority must be unique for given origin for multiplexer nodes.
        """

        self.verify_consistency()
        if self.pk:
            if self.origin.type == NodeSpec.ENTER:
                self.verify_enter_origin()
            if self.origin.type == NodeSpec.STEP:
                self.verify_step_origin()
            if self.origin.type == NodeSpec.MULTIPLEXER:
                self.verify_multiplexer_origin()
            if self.origin.type == NodeSpec.INPUT:
                self.verify_input_origin()
            if self.origin.type == NodeSpec.SPLIT:
                self.verify_split_origin()

    class Meta:
        verbose_name = _('Transition Spec')
        verbose_name_plural = _('Transition Specs')


####################################################
# Workflow instances from here
####################################################


class WorkflowInstance(TrackedLive):

    workflow_spec = models.ForeignKey(WorkflowSpec, blank=False, null=False, on_delete=models.CASCADE,
                                      related_name='instances')
    content_type = models.ForeignKey(ContentType, blank=False, null=False, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(blank=False, null=False)
    document = GenericForeignKey('content_type', 'object_id')

    def verify_accepts_document(self):
        try:
            if self.content_type != self.workflow_spec.document_type:
                raise exceptions.WorkflowInstanceDoesNotAcceptDocument(
                    self, _('Workflow instances must reference documents with expected class in their workflow. '
                            'Current: %(current)s. Expected: %(expected)s') % {
                        'current': self.content_type.model_class().__name__,
                        'expected': self.workflow_spec.document_type.model_class().__name__
                    })
        except ObjectDoesNotExist:
            pass

    def verify_exactly_one_parent_course(self):
        try:
            self.courses.get(parent__isnull=True)
        except CourseInstance.DoesNotExist:
            raise exceptions.WorkflowInstanceHasNoMainCourse(self, _('No main course is present for the workflow '
                                                                     'instance (expected one)'))
        except CourseInstance.MultipleObjectsReturned:
            raise exceptions.WorkflowInstanceHasNoMainCourse(self, _('Multiple main courses are present for the '
                                                                     'workflow instance (expected one)'))

    def clean(self, keep=True):
        """
        content_type must match workflow's expected content_type
        """

        self.verify_accepts_document()
        if self.pk:
            self.verify_exactly_one_parent_course()

    class Meta:
        unique_together = ('content_type', 'object_id')
        verbose_name = _('Workflow Instance')
        verbose_name_plural = _('Workflow Instances')


class CourseInstance(TrackedLive):
    """
    An instance of a course, referencing an instance of a workflow.

    The related course and workflow instance must be consistent on referencing
      the same workflow.
    """

    workflow_instance = models.ForeignKey(WorkflowInstance, related_name='courses', null=False, blank=False,
                                          on_delete=models.CASCADE)
    parent = models.ForeignKey('NodeInstance', related_name='branches', null=True, blank=True, on_delete=models.CASCADE)
    course_spec = models.ForeignKey(CourseSpec, null=False, blank=False, on_delete=models.CASCADE)
    term_level = models.PositiveIntegerField(null=True, blank=True)

    def verify_consistency(self):
        exceptions.ensure(lambda obj: obj.course_spec.workflow_spec != obj.workflow_instance.workflow_spec, self,
                          _('Referenced course and instance do not refer the same workflow'),
                          exceptions.WorkflowCourseInstanceInconsistent)
        exceptions.ensure(lambda obj: obj.parent and obj.parent.course_instance.course_spec not in self.course_spec.callers.all(),
                          self, _('Referenced course and parent node instance\'s course are not the same'),
                          exceptions.WorkflowCourseInstanceInconsistent)
        try:
            self.node_instance.verify_consistent_course()
        except ObjectDoesNotExist:
            pass

    def clean(self):
        """
        Cleans consistency
        """

        self.verify_consistency()


class NodeInstance(TrackedLive):
    """
    An instance of a node, referencing an instance of a course..

    The related node and course instance must be consistent on referencing the
      same course. The related branches must also be consistent.
    """

    course_instance = models.OneToOneField(CourseInstance, related_name='node_instance', null=False, blank=False)
    node_spec = models.ForeignKey(NodeSpec, related_name='+', null=False, blank=False)

    def verify_consistency(self):
        exceptions.ensure(lambda obj: obj.node_spec.course_spec != obj.course_instance.course_spec, self,
                          _('Referenced node and course instance do not refer the same course'),
                          exceptions.WorkflowCourseNodeInstanceInconsistent)

    def verify_respects_branches(self):
        """
        When the node is a SPLIT node, we must ensure every branch is instantiated.
        """

        if self.node_spec.type == NodeSpec.SPLIT:
            spec_branches = set(self.node_spec.branches.all().values_list('code', flat=True))
            instance_branches = set(self.branches.all().values_list('course_spec__code', flat=True))
            if spec_branches != instance_branches:
                raise exceptions.WorkflowCourseNodeInstanceIncompleteSplitBranchReferences(
                    self, _('This split node does not have children biunivocally referencing the branches '
                            'in the split node spec')
                )
        else:
            if self.branches.exists():
                raise exceptions.WorkflowCourseNodeInstanceNonSplitAndHasBranches(
                    self, _('This node instance is not a split node. It must not instantiate any branch')
                )

    def clean(self, keep=False):
        """
        Cleans consistency
        """

        self.verify_consistent_course()
        self.verify_respects_branches()


class CourseInstanceLog(models.Model):
    """
    This class is not intended to be used directly but just be present in the database.
    """

    created_on = models.DateTimeField(auto_now_add=True, null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False, on_delete=models.CASCADE)
    course_instance = models.ForeignKey(CourseInstance, null=False, blank=False, on_delete=models.CASCADE,
                                        related_name='logs')
    node_spec = models.ForeignKey(NodeSpec, related_name='+', null=False, blank=False)
