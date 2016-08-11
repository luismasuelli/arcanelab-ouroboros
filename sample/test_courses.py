from django.core.exceptions import ValidationError
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec, WorkflowSpec, CourseSpec
from arcanelab.ouroboros import exceptions
from .support import ValidationErrorWrappingTestCase

############################################
# WorkflowSpec tests
############################################

# TODO WARNING I MADE CHANGES TO THE WAY THE BRANCHES BEHAVE.
# TODO   AT MODEL LEVEL, COURSES DO NOT ALLOW UNREACHABLE NODES AND
# TODO   -IF BEING CHILDREN COURSES- DO NOT ALLOW AN AUTOMATIC PATH
# TODO   FROM THE ENTER NODE TO ANY EXIT NODE, WITHOUT NODES OF TYPE
# TODO   SPLIT OR INPUT. TESTS MUST BE CHANGED ACCORDINGLY SO THEY
# TODO   TEST THESE VALIDATIONS AND DO NOT FAIL THEM IN THE BRANCHES
# TODO   NOT BEING TESTED (ALSO, CERTAIN TESTS WILL CHANGE THE WAY
# TODO   THEY FAIL, SO AN INTENSIVE CHECK MUST BE DONE). THESE CHANGES
# TODO   IN THE TESTS MUST BE AMEND-COMMITTED

class WorkflowSpecTestCase(ValidationErrorWrappingTestCase):

    def test_unexpected_input_format_or_bad_model_is_bad(self):
        """
        Input format verification.
        :return:
        """

        with self.assertRaises(ValueError):
            # JSON validation on strings
            Workflow.Spec.install('{')

        with self.assertRaises(TypeError):
            # type validation when non-string (dict is good)
            Workflow.Spec.install(1)

        with self.assertRaises(LookupError):
            # model validation (concrete/exists)
            Workflow.Spec.install({'model': 'ouroboros.Document'})

        with self.assertRaises(TypeError):
            # model validation (hierarchy)
            Workflow.Spec.install({'model': 'auth.User'})

    def test_empty_workflow_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'empty-wfspec', 'name': 'Empty Workflow Spec'}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowSpecHasNoMainCourse.CODE, 'Invalid subclass of ValidationError '
                                                                                'raised')

    def test_single_main_course_is_good(self):
        try:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit',
                            'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        except Exception as e:
            self.assertFalse(True, 'An exception was raised (%s): %s' % (type(e).__name__, e))

    def test_cyclical_course_dependencies_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Root',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'parallel-1', 'name': 'Parallel', 'branches': ['foo', 'bar']
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit',
                            'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'parallel-1', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'parallel-1', 'action_name': 'escape', 'destination': 'exit',
                            'name': 'Final transition',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
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
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin'
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'bad-parallel', 'name': 'Bad-Parallel',
                            'branches': ['foo', 'bar']
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'bad-parallel', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'bad-parallel', 'action_name': 'escape', 'destination': 'exit',
                            'name': 'Final transition',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowSpecHasCircularDependentCourses.CODE,
                         'Invalid subclass of ValidationError raised')

############################################
# CourseSpec tests
############################################

class CourseSpecTestCase(ValidationErrorWrappingTestCase):

    def test_no_cancel_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasNoRequiredNode.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_multi_cancel_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel-2', 'name': 'Cancel 2',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecMultipleRequiredNodes.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_no_enter_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': []
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasNoRequiredNode.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_multi_enter_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.ENTER, 'code': 'origin-2', 'name': 'Origin-2',
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
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecMultipleRequiredNodes.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_no_exit_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': []
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasNoRequiredNode.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_no_joined_node_when_caller_uses_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Root',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'parallel-1', 'name': 'Parallel',
                            'joiner': 'sample.support.dummy_joiner', 'branches': ['foo', 'bar']
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-2', 'name': 'Exit 2', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'parallel-1', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'parallel-1', 'action_name': 'escape-1', 'destination': 'exit',
                            'name': 'Final transition 1',
                        }, {
                            'origin': 'parallel-1', 'action_name': 'escape-2', 'destination': 'exit-2',
                            'name': 'Final transition 2',
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
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasNoRequiredNode.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_bad_caller_type_is_bad(self):
        try:
            spec = {'model': 'sample.Task', 'code': 'wf-badnode', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Root',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'parallel-1', 'name': 'Parallel',
                            'joiner': 'sample.support.dummy_joiner', 'branches': ['foo', 'bar']
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-2', 'name': 'Exit 2', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'parallel-1', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'parallel-1', 'action_name': 'escape-1', 'destination': 'exit',
                            'name': 'Final transition 1',
                        }, {
                            'origin': 'parallel-1', 'action_name': 'escape-2', 'destination': 'exit-2',
                            'name': 'Final transition 2',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'input', 'name': 'Input',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'input', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'input', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'go-exit',
                        }]
                    }, {
                        'code': 'bar', 'name': 'Bar',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'input', 'name': 'Input',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'input', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'input', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'go-exit',
                        }]
                    }]}
            Workflow.Spec.install(spec)
            node_spec = NodeSpec.objects.get(code='parallel-1', course_spec__code='',
                                             course_spec__workflow_spec__code='wf-badnode')
            node_spec.type = NodeSpec.INPUT
            node_spec.save()
            course_spec = CourseSpec.objects.get(code='foo', workflow_spec__code='wf-badnode')
        except Exception as e:
            self.assertFalse(True, 'An exception was raised (%s): %s' % (type(e).__name__, e))
        else:
            with self.assertRaises(ValidationError) as ar:
                course_spec.full_clean()
            exc = self.unwrapValidationError(ar.exception)
            self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasInvalidCallers.CODE,
                             'Invalid subclass of ValidationError raised')

    def test_unreachable_node_by_enter_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop 1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop 2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit',
                            'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'exit', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop'
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop'
                        }, {
                            'origin': 'loop-1', 'destination': 'exit', 'name': 'Break Loop', 'action_name': 'break-loop'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasUnreachableNodesByEnter.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_unreachable_node_by_exit_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wfspec', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Single',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'input', 'name': 'Input',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-1', 'name': 'Loop 1',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'loop-2', 'name': 'Loop 2',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit',
                            'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'input', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'input', 'destination': 'exit', 'name': 'Final transition',
                            'permission': 'sample.start_task', 'action_name': 'hop-end'
                        }, {
                            'origin': 'input', 'destination': 'loop-1', 'name': 'Loop transition',
                            'permission': 'sample.start_task', 'action_name': 'enter-loop'
                        }, {
                            'origin': 'loop-1', 'destination': 'loop-2', 'name': 'Loop', 'action_name': 'loop'
                        }, {
                            'origin': 'loop-2', 'destination': 'loop-1', 'name': 'Loop', 'action_name': 'loop'
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasUnreachableNodesByExit.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_automatic_paths_in_branches_are_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            spec = {'model': 'sample.Task', 'code': 'wf-badnode', 'name': 'Workflow Spec', 'create_permission': '',
                    'cancel_permission': '',
                    'courses': [{
                        'code': '', 'name': 'Root',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.SPLIT, 'code': 'parallel-1', 'name': 'Parallel',
                            'joiner': 'sample.support.dummy_joiner', 'branches': ['foo', 'bar']
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit-2', 'name': 'Exit 2', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'parallel-1', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'parallel-1', 'action_name': 'escape-1', 'destination': 'exit',
                            'name': 'Final transition 1',
                        }, {
                            'origin': 'parallel-1', 'action_name': 'escape-2', 'destination': 'exit-2',
                            'name': 'Final transition 2',
                        }]
                    }, {
                        'code': 'foo', 'name': 'Foo',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.STEP, 'code': 'step', 'name': 'Step',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'step', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'step', 'destination': 'exit', 'name': 'Final transition',
                        }]
                    }, {
                        'code': 'bar', 'name': 'Bar',
                        'nodes': [{
                            'type': NodeSpec.ENTER, 'code': 'origin', 'name': 'Origin',
                        }, {
                            'type': NodeSpec.INPUT, 'code': 'input', 'name': 'Input',
                        }, {
                            'type': NodeSpec.EXIT, 'code': 'exit', 'name': 'Exit', 'exit_value': 100,
                        }, {
                            'type': NodeSpec.CANCEL, 'code': 'cancel', 'name': 'Cancel',
                        }, {
                            'type': NodeSpec.JOINED, 'code': 'joined', 'name': 'Joined',
                        }],
                        'transitions': [{
                            'origin': 'origin', 'destination': 'input', 'name': 'Initial transition',
                            'permission': 'sample.start_task',
                        }, {
                            'origin': 'input', 'destination': 'exit', 'name': 'Final transition',
                            'action_name': 'go-exit',
                        }]
                    }]}
            Workflow.Spec.install(spec)
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasAutomaticPath.CODE,
                         'Invalid subclass of ValidationError raised')
