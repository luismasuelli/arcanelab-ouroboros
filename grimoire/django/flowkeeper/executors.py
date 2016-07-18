###################################################################################
#                                                                                 #
# Workflow logic will be coded here, just to get rid of dirty code in the models. #
#                                                                                 #
###################################################################################

from __future__ import unicode_literals
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _
from django.utils.six import string_types
from django.contrib.contenttypes.models import ContentType
from cantrips.iteration import iterable, items
from . import exceptions, models

class Workflow(object):

    class PermissionsChecker(object):
        """
        Permissions checks raise different subclasses of PermissionDenied.

        These checks are all performed against the associated document (since
          each workflow instance must be tied to a specific model or, say, document,
          these points can be addressed easily).
        """

        @classmethod
        def can_instantiate_workflow(cls, workflow_instance, user):
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

        @classmethod
        def can_cancel_course(cls, course_instance, user):
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

        @classmethod
        def can_advance_course(cls, course_instance, transition, user):
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
        def get_exit_code(cls, course_instance):
            """
            Gets the exit code from a given course instance.
            :param course_instance: The course instance to get the exit code from.
            :return: None for non-terminated courses. -1 for joined and cancelled courses, and a non-negative
              integer for courses reaching an exit node (actually, the exit_value field of the reached exit node).
            """

            if not cls.is_terminated(course_instance):
                return None
            if cls.is_joined(course_instance) or cls.is_cancelled(course_instance):
                return -1
            return course_instance.node_instance.node_spec.exit_value

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
                return exceptions.WorkflowCourseInstanceDoesNotExist(
                    course_instance, _('Course does not have children')
                )
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

    class WorkflowRunner(object):

        @classmethod
        def _move(cls, course_instance, node, user):
            """
            Moves the course to a new node. Checks existence (if node code specified) or consistency
              (if node instance specified).
            :param course_instance: The course instance to move.
            :param node: The node instance or code to move this course instance.
            :param user: The user invoking the action that caused this movement.
            """

            if isinstance(node, string_types):
                try:
                    node_spec = course_instance.course_spec.node_specs.get(code=node)
                except models.NodeSpec.DoesNotExist:
                    raise exceptions.WorkflowCourseNodeDoesNotExist(course_instance, node)
            else:
                if node.course != course_instance.course_spec:
                    raise exceptions.WorkflowCourseInstanceDoesNotAllowForeignNodes(course_instance, node)
                node_spec = node

            # We run validations on node_spec.
            node_spec.clean()

            # Now we must run the callable, if any.
            handler = node_spec.landing_handler
            if handler:
                handler(course_instance.workflow_instance.document, user)

            # Nodes of type INPUT, EXIT, SPLIT, JOINED and CANCEL are not intermediate execution nodes but
            #   they end the advancement of a course (EXIT, JOINED and CANCEL do that permanently, while
            #   INPUT and SPLIT will continue by running other respective workflow calls).
            #
            # Nodes of type ENTER, MULTIPLEXER, and STEP are temporary and so they should not be saved like that.
            if node_spec.type in (models.NodeSpec.INPUT, models.NodeSpec.SPLIT, models.NodeSpec.EXIT,
                                  models.NodeSpec.CANCEL, models.NodeSpec.JOINED):
                try:
                    course_instance.node_instance.delete()
                except models.NodeInstance.DoesNotExist:
                    pass
                node_instance = models.NodeInstance.objects.create(course_instance=course_instance, node_spec=node_spec)
                # For split nodes, we also need to create the pending courses as branches.
                if node_spec.type == models.NodeSpec.SPLIT:
                    for branch in node_spec.branches.all():
                        node_instance.branches.create(workflow_instance=course_instance.workflow_instance,
                                                      course_spec=branch)

        @classmethod
        def _cancel(cls, course_instance, user, level=0):
            """
            Moves the course recursively (if this course has children) to a cancel node.
              For more information see the _move method in this class.
            :param course_instance: The course instance being cancelled.
            :param user: The user invoking the action leading to this call.
            :param level: The cancellation level. Not directly useful except as information for the
              user, later in the database.
            :return:
            """

            if Workflow.CourseHelpers.is_terminated(course_instance):
                return
            node_spec = course_instance.course_spec.verify_has_cancel_node()
            course_instance.clean()
            if Workflow.CourseHelpers.is_splitting(course_instance):
                next_level = level + 1
                for branch in course_instance.node_instance.branches.all():
                    cls._cancel(branch, user, next_level)
            cls._move(course_instance, node_spec, user)
            course_instance.term_level = level
            course_instance.save()

        @classmethod
        def _join(cls, course_instance, user, level=0):
            """
            Moves the course recursively (if this course has children) to a joined node.
              For more information see the _move method in this class.
            :param course_instance: The course instance being joined.
            :param user: The user invoking the action leading to this call.
            :param level: The joining level. Not directly useful except as information for the
              user, later in the database.
            :return:
            """

            if Workflow.CourseHelpers.is_terminated(course_instance):
                return
            node_spec = course_instance.course_spec.verify_has_joined_node()
            if not node_spec:
                raise exceptions.WorkflowCourseInstanceNotJoinable(course_instance, _('This course is not joinable'))
            course_instance.clean()
            if Workflow.CourseHelpers.is_splitting(course_instance):
                next_level = level + 1
                for branch in course_instance.node_instance.branches.all():
                    cls._join(branch, user, next_level)
            cls._move(course_instance, node_spec, user)
            course_instance.term_level = level
            course_instance.save()

        @classmethod
        def _run_transition(cls, course_instance, transition, user):
            """
            Runs a transition in a course instance. Many things are ensured already:
            - The course has a valid origin (one which can have outbounds).
            - The transition's origin is the course instance's current node instance's
              node spec.
            :param course_instance: The course instance to run the transition on.
            :param transition: The transition to execute.
            :param user: The user trying to run by this transition.
            :return:
            """

            ####
            # course_instance and transition are already clean by this point
            ####

            # Obtain and validate elements to interact with
            origin = transition.origin
            origin.clean()
            destination = transition.destination
            destination.clean()
            course_spec = course_instance.course_spec
            course_spec.clean()

            # Check if we have permission to do this
            Workflow.PermissionsChecker.can_advance_course(course_instance, transition, user)

            # We move to the destination node
            cls._move(course_instance, destination, user)

            # We must see what happens next.
            # ENTER, CANCEL and JOINED types are not valid destination types.
            # INPUT, SPLIT are types which expect user interaction and will not
            #   continue the execution.
            # While...
            #   STEP nodes will continue the execution from the only transition they have.
            #   EXIT nodes MAY continue the execution by exciting a parent joiner or completing
            #     parallel branches (if the parent SPLIT has no joiner and only one outbound).
            #   MULTIPLEXER nodes will continue from a picked transition, depending on which
            #     one satisfies the condition. It will be an error if no transition satisfies
            #     the multiplexer condition.
            if destination.type == models.NodeSpec.EXIT:
                if course_instance.parent:
                    course_instance.parent.clean()
                    parent_course_instance = course_instance.parent.course_instance
                    parent_course_instance.clean()
                    cls._test_split_branch_reached(parent_course_instance, user, course_instance)
            elif destination.type == models.NodeSpec.STEP:
                # After cleaning destination, we know that it has exactly one outbound.
                transition = destination.outbounds.get()
                # Clean the transition.
                transition.clean()
                # Run the transition.
                cls._run_transition(course_instance, transition, user)
            elif destination.type == models.NodeSpec.MULTIPLEXER:
                # After cleaning destination, we know that it has more than one outbound.
                transitions = list(destination.outbounds.order('priority').all())
                # Clean all the transitions.
                for transition in transitions:
                    transition.clean()
                # Evaluate the conditions and take the transition satisfying the first.
                # If no transition is picked, an error is thrown.
                for transition in transitions:
                    condition = transition.condition
                    # Condition will be set since we cleaned the transition.
                    if condition(course_instance.workflow_instance.document, user):
                        cls._run_transition(course_instance, transition, user)
                        break
                else:
                    raise exceptions.WorkflowCourseNodeMultiplexerDidNotSatisfyAnyCondition(
                        destination, _('No condition was satisfied when traversing a multiplexer node')
                    )

        @classmethod
        def _test_split_branch_reached(cls, course_instance, user, reaching_branch):
            """
            Decides on a parent course instance what to do when a child branch has reached and end.
            :param course_instance: The parent course instance being evaluated. This instance will have
              a node instance referencing a SPLIT node.
            :param user: The user causing this action by running a transition or cancelling a course.
            :param reaching_branch: The branch reaching this end. It will be a branch of the
              `course_instance` argument.
            :return:
            """

            # We validate the SPLIT node spec
            node_spec = course_instance.node_instance.node_spec
            node_spec.clean()
            joiner = node_spec.joiner
            branches = course_instance.branches.all()
            if not joiner:
                # By cleaning we know we will be handling only one transition
                transition = node_spec.outbounds.get()
                transition.clean()
                # If any branch is not terminated, then we do nothing.
                # Otherwise we will execute the transition.
                if all(Workflow.CourseHelpers.is_terminated(branch) for branch in branches):
                    cls._run_transition(course_instance, transition, user)
            else:
                # By cleaning we know we will be handling many transitions
                transitions = node_spec.outbounds.all()
                # We call the joiner with its arguments
                reaching_branch_code = reaching_branch.code
                # Making a dictionary of branch statuses
                branch_statuses = {branch.course_spec.code: Workflow.CourseHelpers.get_exit_code(branch)
                                   for branch in branches}
                # Execute the joiner with (document, branch statuses, and current branch being joined) and
                #   get the return value.
                returned = joiner(course_instance.workflow_instance.document, branch_statuses, reaching_branch_code)
                if returned is None:
                    # If all the branches have ended (i.e. they have non-None values), this
                    #   is an error.
                    # Otherwise, we do nothing.
                    if all(bool(status) for status in branch_statuses.values()):
                        raise exceptions.WorkflowCourseNodeNoTransitionResolvedAfterCompleteSplitJoin(
                            node_spec, _('The joiner callable returned None -not deciding any action- but '
                                         'all the branches have terminated')
                        )
                elif isinstance(returned, string_types):
                    # The transitions will have unique and present action codes.
                    # We validate they have unique codes and all codes are present.
                    # IF the count of distinct action_names is not the same as the count
                    #   of transitions, this means that either some transitions do not
                    #   have action name, or have a repeated one.
                    count = transitions.count()
                    transition_codes = {transition.action_name for transition in transitions if transition.action_name}
                    if len(transition_codes) != count:
                        raise exceptions.WorkflowCourseNodeBadTransitionActionNamesAfterSplitNode(
                            node_spec, _('Split node transitions must all have a unique action name')
                        )
                    try:
                        # We get the transition by its code.
                        transition = transitions.get(action_name=returned)
                    except models.TransitionSpec.DoesNotExist:
                        raise exceptions.WorkflowCourseNodeTransitionDoesNotExist(node_spec, returned)
                    # We clean the transition
                    transition.clean()
                    # We force a join in any non-terminated branch (i.e. status in None)
                    for code, status in items(branch_statuses):
                        if status is None:
                            cls._join(branches.get(course_spec__code=code), user)
                    # And THEN we execute our picked transition
                    cls._run_transition(course_instance, transition, user)
                else:
                    # Invalid joiner return value type
                    raise exceptions.WorkflowCourseNodeInvalidSplitResolutionCode(
                        node_spec, _('Invalid joiner resolution code type. Expected string or None'), returned
                    )

    def __init__(self, workflow_instance):
        """
        In the end, this whole class is just a Wrapper of a workflow instance,
          and provides all the related methods.
        :param workflow_instance: Instance being wrapped.
        """

        workflow_instance.clean()
        self._instance = workflow_instance

    @property
    def instance(self):
        return self._instance

    @classmethod
    def get(cls, document):
        """
        Gets an existent workflow for a given document.
        :param document:
        :return:
        """

        content_type = ContentType.objects.get_for_model(type(document))
        object_id = document.id
        try:
            return cls(models.WorkflowInstance.objects.get(content_type=content_type, object_id=object_id))
        except models.WorkflowInstance.DoesNotExist:
            raise exceptions.WorkflowInstanceDoesNotExist(
                None, _('No workflow instance exists for given document'), document
            )

    @classmethod
    def create(cls, user, workflow_spec, document):
        """
        Tries to create a workflow instance with this workflow spec, the document, and
          on behalf of the specified user.
        :param user: The user requesting this action. Permission will be checked for him
          against the document.
        :param workflow_spec: The workflow spec to be tied to.
        :param document: The document to associate.
        :return: A wrapper for the newly created instance.
        """

        with atomic():
            workflow_spec.clean()
            workflow_instance = models.WorkflowInstance(workflow_spec=workflow_spec, document=document)
            cls.PermissionsChecker.can_instantiate_workflow(workflow_instance, user)
            workflow_instance.full_clean()
            workflow_instance.save()
            workflow_instance.courses.create(course_spec=workflow_spec.course_specs.get(depth=0))
            return cls(workflow_instance)

    def start(self, user, path=''):
        """
        Starts the workflow by its main course, or searches a course and starts it.
        :param user: The user starting the course or workflow.
        :param path: Optional path to a course in this instance.
        :return:
        """

        with atomic():
            course_instance = self.CourseHelpers.find_course(self.instance.courses.get(parent__isnull=True), path)
            if self.CourseHelpers.is_pending(course_instance):
                course_instance.clean()
                course_instance.course_spec.clean()
                # Get the enter node (after clean, we are sure there will be an enter node on the spec)
                enter_node = course_instance.course_spec.node_specs.get(type=models.NodeSpec.ENTER)
                self.WorkflowRunner._move(course_instance, enter_node, user)
                # The enter_node was alreeady cleaned by the last call. We can proceed with the only outbound.
                transition = enter_node.outbounds.get()
                transition.clean()
                # Now we execute the transition with our private runner.
                self.WorkflowRunner._run_transition(course_instance, transition, user)
            else:
                raise exceptions.WorkflowCourseInstanceNotPending(
                    course_instance, _('The specified course instance cannot be started because it is not pending')
                )

    def execute(self, user, action_name, path=''):
        """
        Executes an action in the workflow by its main course, or searches a course and executes an action on it.
        :param user: The user executing an action in the course or workflow.
        :param action_name: The name of the action (transition) to execute.
        :param path: Optional path to a course in this instance.
        :return:
        """

        with atomic():
            course_instance = self.CourseHelpers.find_course(self.instance.courses.get(parent__isnull=True), path)
            if self.CourseHelpers.is_waiting(course_instance):
                course_instance.clean()
                course_instance.course_spec.clean()
                node_spec = course_instance.node_instance.node_spec
                node_spec.clean()
                transitions = node_spec.outbounds.all()
                # The transitions will have unique and present action codes.
                # We validate they have unique codes and all codes are present.
                # IF the count of distinct action_names is not the same as the count
                #   of transitions, this means that either some transitions do not
                #   have action name, or have a repeated one.
                count = transitions.count()
                transition_codes = {transition.action_name for transition in transitions if transition.action_name}
                if len(transition_codes) != count:
                    raise exceptions.WorkflowCourseNodeBadTransitionActionNamesForInputNode(
                        node_spec, _('Input node transitions must all have a unique action name')
                    )
                # We get the transition or fail with non-existence
                try:
                    transition = transitions.get(action_name)
                except models.TransitionSpec.DoesNotExist:
                    raise exceptions.WorkflowCourseNodeTransitionDoesNotExist(node_spec, action_name)
                # We clean the transition
                transition.clean()
                # And THEN we execute our picked transition
                self.WorkflowRunner._run_transition(course_instance, transition, user)
            else:
                raise exceptions.WorkflowCourseInstanceNotWaiting(
                    course_instance, _('No action can be executed in the specified course instance because it is not '
                                       'waiting for an action to be taken')
                )

    def cancel(self, user, path=''):
        """
        Cancels a workflow entirely (by its main course), or searches a course and cancels it.
        :param user: The user cancelling the course or workflow.
        :param path: Optional path to a course in this instance.
        :return:
        """

        with atomic():
            course_instance = self.CourseHelpers.find_course(self.instance.courses.get(parent__isnull=True), path)
            if self.CourseHelpers.is_terminated(course_instance):
                raise exceptions.WorkflowCourseInstanceAlreadyTerminated(
                    course_instance, _('Cannot cancel this instance because it is already terminated')
                )
            # Check permission on workflow AND on course.
            course_instance.clean()
            course_instance.course_spec.clean()
            self.PermissionsChecker.can_cancel_course(course_instance, user)
            # Cancel (recursively).
            self.WorkflowRunner._cancel(course_instance, user)
            # Trigger the parent joiner, if any.
            if course_instance.parent:
                course_instance.parent.clean()
                parent_course_instance = course_instance.parent.course_instance
                parent_course_instance.clean()
                self.WorkflowRunner._test_split_branch_reached(parent_course_instance, user, course_instance)

    def get_available_actions(self):
        """
        Get all the available actions for the courses in this workflow. For nodes
        :return: A dictionary with 'course.path' => (
            'pending' | 'splitting' | 'cancelled' | 'ended' | ['list', 'of', 'available', 'actions']
        )
        """

        self.instance.clean()
        course_instance = self.instance.courses.get(parent__isnull=True)
        result = {}

        def traverse_actions(course_instance, path=''):
            course_instance.clean()
            if self.CourseHelpers.is_splitting(course_instance):
                # Splits do not have available actions on their own.
                # They can only continue traversal on their children
                #   branches.
                code = course_instance.course_spec.code
                result[path] = 'splitting'
                new_path = code if not path else "%s.%s" % (path, code)
                for branch in course_instance.node_instance.branches.all():
                    traverse_actions(branch, new_path)
            elif self.CourseHelpers.is_pending(course_instance):
                # Marking path => 'pending' means that the course is not even
                #   started yet, but it is available to be started.
                result[path] = 'pending'
            elif self.CourseHelpers.is_waiting(course_instance):
                # Waiting courses will enumerate actions by their transitions.
                result[path] = list(course_instance.node_instance.outbounds.all().values_list('action_name', flat=True))
            elif self.CourseHelpers.is_cancelled(course_instance):
                result[path] = 'cancelled'
            elif self.CourseHelpers.is_ended(course_instance):
                result[path] = 'ended'
            # NOTES: joined courses will NEVER be listed since they exist for
            #   just a moment.

        traverse_actions(course_instance)
        return result
