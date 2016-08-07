from django.core.exceptions import ValidationError
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec
from arcanelab.ouroboros import exceptions
from .support import ValidationErrorWrappingTestCase

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
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                            'joiner': 'sample.support.dummy_joiner',
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
            Workflow.Spec.install(spec)
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
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                            'joiner': 'sample.support.dummy_joiner',
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

    def test_exit_node_without_exit_value_is_bad(self):
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
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit',
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

    # testing cancel node

    def test_cancel_node_with_inbounds_is_bad(self):
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
            trans.destination = installed.spec.course_specs.get(code='').node_specs.get(code='cancel')
            trans.save()
            installed.spec.course_specs.get(code='').node_specs.get(code='cancel').full_clean()
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasInbounds.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_cancel_node_with_outbounds_is_bad(self):
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
            trans.origin = installed.spec.course_specs.get(code='').node_specs.get(code='cancel')
            trans.save()
            installed.spec.course_specs.get(code='').node_specs.get(code='cancel').full_clean()
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasOutbounds.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_cancel_node_with_branches_is_bad(self):
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
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                            'branches': ['foo', 'bar'],
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

    def test_cancel_node_with_exit_value_is_bad(self):
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
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel', 'exit_value': 101,
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

    def test_cancel_node_with_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                            'joiner': 'sample.support.dummy_joiner',
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

    def test_cancel_node_with_execute_permission_is_bad(self):
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
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                            'execute_permission': 'sample.cancel_task',
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

    # testing joined node

    def test_joined_node_with_inbounds_is_bad(self):
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
                            'type': NodeSpec.INPUT, 'code': 'loop-3', 'name': 'Loop-3',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo', 'bar'], 'joiner': 'sample.support.dummy_joiner',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-3', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop-to-1',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-3', 'name': 'Loop', 'action_name': 'loop-to-3',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
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
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            installed = Workflow.Spec.install(spec)
            course_spec = installed.spec.course_specs.get(code='bar')
            course_spec.node_specs.get(code='origin').outbounds.create(
                destination=course_spec.node_specs.get(code='joined'),
                name='Join Transition'
            )
            course_spec.node_specs.get(code='joined').full_clean()
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasInbounds.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_joined_node_with_outbounds_is_bad(self):
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
                            'type': NodeSpec.INPUT, 'code': 'loop-3', 'name': 'Loop-3',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo', 'bar'], 'joiner': 'sample.support.dummy_joiner',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-3', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop-to-1',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-3', 'name': 'Loop', 'action_name': 'loop-to-3',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
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
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            installed = Workflow.Spec.install(spec)
            course_spec = installed.spec.course_specs.get(code='bar')
            course_spec.node_specs.get(code='exit').inbounds.create(
                origin=course_spec.node_specs.get(code='joined'),
                name='Post-Join Transition'
            )
            course_spec.node_specs.get(code='joined').full_clean()
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasOutbounds.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_joined_node_with_branches_is_bad(self):
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
                            'type': NodeSpec.INPUT, 'code': 'loop-3', 'name': 'Loop-3',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo', 'bar'], 'joiner': 'sample.support.dummy_joiner',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-3', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop-to-1',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-3', 'name': 'Loop', 'action_name': 'loop-to-3',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                            'branches': ['baz', 'bat']
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'split', 'name': 'Split',
                            'branches': ['baz', 'bat']
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'split', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'split', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task', 'action_name': 'end',
                        }]
                    }, {
                        'code': 'bar', 'name': 'Bar',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }, {
                        'code': 'bat', 'name': 'Bat',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }, {
                        'code': 'baz', 'name': 'Baz',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
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

    def test_joined_node_with_exit_value_is_bad(self):
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
                            'type': NodeSpec.INPUT, 'code': 'loop-3', 'name': 'Loop-3',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo', 'bar'], 'joiner': 'sample.support.dummy_joiner',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-3', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop-to-1',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-3', 'name': 'Loop', 'action_name': 'loop-to-3',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                            'exit_value': 101,
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
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'exit_value')

    def test_joined_node_with_joiner_is_bad(self):
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
                            'type': NodeSpec.INPUT, 'code': 'loop-3', 'name': 'Loop-3',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo', 'bar'], 'joiner': 'sample.support.dummy_joiner',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-3', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop-to-1',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-3', 'name': 'Loop', 'action_name': 'loop-to-3',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                            'joiner': 'sample.support.dummy_joiner',
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
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'joiner')

    def test_joined_node_with_execute_permission_is_bad(self):
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
                            'type': NodeSpec.INPUT, 'code': 'loop-3', 'name': 'Loop-3',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo', 'bar'], 'joiner': 'sample.support.dummy_joiner',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-3', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop-to-1',
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-3', 'name': 'Loop', 'action_name': 'loop-to-3',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                            'execute_permission': 'sample.cancel_task',
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
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'execute_permission')

    # testing split node

    def test_split_node_without_inbounds_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2', 'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End'
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
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoInbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_split_node_without_outbounds_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1'
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2', 'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'End', 'action_name': 'end'
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Go Branch', 'action_name': 'go-branch'
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
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoOutbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_split_node_without_branches_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-2', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNotEnoughBranches.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_split_node_with_one_branch_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2',
                            'branches': ['foo'],
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-2', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End'
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
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNotEnoughBranches.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_split_node_with_branches_in_other_workflow_is_bad(self):
        with self.assertRaises(ValidationError) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2', 'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-2', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End A', 'action_name': 'end_a'
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
            target_wf = Workflow.Spec.install(spec)
            spec2 = {'model': 'sample.Task', 'code': 'wfspec2', 'name': 'Workflow Spec 2', 'create_permission': '',
                     'cancel_permission': '',
                     'courses': [{
                         'code': '', 'name': 'Single',
                         'nodes': [{
                             'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                         }, {
                             'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                         }, {
                             'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                         }],
                         'transitions': [{
                             'origin': 'origin', 'destination': 'exit', 'name': 'Transition',
                         }]
                     }]}
            target_wf2 = Workflow.Spec.install(spec2)
            node_spec = target_wf.spec.course_specs.get(code='').node_specs.get(code='loop-2')
            node_spec.branches.add(target_wf2.spec.course_specs.get(code=''))
            node_spec.branches.remove(target_wf.spec.course_specs.get(code='bar'))
            node_spec.full_clean()
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeInconsistentBranches.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_split_node_with_one_outbound_and_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2', 'branches': ['foo', 'bar'],
                            'joiner': 'sample.support.dummy_joiner'
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-2', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End'
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
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeInconsistentJoiner.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_split_node_with_many_outbounds_and_no_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2', 'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-2', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End A'
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End B'
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
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeInconsistentJoiner.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_split_node_with_exit_value_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2', 'branches': ['foo', 'bar'],
                            'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-2', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End'
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
        exc = self.unwrapValidationError(ar.exception, 'exit_value')

    def test_split_node_with_execute_permission_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'loop-2', 'name': 'Loop-2', 'branches': ['foo', 'bar'],
                            'execute_permission': 'sample.cancel_task',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-2', 'name': 'Initial transition 1',
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End'
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
        exc = self.unwrapValidationError(ar.exception, 'execute_permission')

    # testing step node

    def test_step_node_without_inbounds_is_bad(self):
        with self.assertRaises(ValidationError) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.STEP, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoInbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_step_node_with_no_outbounds_is_bad(self):
        with self.assertRaises(ValidationError) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.STEP, 'code': 'step', 'name': 'step',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'state', 'name': 'State',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'state', 'name': 'Initial transition',
                        }, {
                            'origin': 'state', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'state', 'destination': 'step', 'name': 'Step transition',
                            'action_name': 'go-step',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoOutbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_step_node_with_many_outbounds_is_bad(self):
        with self.assertRaises(ValidationError) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.STEP, 'code': 'step', 'name': 'step',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'state', 'name': 'State',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-2', 'name': 'Exit 2', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'state', 'name': 'Initial transition',
                        }, {
                            'origin': 'state', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'break',
                        }, {
                            'origin': 'state', 'destination': 'step', 'name': 'Step transition',
                            'action_name': 'go-step',
                        }, {
                            'origin': 'step', 'destination': 'exit', 'name': 'Exit 1 transition',
                        }, {
                            'origin': 'step', 'destination': 'exit-2', 'name': 'Exit 2 transition',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasMultipleOutbounds.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_step_node_with_branches_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.STEP, 'code': 'loop-1', 'name': 'Loop-1',
                            'branches': ['foo', 'bar'],
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
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Move'
                        }, {
                            'origin': 'loop-2', 'destination': 'exit', 'name': 'End'
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

    def test_step_node_with_exit_value_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.STEP, 'code': 'loop-1', 'name': 'Loop-1',
                            'exit_value': 101
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'exit_value')

    def test_step_node_with_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.STEP, 'code': 'loop-1', 'name': 'Loop-1',
                            'joiner': 'sample.support.dummy_joiner'
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'joiner')

    def test_step_node_with_execute_permission_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.STEP, 'code': 'loop-1', 'name': 'Loop-1',
                            'execute_permission': 'sample.cancel_task',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'loop-1', 'name': 'Initial transition',
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Final transition',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'execute_permission')

    # testing multiplexer node

    def test_multiplexer_node_with_no_inbounds_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.MULTIPLEXER, 'code': 'multiplexer', 'name': 'Decision',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-a', 'name': 'Exit A', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-b', 'name': 'Exit B', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit-a', 'name': 'Bypass transition',
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-a', 'name': 'Choice A',
                            'priority': 0, 'condition': 'sample.support.dummy_condition_a'
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-b', 'name': 'Choice B',
                            'priority': 1, 'condition': 'sample.support.dummy_condition_b'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoInbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_multiplexer_node_with_no_outbounds_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.MULTIPLEXER, 'code': 'multiplexer', 'name': 'Decision',
                        }, {
                            'type': NodeSpec.MULTIPLEXER, 'code': 'multiplexer-2', 'name': 'Decision 2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-a', 'name': 'Exit A', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-b', 'name': 'Exit B', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'multiplexer', 'name': 'Bypass transition',
                        }, {
                            'origin': 'multiplexer', 'destination': 'multiplexer-2', 'name': 'Choice A',
                            'priority': 0, 'condition': 'sample.support.dummy_condition_a'
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-a', 'name': 'Choice A',
                            'priority': 0, 'condition': 'sample.support.dummy_condition_b'
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-b', 'name': 'Choice B',
                            'priority': 1, 'condition': 'sample.support.dummy_condition_c'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoOutbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_multiplexer_node_with_one_outbound_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.MULTIPLEXER, 'code': 'multiplexer', 'name': 'Decision',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-a', 'name': 'Exit A', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'multiplexer', 'name': 'Bypass transition',
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-a', 'name': 'Choice A',
                            'priority': 0, 'condition': 'sample.support.dummy_condition_a'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, '__all__')
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasOneOutbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_multiplexer_node_with_branches_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'split', 'name': 'Split',
                            'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.MULTIPLEXER, 'code': 'multiplexer', 'name': 'Decision',
                            'branches': ['foo', 'bar'],
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-a', 'name': 'Exit A', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-b', 'name': 'Exit B', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'split', 'name': 'split transition',
                        }, {
                            'origin': 'split', 'destination': 'multiplexer', 'name': 'multiplexer transition',
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-a', 'name': 'Choice A',
                            'priority': 0, 'condition': 'sample.support.dummy_condition_a'
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-b', 'name': 'Choice B',
                            'priority': 1, 'condition': 'sample.support.dummy_condition_b'
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

    def test_multiplexer_node_with_execute_permission_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.MULTIPLEXER, 'code': 'multiplexer', 'name': 'Decision',
                            'execute_permission': 'sample.cancel_task',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-a', 'name': 'Exit A', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-b', 'name': 'Exit B', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'multiplexer', 'name': 'Bypass transition',
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-a', 'name': 'Choice A',
                            'priority': 0, 'condition': 'sample.support.dummy_condition_a'
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-b', 'name': 'Choice B',
                            'priority': 1, 'condition': 'sample.support.dummy_condition_b'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'execute_permission')

    def test_multiplexer_node_with_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.MULTIPLEXER, 'code': 'multiplexer', 'name': 'Decision',
                            'joiner': 'sample.support.dummy_joiner',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-a', 'name': 'Exit A', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-b', 'name': 'Exit B', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'multiplexer', 'name': 'Bypass transition',
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-a', 'name': 'Choice A',
                            'priority': 0, 'condition': 'sample.support.dummy_condition_a'
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-b', 'name': 'Choice B',
                            'priority': 1, 'condition': 'sample.support.dummy_condition_b'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'joiner')

    def test_multiplexer_node_with_exit_value_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.MULTIPLEXER, 'code': 'multiplexer', 'name': 'Decision',
                            'exit_value': 102,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-a', 'name': 'Exit A', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-b', 'name': 'Exit B', 'exit_value': 101,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'multiplexer', 'name': 'Bypass transition',
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-a', 'name': 'Choice A',
                            'priority': 0, 'condition': 'sample.support.dummy_condition_a'
                        }, {
                            'origin': 'multiplexer', 'destination': 'exit-b', 'name': 'Choice B',
                            'priority': 1, 'condition': 'sample.support.dummy_condition_b'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception, 'exit_value')

    # testing input node

    def test_input_node_with_no_inbounds_is_bad(self):
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
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoInbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_input_node_with_no_outbounds_is_bad(self):
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
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseNodeHasNoOutbound.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_input_node_with_branches_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                            'branches': ['foo', 'bar'],
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

    def test_input_node_with_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2',
                            'joiner': 'sample.support.dummy_joiner',
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

    def test_input_node_with_exit_value_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop-1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop-2', 'exit_value': 101,
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
