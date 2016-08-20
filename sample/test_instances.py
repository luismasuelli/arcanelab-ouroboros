from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec, TransitionSpec
from arcanelab.ouroboros.support import CallableReference
from arcanelab.ouroboros import exceptions
from .support import ValidationErrorWrappingTestCase
from .models import Task, Area


class WorkflowInstanceTestCase(ValidationErrorWrappingTestCase):

    def _base_install_workflow_spec(self):
        """
        Installs a dummy workflow, having all the possible nodes in a
          main course, being ok.
        """

        spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec',
                'create_permission': 'sample.create_task',
                'cancel_permission': 'sample.cancel_task',
                'courses': [{
                    'code': '', 'name': 'Main',
                    'nodes': [{
                        'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        'description': 'Origin',
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'created', 'name': 'Created',
                        'description': 'The task was just created at this point. Yet to review',
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'reviewed', 'name': 'Reviewed',
                        'description': 'The task was just reviewed at this point. Yet to be assigned',
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'assigned', 'name': 'Assigned',
                        'description': 'The task was just assigned at this point. Yet to be started',
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'started', 'name': 'Started',
                        'description': 'The task was just started at this point. Yet to be completed',
                    }, {
                        'type': NodeSpec.STEP, 'code': 'completed', 'name': 'Completed',
                        'description': 'The task was completed at this point. Will start post-complete tasks',
                    }, {
                        'type': NodeSpec.SPLIT, 'code': 'invoice-control', 'name': 'Split Invoice/Control',
                        'description': 'Invoicing and Task Control parallel branches',
                        'branches': ['control', 'invoice'], 'joiner': 'sample.support.invoice_control_joiner'
                    }, {
                        'type': NodeSpec.MULTIPLEXER, 'code': 'service-type', 'name': 'Service Type'
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'pending-delivery', 'name': 'Pending Delivery',
                        'description': 'The product is about to be delivered',
                        'landing_handler': 'sample.support.on_pending_delivery'
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'pending-pick', 'name': 'Pending Customer Pick',
                        'description': 'The product is about to be picked',
                    }, {
                        'type': NodeSpec.STEP, 'code': 'notify', 'name': 'Notify',
                    }, {
                        'type': NodeSpec.EXIT, 'code': 'finished', 'name': 'Finished', 'exit_value': 105
                    }, {
                        'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                    }],
                    'transitions': [{
                        'origin': 'origin', 'destination': 'created', 'name': 'Enter Created',
                    }, {
                        'origin': 'created', 'destination': 'reviewed', 'name': 'Review',
                        'permission': 'sample.review_task', 'action_name': 'review'
                    }, {
                        'origin': 'reviewed', 'destination': 'assigned', 'name': 'Assign',
                        'permission': 'sample.create_task', 'action_name': 'assign'
                    }, {
                        'origin': 'assigned', 'destination': 'started', 'name': 'Start',
                        'permission': 'sample.start_task', 'action_name': 'start'
                    }, {
                        'origin': 'started', 'destination': 'completed', 'name': 'Complete',
                        'permission': 'sample.complete_task', 'action_name': 'complete'
                    }, {
                        'origin': 'completed', 'destination': 'invoice-control', 'name': 'Start I/C Split',
                    }, {
                        'origin': 'invoice-control', 'destination': 'started', 'name': 'On Reject',
                        'action_name': 'on-reject'
                    }, {
                        'origin': 'invoice-control', 'destination': 'service-type', 'name': 'On Accept',
                        'action_name': 'on-accept'
                    }, {
                        'origin': 'service-type', 'destination': 'pending-delivery', 'name': 'Is Deliverable?',
                        'priority': 1, 'condition': 'sample.support.is_deliverable'
                    }, {
                        'origin': 'service-type', 'destination': 'pending-pick', 'name': 'Is Non-Deliverable?',
                        'priority': 2, 'condition': 'sample.support.is_non_deliverable'
                    }, {
                        'origin': 'service-type', 'destination': 'notify', 'name': 'Is Service?',
                        'priority': 3, 'condition': 'sample.support.is_service'
                    }, {
                        'origin': 'pending-delivery', 'destination': 'notify', 'name': 'Deliver',
                        'action_name': 'deliver', 'permission': 'sample.deliver_task'
                    }, {
                        'origin': 'pending-pick', 'destination': 'notify', 'name': 'Pick-Attend',
                        'action_name': 'pick-attend', 'permission': 'sample.pick_attend_task'
                    }, {
                        'origin': 'notify', 'destination': 'finished', 'name': 'Finish'
                    }]
                }, {
                    'code': 'control', 'name': 'Control',
                    'nodes': [{
                        'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                    }, {
                        'type': NodeSpec.SPLIT, 'code': 'approve-audit', 'name': 'Split Audit/Approve',
                        'description': 'Audit and Approval parallel branches',
                        'branches': ['approval', 'audit'], 'joiner': 'sample.support.approve_audit_joiner'
                    }, {
                        'type': NodeSpec.EXIT, 'code': 'was-rejected', 'name': 'Was Rejected', 'exit_value': 100,
                    }, {
                        'type': NodeSpec.EXIT, 'code': 'was-satisfied', 'name': 'Was Rejected', 'exit_value': 101,
                    }, {
                        'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                    }, {
                        'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                    }],
                    'transitions': [{
                        'origin': 'origin', 'destination': 'approve-audit', 'name': 'Enter A/E'
                    }, {
                        'origin': 'approve-audit', 'destination': 'was-rejected', 'name': 'Rejected',
                        'action_name': 'rejected'
                    }, {
                        'origin': 'approve-audit', 'destination': 'was-satisfied', 'name': 'Satisfied',
                        'action_name': 'satisfied'
                    }]
                }, {
                    'code': 'approval', 'name': 'Approval',
                    'nodes': [{
                        'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'pending-approval', 'name': 'Pending Approval',
                        'description': 'The task is about to be approved or rejected',
                    }, {
                        'type': NodeSpec.EXIT, 'code': 'approved', 'name': 'Approved', 'exit_value': 101,
                    }, {
                        'type': NodeSpec.EXIT, 'code': 'rejected', 'name': 'Rejected', 'exit_value': 102,
                    }, {
                        'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                    }, {
                        'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                    }],
                    'transitions': [{
                        'origin': 'origin', 'destination': 'pending-approval', 'name': 'Enter P/A'
                    }, {
                        'origin': 'pending-approval', 'destination': 'approved', 'name': 'Approve',
                        'action_name': 'approve', 'permission': 'sample.accept_task'
                    }, {
                        'origin': 'pending-approval', 'destination': 'rejected', 'name': 'Reject',
                        'action_name': 'reject', 'permission': 'sample.reject_task'
                    }]
                }, {
                    'code': 'audit', 'name': 'Audit',
                    'nodes': [{
                        'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'pending-audit', 'name': 'Pending Audit',
                        'description': 'The task is about to be audited',
                    }, {
                        'type': NodeSpec.EXIT, 'code': 'audited', 'name': 'Audited', 'exit_value': 103,
                    }, {
                        'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                    }, {
                        'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                    }],
                    'transitions': [{
                        'origin': 'origin', 'destination': 'pending-audit', 'name': 'Enter Audit'
                    }, {
                        'origin': 'pending-audit', 'destination': 'audited', 'name': 'Audit',
                        'action_name': 'audit', 'permission': 'sample.audit_task'
                    }]
                }, {
                    'code': 'invoice', 'name': 'Invoice',
                    'nodes': [{
                        'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                    }, {
                        'type': NodeSpec.INPUT, 'code': 'pending-invoice', 'name': 'Pending Invoice',
                        'description': 'The task is about to be invoiced',
                    }, {
                        'type': NodeSpec.EXIT, 'code': 'invoiced', 'name': 'Invoiced', 'exit_value': 104,
                    }, {
                        'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                    }, {
                        'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                    }],
                    'transitions': [{
                        'origin': 'origin', 'destination': 'pending-invoice', 'name': 'Enter Invoice'
                    }, {
                        'origin': 'pending-invoice', 'destination': 'invoiced', 'name': 'Invoice',
                        'action_name': 'invoice', 'permission': 'sample.invoice_task'
                    }]
                }]}
        return Workflow.Spec.install(spec)

    def _install_users_and_data(self, service_type):
        User = get_user_model()
        users = [
            User.objects.create_user('foo', 'foo@example.com', 'foo1'),
            User.objects.create_user('bar', 'bar@example.com', 'bar1'),
            User.objects.create_user('baz', 'baz@example.com', 'baz1'),
            User.objects.create_user('bat', 'bat@example.com', 'bat1'),
            User.objects.create_user('boo', 'boo@example.com', 'boo1'),
            User.objects.create_user('poo', 'poo@example.com', 'poo1'),
            User.objects.create_user('god', 'god@example.com', 'god1'),
        ]
        area = Area.objects.create(head=users[6])
        task = Task.objects.create(area=area, service_type=service_type, title='Sample',
                                   content='Lorem ipsum dolor sit amet', performer=users[0], reviewer=users[1],
                                   accountant=users[2], auditor=users[3], dispatcher=users[4], attendant=users[5])
        return users, task

    def test_base_workflow(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)

    def test_user_not_able_to_create_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)
        with self.assertRaises(exceptions.WorkflowCreateDenied):
            Workflow.create(users[1], workflow, task)

    def test_user_not_able_to_execute_action_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)
        instance = Workflow.create(users[6], workflow, task)
        instance.start(users[1])
        with self.assertRaises(exceptions.WorkflowActionDenied):
            instance.execute(users[2], 'review')

    def test_execute_invalid_action_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)
        instance = Workflow.create(users[6], workflow, task)
        instance.start(users[1])
        with self.assertRaises(exceptions.WorkflowCourseNodeTransitionDoesNotExist):
            instance.execute(users[1], 'review')
            instance.execute(users[6], 'assign')
            instance.execute(users[0], 'start')
            instance.execute(users[0], 'complit')  # funny enough for a typo

    def test_execute_invalid_course_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)
        instance = Workflow.create(users[6], workflow, task)
        instance.start(users[1])
        with self.assertRaises(exceptions.WorkflowCourseInstanceDoesNotExist):
            instance.execute(users[1], 'review')
            instance.execute(users[6], 'assign')
            instance.execute(users[0], 'start')
            instance.execute(users[0], 'complete', 'wtf')

    def test_execute_invalid_nested_course_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)
        instance = Workflow.create(users[6], workflow, task)
        instance.start(users[1])
        with self.assertRaises(exceptions.WorkflowCourseInstanceDoesNotExist):
            instance.execute(users[1], 'review')
            instance.execute(users[6], 'assign')
            instance.execute(users[0], 'start')
            instance.execute(users[0], 'complete')
            instance.execute(users[3], 'audit', 'control.clorch') # this one should also fail!

    def test_execute_adequately_split_is_good(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)
        instance = Workflow.create(users[6], workflow, task)
        instance.start(users[1])
        instance.execute(users[1], 'review')
        instance.execute(users[6], 'assign')
        instance.execute(users[0], 'start')
        instance.execute(users[0], 'complete')
        actions = instance.get_workflow_available_actions(users[2])
        target = {
            'invoice': {
                'display_name': _('Invoice'),
                'actions': [{
                    'display_name': _('Invoice'),
                    'action_name': 'invoice'
                }]
            },
        }
        self.assertTrue(actions == target, "expected %r == %r" % (actions, target))
        instance.execute(users[2], 'invoice', 'invoice')
        actions = instance.get_workflow_available_actions(users[3])
        target = {
            'control.audit': {
                'display_name': _('Audit'),
                'actions': [{
                    'display_name': _('Audit'),
                    'action_name': 'audit'
                }]
            },
        }
        self.assertTrue(actions == target, "expected %r == %r" % (actions, target))
        instance.execute(users[3], 'audit', 'control.audit')
        actions = instance.get_workflow_available_actions(users[1])
        target = {
            'control.approval': {
                'display_name': _('Approval'),
                'actions': [{
                    'display_name': _('Approve'),
                    'action_name': 'approve'
                }, {
                    'display_name': _('Reject'),
                    'action_name': 'reject'
                }]
            },
        }
        self.assertTrue(actions == target, "expected %r == %r" % (actions, target))
        instance.execute(users[1], 'approve', 'control.approval')
        workflow_status = instance.get_workflow_status()
        target = {'': ('ended', 105)}
        self.assertTrue(workflow_status == target, "expected %r == %r" % (workflow_status, target))

    def test_rejection_and_loopback_is_good(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)
        instance = Workflow.create(users[6], workflow, task)
        instance.start(users[1])
        instance.execute(users[1], 'review')
        instance.execute(users[6], 'assign')
        instance.execute(users[0], 'start')
        instance.execute(users[0], 'complete')
        instance.execute(users[1], 'reject', 'control.approval')
        workflow_status = instance.get_workflow_status()
        target = {'': ('waiting', 'started')}
        self.assertTrue(workflow_status == target, "expected %r == %r" % (workflow_status, target))

    def test_approval_deliverable_waiting_delivery_is_good(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.DELIVERABLE)
        instance = Workflow.create(users[6], workflow, task)
        instance.start(users[1])
        instance.execute(users[1], 'review')
        instance.execute(users[6], 'assign')
        instance.execute(users[0], 'start')
        instance.execute(users[0], 'complete')
        instance.execute(users[1], 'approve', 'control.approval')
        instance.execute(users[2], 'invoice', 'invoice')
        instance.execute(users[3], 'audit', 'control.audit')
        workflow_status = instance.get_workflow_status()
        target = {'': ('waiting', 'pending-delivery')}
        self.assertTrue(workflow_status == target, "expected %r == %r" % (workflow_status, target))
        self.assertEqual(instance.instance.document.content, 'Lorem ipsum dolor sit amet Pending Delivery')

    def test_unmatched_condition_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data('crap')
        with self.assertRaises(exceptions.WorkflowCourseNodeMultiplexerDidNotSatisfyAnyCondition):
            instance = Workflow.create(users[6], workflow, task)
            instance.start(users[1])
            instance.execute(users[1], 'review')
            instance.execute(users[6], 'assign')
            instance.execute(users[0], 'start')
            instance.execute(users[0], 'complete')
            instance.execute(users[1], 'approve', 'control.approval')
            instance.execute(users[2], 'invoice', 'invoice')
            instance.execute(users[3], 'audit', 'control.audit')

    def test_cancel_terminated_course_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.DELIVERABLE)
        with self.assertRaises(exceptions.WorkflowCourseInstanceAlreadyTerminated):
            instance = Workflow.create(users[6], workflow, task)
            instance.start(users[1])
            instance.cancel(users[6])
            instance.cancel(users[6])

    def test_cancel_course_without_workflow_permission_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.DELIVERABLE)
        with self.assertRaises(exceptions.WorkflowCourseCancelDeniedByWorkflow):
            instance = Workflow.create(users[6], workflow, task)
            instance.start(users[1])
            instance.cancel(users[3])

    def test_cancel_course_without_course_permission_is_bad(self):
        workflow = self._base_install_workflow_spec()
        spec = workflow.spec
        permission = spec.cancel_permission
        spec.cancel_permission = ''
        spec.save()
        course_spec = spec.course_specs.get(code='')
        course_spec.cancel_permission = permission
        course_spec.save()
        users, task = self._install_users_and_data(Task.DELIVERABLE)
        with self.assertRaises(exceptions.WorkflowCourseCancelDeniedByCourse):
            instance = Workflow.create(users[6], workflow, task)
            instance.start(users[1])
            instance.cancel(users[3])

    def test_start_a_started_workflow_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.DELIVERABLE)
        with self.assertRaises(exceptions.WorkflowInstanceNotPending):
            instance = Workflow.create(users[6], workflow, task)
            instance.start(users[1])
            instance.start(users[1])

    def test_execute_existing_action_from_split_node_is_bad(self):
        workflow = self._base_install_workflow_spec()
        users, task = self._install_users_and_data(Task.SERVICE)
        with self.assertRaises(exceptions.WorkflowCourseInstanceNotWaiting):
            instance = Workflow.create(users[6], workflow, task)
            instance.start(users[1])
            instance.execute(users[1], 'review')
            instance.execute(users[6], 'assign')
            instance.execute(users[0], 'start')
            instance.execute(users[0], 'complete')
            instance.execute(users[0], 'on-accept')