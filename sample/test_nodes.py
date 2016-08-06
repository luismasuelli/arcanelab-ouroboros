from django.core.exceptions import ValidationError
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec, WorkflowSpec, CourseSpec
from arcanelab.ouroboros import exceptions
from .support import ValidationErrorWrappingTestCase


# TODO transition-spec

# TODO check on instances

# TODO check on runs

##########################################
# NodeSpec tests
##########################################

class NodeSpecTestCase(ValidationErrorWrappingTestCase):

    # testing enter node
    # TODO actually make them! right now they are only empty stubs

    def test_enter_node_with_inbounds_is_bad(self):
        with self.assertRaises(ValidationError) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            installed = Workflow.Spec.install(spec)
            trans = installed.spec.course_specs.get(code='').node_specs.get(code='loop-1').outbounds.get(
                action_name='loop'
            )
            trans.destination = installed.spec.course_specs.get(code='').node_specs.get(code='origin')
            trans.save()
            installed.spec.course_specs.get(code='').node_specs.get(code='origin').full_clean()
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasInbounds.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_enter_node_without_outbounds_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Initial transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoOutbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_enter_node_wit_many_outbounds_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'origin', 'destination': 'loop-2', 'name': 'Initial transition 2',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Initial transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasMultipleOutbounds.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_enter_node_with_exit_value_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Initial transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'exit_value')

    def test_enter_node_with_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin', 'joiner':
                            'sample.support.dummy_joiner',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Initial transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'joiner')

    def test_enter_node_with_branches_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                            'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Initial transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }, {
                        'code': 'bar', 'name': 'Bar',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasBranches.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_enter_node_with_execute_permission_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                            'execute_permission': 'sample.cancel_task',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Initial transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'execute_permission')

    # testing exit node

    def test_exit_node_with_outbounds_is_bad(self):
        with self.assertRaises(ValidationError) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            installed = Workflow.Spec.install(spec)
            trans = installed.spec.course_specs.get(code='').node_specs.get(code='loop-1').outbounds.get(
                action_name='loop'
            )
            trans.origin = installed.spec.course_specs.get(code='').node_specs.get(code='exit')
            trans.save()
            installed.spec.course_specs.get(code='').node_specs.get(code='exit').full_clean()
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasOutbounds.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_exit_node_without_inbounds_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            installed = Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoInbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_exit_node_with_branches_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                            'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Initial transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }, {
                        'code': 'bar', 'name': 'Bar',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasBranches.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_exit_node_with_execute_permission_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                            'execute_permission': 'sample.cancel_task',
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Initial transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'execute_permission')

    def test_exit_node_with_joiner_is_bad(self):
        pass

    def test_exit_node_without_exit_value_is_bad(self):
        pass

    # testing cancel node

    def test_cancel_node_with_inbounds_is_bad(self):
        pass

    def test_cancel_node_with_outbounds_is_bad(self):
        pass

    def test_cancel_node_with_branches_is_bad(self):
        pass

    def test_cancel_node_with_exit_value_is_bad(self):
        pass

    def test_cancel_node_with_joiner_is_bad(self):
        pass

    def test_cancel_node_with_execute_permission_is_bad(self):
        pass

    # testing joined node

    def test_joined_node_with_inbounds_is_bad(self):
        pass

    def test_joined_node_with_outbounds_is_bad(self):
        pass

    def test_joined_node_with_branches_is_bad(self):
        pass

    def test_joined_node_with_exit_value_is_bad(self):
        pass

    def test_joined_node_with_joiner_is_bad(self):
        pass

    def test_joined_node_with_execute_permission_is_bad(self):
        pass

    # testing split node

    def test_split_node_without_inbounds_is_bad(self):
        pass

    def test_split_node_without_outbounds_is_bad(self):
        pass

    def test_split_node_without_branches_is_bad(self):
        pass

    def test_split_node_with_one_branch_is_bad(self):
        pass

    def test_split_node_with_branches_in_other_workflow_is_bad(self):
        pass

    def test_split_node_with_one_outbound_and_joiner_is_bad(self):
        pass

    def test_split_node_with_many_outbounds_and_no_joiner_is_bad(self):
        pass

    def test_split_node_with_exit_value_is_bad(self):
        pass

    def test_split_node_with_execute_permission_is_bad(self):
        pass

    # testing step node

    def test_step_node_without_inbounds_is_bad(self):
        pass

    def test_step_node_with_no_outbounds_is_bad(self):
        pass

    def test_step_node_with_many_outbounds_is_bad(self):
        pass

    def test_step_node_with_branches_is_bad(self):
        pass

    def test_step_node_with_exit_value_is_bad(self):
        pass

    def test_step_node_with_joiner_is_bad(self):
        pass

    def test_step_node_with_execute_permission_is_bad(self):
        pass

    # testing multiplexer node

    def test_multiplexer_node_with_no_inbounds_is_bad(self):
        pass

    def test_multiplexer_node_with_no_outbounds_is_bad(self):
        pass

    def test_multiplexer_node_with_one_outbound_is_bad(self):
        pass

    def test_multiplexer_node_with_branches_is_bad(self):
        pass

    def test_multiplexer_node_with_execute_permission_is_bad(self):
        pass

    def test_multiplexer_node_with_joiner_is_bad(self):
        pass

    def test_multiplexer_node_with_exit_value_is_bad(self):
        pass

    # testing input node

    def test_input_node_with_no_inbounds_is_bad(self):
        pass

    def test_input_node_with_no_outbounds_is_bad(self):
        pass

    def test_input_node_with_branches_is_bad(self):
        pass

    def test_input_node_with_execute_permission_is_bad(self):
        pass

    def test_input_node_with_joiner_is_bad(self):
        pass

    def test_input_node_with_exit_value_is_bad(self):
        pass

##########################################
# TransitionSpec tests
##########################################

class TransitionSpecTestCase(ValidationErrorWrappingTestCase):

    pass
