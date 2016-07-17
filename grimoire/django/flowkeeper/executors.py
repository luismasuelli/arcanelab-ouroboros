###################################################################################
#                                                                                 #
# Workflow logic will be coded here, just to get rid of dirty code in the models. #
#                                                                                 #
###################################################################################

from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from cantrips.iteration import iterable
from . import exceptions, models

class Workflow(object):

    class PermissionsChecker(object):
        """
        Permissions checks raise different subclasses of PermissionDenied.

        These checks are all performed against the associated document (since
          each workflow instance must be tied to a specific model or, say, document,
          these points can be addressed easily).
        """

        def can_instantiate_workflow(self, workflow_instance, user):
            """
            Verifies the user can create a workflow instance, given the instance and user.
            :param workflow_instance: The instance to check (will be already valid).
            :param user: The user to check
            :return: nothing
            """

            permission = workflow_instance.workflow_spec.create_permission
            document = workflow_instance.document
            if permission and not user.has_perm(permission, document):
                raise exceptions.WorkflowCreateDenied(workflow_instance)

        def can_cancel_course(self, course_instance, user):
            """
            Verifies the user can cancel a course instance, given the instance and user.
            Both the workflow permission AND the course permission, if any, must be
              satisfied by the user.
            :param course_instance: The instance to check (will be already valid).
            :param user: The user to check
            :return: nothing
            """

            wf_permission = course_instance.course_spec.workflow_spec.cancel_permission
            cs_permission = course_instance.course_spec.cancel_permission
            document = course_instance.workflow_instance.document
            if wf_permission and not user.has_perm(wf_permission, document):
                raise exceptions.WorkflowCourseCancelDeniedByWorkflow(course_instance)
            if cs_permission and not user.has_perm(cs_permission, document):
                raise exceptions.WorkflowCourseCancelDeniedByCourse(course_instance)

        def can_advance_course(self, course_instance, transition, user):
            """
            Verifies the user can advance a course instance, given the instance and user.
            This check involves several cases:
            - The course instance is started and waiting on an Input node: the user
              satisfies the node's permission (if any) and the transition's permission
              (if any).
            - The course instance is starting and trying to execute the only transition
              from the only starting node: the user satisfies the transition's permission
              (if any).
            - The user is standing on a different node (not ENTER, not INPUT): this is
              always a failure. There will never be an allowance in this point.

            This method will be called when an explicit call to start or advance a
              workflow is performed. This means that multiplexer nodes or step nodes
              which are hit as intermediate steps of an execution will not call this
              method for their transitions.
            """

            document = course_instance.course_spec.workflow_spec
            try:
                node_instance = course_instance.node_instance
                # Reached this point, the node is either INPUT or a type we should not
                #   allow.
                if node_instance.node_spec.type != models.NodeSpec.INPUT:
                    raise exceptions.WorkflowCourseAdvanceDeniedByWrongNodeType(course_instance)
                else:
                    node_permission = node_instance.node_spec.execute_permission
                    if node_permission and not user.has_perm(node_permission, document):
                        raise exceptions.WorkflowCourseAdvanceDeniedByNode(course_instance)
                    transition_permission = transition.permission
                    if transition_permission and not user.has_perm(transition_permission, document):
                        raise exceptions.WorkflowCourseAdvanceDeniedByTransition(course_instance)
            except models.NodeInstance.DoesNotExist:
                # Reached this point, the workflow course was pending. It seems it is starting.
                # Right now the transition is the first transition, which has an ENTER node as its origin.
                transition_permission = transition.permission
                if transition_permission and not user.has_perm(transition_permission, document):
                    raise exceptions.WorkflowCourseAdvanceDeniedByTransition(course_instance)

    class CourseHelpers(object):
        """
        Helpers to get information from a course (instance or spec).
        """

        @classmethod
        def _check_status(cls, course_instance, types, invert=False):
            """
            Checks whether the instance's current node has a specific type or list of types.
              The condition can be inverted to see whether the instance's current node does
              not have that/those type(s). If the node does not exist, this method returns
              False. If the node does not exist AND the condition is requested to be inverted,
              this method returns True.
            :param course_instance: Instance to ask for.
            :param types: Node type or iterable with Node types to ask for.
            :param invert: Whether this condition is inverted or not.
            :return: Boolean indicating whether the course instance's node's type is among the
              given types.
            """

            try:
                return (course_instance.node_instance.node.type in iterable(types)) ^ bool(invert)
            except models.NodeInstance.DoesNotExist:
                return bool(invert)

        @classmethod
        def is_pending(cls, course_instance):
            return cls._check_status(course_instance, (), True)

        @classmethod
        def is_waiting(cls, course_instance):
            return cls._check_status(course_instance, models.NodeSpec.INPUT)

        @classmethod
        def is_cancelled(cls, course_instance):
            return cls._check_status(course_instance, models.NodeSpec.CANCEL)

        @classmethod
        def is_ended(cls, course_instance):
            return cls._check_status(course_instance, models.NodeSpec.EXIT)

        @classmethod
        def is_splitting(cls, course_instance):
            return cls._check_status(course_instance, models.NodeSpec.SPLIT)

        @classmethod
        def is_joined(cls, course_instance):
            return cls._check_status(course_instance, models.NodeSpec.JOINED)

        @classmethod
        def is_terminated(cls, course_instance):
            return cls._check_status(course_instance, (models.NodeSpec.JOINED, models.NodeSpec.EXIT,
                                                       models.NodeSpec.CANCEL))

        @classmethod
        def find_course(cls, course_instance, path):
            """
            Finds a specific course instance given a starting course instance and traversing the tree. The path
              will be broken by separating dot and the descendants will be searched until one course instance is
              found as described (by course codes) or an exception telling no element was found (or no element
              can be found) is triggered.
            :param course_instance: The course instance to check.
            :param path: The path to check under the course instance.
            :return: A descendant, or the same given, course instance.
            """

            if path == '':
                return course_instance
            elif not cls.is_splitting(course_instance):
                return exceptions.WorkflowNoSuchElement(course_instance, _('Course does not have children'))
            else:
                course_instance.verify_consistent_course()
                parts = path.split('.', 1)
                if len(parts) == 1:
                    head, tail = parts[0], ''
                else:
                    head, tail = parts
                try:
                    return cls.find_course(course_instance.node.branches.get(course__code=head), tail)
                except models.NodeInstance.DoesNotExist:
                    raise exceptions.WorkflowNoSuchElement(course_instance, _('Children course does not exist'), head)
                except models.NodeInstance.MultipleObjectsReturned:
                    raise exceptions.WorkflowNoSuchElement(course_instance, _('Multiple children courses exist '
                                                                              'with course code in path'), head)

    class WorkflowHelpers(object):
        """
        Helpers to get information from a node (instance or spec).
        """

        @classmethod
        def find_course(cls, workflow_instance, path):
            """
            Finds a specific course instance given a target workflow instance and traversing the tree. The path
              will be broken by separating dot and the descendants will be searched until one course instance is
              found as described (by course codes) or an exception telling no element was found (or no element
              can be found) is triggered.
            :param workflow_instance: The workflow instance to query.
            :param path: The path to check under the course instance.
            :return: A descendant, or the first (root), course instance.
            """

            workflow_instance.verify_exactly_one_parent_course()
            return Workflow.CourseHelpers.find_course(workflow_instance.courses.get(parent__isnull=True), path)
