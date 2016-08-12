from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
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
                        'type': NodeSpec.ENTER, 'code': 'created', 'name': 'Created',
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
                        'origin': 'created', 'destination': 'reviewed', 'name': 'Review',
                        'permission': 'sample.review_task'
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
                        'action_name': 'approve'
                    }, {
                        'origin': 'pending-approval', 'destination': 'rejected', 'name': 'Reject',
                        'action_name': 'reject'
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
                        'action_name': 'audit'
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
                        'action_name': 'invoice'
                    }]
                }]}
        return Workflow.Spec.install(spec)

    def _install_users_and_area(self):
        User = get_user_model()
        users = [
            User.objects.create_user('foo', 'foo@example.com', 'foo1'),
            User.objects.create_user('bar', 'bar@example.com', 'bar1'),
            User.objects.create_user('baz', 'baz@example.com', 'baz1'),
            User.objects.create_user('bat', 'bat@example.com', 'bat1'),
            User.objects.create_user('boo', 'boo@example.com', 'boo1'),
        ]
        area = Area.objects.create(head=users[0])
        return users, area

    def test_base_workflow(self):
        self._base_install_workflow_spec()
        users, area = self._install_users_and_area()
