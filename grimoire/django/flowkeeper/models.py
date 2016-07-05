from __future__ import unicode_literals
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from .fields import CallableReferenceField


def valid_document_type(value):
    if value and not issubclass(value.model_class(), Document):
        raise ValidationError(_('The `document_type` field must reference a subclass of Document'))


class Document(models.Model):
    """
    Base class for any model accepting a workflow
    """

    class Meta:
        abstract = True


class CodeManager(models.Manager):

    def get_by_natural_key(self, code):
        return self.get(code=code)


class Workflow(models.Model):
    """
    Workflow class. Defines itself, and the document type it can associate to.
    """

    document_type = models.ForeignKey(ContentType, null=False, blank=False, on_delete=models.CASCADE,
                                      validators=[valid_document_type], verbose_name=_('Document Type'),
                                      help_text=_('Accepted related document class'))
    code = models.SlugField(max_length=20, null=False, blank=False, unique=True, verbose_name=_('Code'),
                            help_text=_('Internal (unique) code'))
    name = models.CharField(max_length=60, null=False, blank=False, verbose_name=_('Name'))
    description = models.CharField(max_length=100, null=False, blank=False, verbose_name=_('Description'))
    permission = models.CharField(max_length=201, blank=True, null=True, verbose_name=_('Permission'),
                                  help_text=_('Permission code (as <application>.<permission>) to test against. The '
                                              'user who intends to create a workflow instance must satisfy this '
                                              'permission.'))
    objects = CodeManager()

    def natural_key(self):
        return self.code

    def clean(self):
        """
        TODO a workflow must validate by having:
        - Exactly one parent Course.
        """

        if self.pk:
            if not self.courses.filter(depth=0).exists():
                raise ValidationError(_('Workflows must have at least one parent course'))

    class Meta:
        verbose_name = _('Workflow')
        verbose_name_plural = _('Workflows')


class Course(models.Model):
    """
    Workflow action course.
    """

    workflow = models.ForeignKey(Workflow, null=False, blank=False, on_delete=models.CASCADE, related_name='courses',
                                 verbose_name=_('Workflow'), help_text=_('Workflow this course belongs to'))
    code = models.SlugField(max_length=20, null=False, blank=False, verbose_name=_('Code'),
                            help_text=_('Internal (unique) code'))
    depth = models.PositiveSmallIntegerField(verbose_name=_('Depth'), null=False, blank=False,
                                             help_text=_('Tells the depth of this course. The main course must be '
                                                         'of depth 0, while successive descendants should increment '
                                                         'the level by 1'))
    permission = models.CharField(max_length=201, blank=True, null=True, verbose_name=_('Permission'),
                                  help_text=_('Permission code (as <application>.<permission>) to test against. The '
                                              'user who intends to start this course must satisfy this permission.'))

    def clean(self):
        """
        A course must validate by having:
        - Exactly one enter node.
        - Exactly one "cancel" exit node.
        - At least one non-"cancel" exit node.
        """

        if self.pk:
            if self.nodes.filter(type=Node.ENTER).count() != 1:
                raise ValidationError(_('A workflow course is expected to have exactly one enter node'))
            if self.nodes.filter(type=Node.CANCEL).count() != 1:
                raise ValidationError(_('A workflow course is expected to have exactly one enter node'))
            if not self.nodes.filter(type=Node.EXIT).exists():
                raise ValidationError(_('A workflow course is expected to have a least one exit node'))

    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        unique_together = (('workflow', 'code'),)


class Node(models.Model):
    """
    Workflow action course node.
    """

    ENTER = 'enter'
    EXIT = 'exit'
    CANCEL = 'cancel'
    INPUT = 'input'
    STEP = 'step'
    MULTIPLEXER = 'multiplexer'
    SPLIT = 'split'

    TYPES = (
        (ENTER, _('Enter')),
        (EXIT, _('Exit')),
        (CANCEL, _('Cancel')),
        (INPUT, _('Input')),
        (STEP, _('Step')),
        (MULTIPLEXER, _('Multiplexed')),
        (SPLIT, _('Split'))
    )

    type = models.CharField(max_length=15, null=False, blank=False, verbose_name=_('Type'), help_text=_('Node type'))
    course = models.ForeignKey(Course, null=False, blank=False, on_delete=models.CASCADE, related_name='nodes',
                               verbose_name=_('Course'), help_text=_('Course this node belongs to'))
    code = models.SlugField(max_length=20, null=False, blank=False, verbose_name=_('Code'),
                            help_text=_('Internal (unique) code'))
    # Exit nodes will have an exit value
    exit_value = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('Exit Value'),
                                                  help_text=_('Exit value. Expected only for exit nodes'))
    # Only for split nodes
    joiner = CallableReferenceField(blank=True, null=True, verbose_name=_('Joiner'),
                                    help_text=_('A callable that will be triggered every time a joined branch '
                                                'reaches an end. The joined branch will trigger this callable '
                                                'also providing the exit value (which is a positive integer, or '
                                                '-1 if the branch was closed due to a cancelation node). This '
                                                'callable must return a valid transition name (existing outbound '
                                                'in this node) to leave the split and take an action, or None to '
                                                'remain in the split and wait for other branches (an exception '
                                                'will be raised if None is returned but no branch is still to '
                                                'finish)'))
    branches = models.ManyToManyField(Course, blank=True, related_name='callers', verbose_name=_('Branches'),
                                      help_text=_('Courses this node branches to. Expected only for split nodes'))

    def clean(self):
        """
        Validations must be done according to node type. This call will validate the bounds and
          additional fields like the joiner.
        """

        if self.pk:
            if self.type == self.ENTER:
                if self.inbounds.exists():
                    raise ValidationError(_('Enter nodes must not have inbound transitions'))
                if self.outbounds.count() != 1:
                    raise ValidationError(_('Enter nodes must have exactly one outbound transition'))
            elif self.type == self.CANCEL:
                if self.inbounds.exists() or self.outbounds.exists():
                    raise ValidationError(_('Cancel nodes must not have any transition'))
            elif self.type == self.EXIT:
                if self.outbounds.exists():
                    raise ValidationError(_('Exit nodes must not have outbound transitions'))
            elif self.type in (self.INPUT, self.MULTIPLEXER, self.SPLIT):
                if self.inbounds.exists() or self.outbounds.exists():
                    raise ValidationError(_('Input nodes must have at least one inbound and one outbound transitions'))
            elif self.type == self.STEP:
                if self.outbounds.count() != 1:
                    raise ValidationError(_('Step nodes must have exactly one outbound transition'))
                if not self.inbounds.exists():
                    raise ValidationError(_('Step nodes must have at least one inbound transition'))
            if self.type == self.SPLIT:
                if self.branches.count() < 2:
                    raise ValidationError(_('Split nodes must have at least two branches'))
                try:
                    if self.branches.exclude(depth=self.course.depth+1).exists():
                        raise ValidationError(_('Split nodes must branch to courses with depth=(depth)+1'))
                    if self.branches.exclude(workflow=self.course.workflow).exists():
                        raise ValidationError(_('Split nodes must branch to courses in the same workflow'))
                except Course.DoesNotExist:
                    pass
            else:
                if self.branches.exists():
                    raise ValidationError(_('Only split nodes can have branches'))

    class Meta:
        verbose_name = _('Node')
        verbose_name_plural = _('Nodes')
        unique_together = (('course', 'code'),)


def valid_origin_types(obj):
    if obj and obj.type not in (Node.EXIT, Node.CANCEL):
        raise ValidationError(_('Origin node cannot be of type "exit" or "cancel"'))


def valid_destination_types(obj):
    if obj and obj.type not in (Node.ENTER, Node.CANCEL):
        raise ValidationError(_('Origin node cannot be of type "enter" or "cancel"'))


class Transition(models.Model):
    """
    Workflow transition.
    """

    origin = models.ForeignKey(Node, null=False, blank=False, on_delete=models.CASCADE, related_name='outbounds',
                               validators=[valid_origin_types], verbose_name=_('Origin'), help_text=_('Origin node'))
    destination = models.ForeignKey(Node, null=False, blank=False, on_delete=models.CASCADE, related_name='inbounds',
                                    validators=[valid_destination_types], verbose_name=_('Destination'),
                                    help_text=_('Destination node'))
    # These fields are only allowed for split and input
    action_name = models.SlugField(max_length=30, blank=True, null=True, verbose_name=_('Action Name'),
                                   help_text=_('Action name for this transition. Unique with respect to the origin '
                                               'node. Expected only for split and input nodes'))
    # These fields are only allowed for input
    permission = models.CharField(max_length=201, blank=True, null=True, verbose_name=_('Permission'),
                                  help_text=_('Permission code (as <application>.<permission>) to test against. It is '
                                              'not required, but only allowed if coming from an input node.'))
    # These fields are only allowed for multiplexer
    condition = CallableReferenceField(blank=True, null=True, verbose_name=_('Condition'),
                                       help_text=_('A callable evaluating the condition. Expected only for '
                                                   'multiplexer nodes'))
    priority = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_('Priority'),
                                                help_text=_('A priority value used to order evaluation of condition. '
                                                            'Expected only for multiplexer nodes'))

    def clean(self):
        """
        Transitions must validate:
        - origin and destination must have the same action course.
        - condition and priority must be present for multiplexer origin, but absent for any other origin.
        - action_name must be present for input and split origins, but absent for any other origin.
        - action_name must be unique for given origin for input and split origins.
        - priority must be unique for given origin for multiplexer nodes.
        """

        try:
            origin = self.origin.course
            destination = self.destination
        except Node.DoesNotExist:
            return

        if origin.course != destination.course:
            raise ValidationError(_('Connected nodes for a transition must belong to the same course'))

        if origin.type == Node.MULTIPLEXER:
            # not null
            if self.condition is None:
                raise ValidationError({'condition': [_('This field cannot be null.')]})
            # not blank
            elif not self.condition:
                raise ValidationError({'condition': [_('This field cannot be blank.')]})
            # not null
            elif self.priority is None:
                raise ValidationError({'priority': [_('This field cannot be null.')]})
            # not blank
            elif not self.priority:
                raise ValidationError({'priority': [_('This field cannot be blank.')]})
            # unique
            elif self.origin.outbounds.exclude(pk=self.pk).filter(priority=self.priority).exists():
                raise ValidationError({'action_name': [_('This field must be unique among transitions in '
                                                         'multiplexer nodes.')]})
        else:
            # null
            if self.condition is not None:
                raise ValidationError({'condition': [_('This field must be null.')]})
            # null
            elif self.priority is not None:
                raise ValidationError({'priority': [_('This field must be null.')]})
        if origin.type in (Node.SPLIT, Node.INPUT):
            # not null
            if self.action_name is None:
                raise ValidationError({'action_name': [_('This field cannot be null.')]})
            # not blank
            elif self.action_name:
                raise ValidationError({'action_name': [_('This field cannot be blank.')]})
            # unique
            elif self.origin.outbounds.exclude(pk=self.pk).filter(action_name=self.action_name).exists():
                raise ValidationError({'action_name': [_('This field must be unique among transitions in '
                                                         'split and input nodes.')]})
        else:
            # null
            if self.action_name is not None:
                raise ValidationError({'action_name': [_('This field must be null.')]})
        if origin.type != Node.INPUT:
            # Null or blank.
            if origin.permission is not None:
                raise ValidationError({'permission': [_('This field must be null.')]})

    class Meta:
        verbose_name = _('Transition')
        verbose_name_plural = _('Transitions')


####################################################
# Workflow instances from here
####################################################


class WorkflowInstance(models.Model):

    workflow = models.ForeignKey(Workflow, blank=False, null=False, on_delete=models.CASCADE, related_name='instances')
    content_type = models.ForeignKey(ContentType, blank=False, null=False, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(blank=False, null=False)
    document = GenericForeignKey('content_type', 'object_id')

    def clean(self):
        """
        content_type must match workflow's expected content_type
        """

        try:
            if self.content_type != self.workflow.document_type:
                raise ValidationError(_('Workflow instances must reference documents with expected class '
                                        'in their workflow. Current: %s. Expected: %s') % (
                    self.content_type.model_class().__name__, self.workflow.document_type.model_class().__name__
                ))
        except ObjectDoesNotExist:
            pass

    class Meta:
        verbose_name = _('Workflow Instance')
        verbose_name_plural = _('Workflow Instances')


# class CourseInstance(models.Model):
#
#     workflow_instance = models.ForeignKey(WorkflowInstance, null=False, blank=False, on_delete=models.CASCADE)
#     parent = models.ForeignKey('NodeInstance', null=False, blank=False, on_delete=models.CASCADE)
#     course = models.ForeignKey(Course, null=False, blank=False, on_delete=models.CASCADE)


# class NodeInstance(models.Model):
#
#     pass
