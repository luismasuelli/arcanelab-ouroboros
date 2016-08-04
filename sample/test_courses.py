from django.core.exceptions import ValidationError
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec, WorkflowSpec, CourseSpec
from arcanelab.ouroboros import exceptions
from .support import ValidationErrorWrappingTestCase

############################################
# WorkflowSpec tests
############################################

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
                        }]}]}
            Workflow.Spec.install(spec)
            self.assertTrue(True)
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

    def tearDown(self):
        """
        Removing the successfully created workflow spec.
        """

        WorkflowSpec.objects.all().delete()

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
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wf-badnode',
                                   'name': 'Workflow Spec',
                                   'description': 'This workflow spec shall not pass',
                                   'create_permission': '',
                                   'cancel_permission': '',
                                   'courses': [{
                                       'code': '',
                                       'name': 'Root',
                                       'description': 'The root course',
                                       'nodes': [{
                                           'type': NodeSpec.ENTER,
                                           'code': 'origin',
                                           'name': 'Origin',
                                           'description': 'The origin node'
                                       }, {
                                           'type': NodeSpec.SPLIT,
                                           'code': 'parallel-1',
                                           'name': 'Parallel',
                                           'joiner': 'sample.support.dummy_joiner',
                                           'description': 'Parallel brancher',
                                           'branches': ['foo', 'bar']
                                       }, {
                                           'type': NodeSpec.EXIT,
                                           'code': 'exit',
                                           'name': 'Exit',
                                           'description': 'One exit node',
                                           'exit_value': 100,
                                       }, {
                                           'type': NodeSpec.EXIT,
                                           'code': 'exit-2',
                                           'name': 'Exit 2',
                                           'description': 'Another exit node',
                                           'exit_value': 100,
                                       }, {
                                           'type': NodeSpec.CANCEL,
                                           'code': 'cancel',
                                           'name': 'Cancel',
                                           'description': 'The cancel node',
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'parallel-1',
                                           'name': 'Initial transition',
                                           'description': 'The initial transition',
                                           'permission': 'sample.start_task',
                                       }, {
                                           'origin': 'parallel-1',
                                           'action_name': 'escape-1',
                                           'destination': 'exit',
                                           'name': 'Final transition 1',
                                           'description': 'The final transition to exit 1',
                                       }, {
                                           'origin': 'parallel-1',
                                           'action_name': 'escape-2',
                                           'destination': 'exit-2',
                                           'name': 'Final transition 2',
                                           'description': 'The final transition to exit 2',
                                       }]
                                   }, {
                                       'code': 'foo',
                                       'name': 'Foo',
                                       'description': 'Foo branch',
                                       'nodes': [{
                                           'type': NodeSpec.ENTER,
                                           'code': 'origin',
                                           'name': 'Origin',
                                           'description': 'The origin node'
                                       }, {
                                           'type': NodeSpec.EXIT,
                                           'code': 'exit',
                                           'name': 'Exit',
                                           'description': 'The only exit node',
                                           'exit_value': 100,
                                       }, {
                                           'type': NodeSpec.CANCEL,
                                           'code': 'cancel',
                                           'name': 'Cancel',
                                           'description': 'The cancel node',
                                       }, {
                                           'type': NodeSpec.JOINED,
                                           'code': 'joined',
                                           'name': 'Joined',
                                           'description': 'The joined node',
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'exit',
                                           'name': 'Initial transition',
                                           'description': 'The initial and only transition',
                                           'permission': 'sample.start_task',
                                       }]
                                   }, {
                                       'code': 'bar',
                                       'name': 'Bar',
                                       'description': 'Bar branch',
                                       'nodes': [{
                                           'type': NodeSpec.ENTER,
                                           'code': 'origin',
                                           'name': 'Origin',
                                           'description': 'The origin node'
                                       }, {
                                           'type': NodeSpec.EXIT,
                                           'code': 'exit',
                                           'name': 'Exit',
                                           'description': 'The only exit node',
                                           'exit_value': 100,
                                       }, {
                                           'type': NodeSpec.CANCEL,
                                           'code': 'cancel',
                                           'name': 'Cancel',
                                           'description': 'The cancel node',
                                       }, {
                                           'type': NodeSpec.JOINED,
                                           'code': 'joined',
                                           'name': 'Joined',
                                           'description': 'The joined node',
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'exit',
                                           'name': 'Initial transition',
                                           'description': 'The initial transition',
                                           'permission': 'sample.start_task',
                                       }]
                                   }]})
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

    def tearDown(self):
        """
        Removing the successfully created workflow spec.
        """

        WorkflowSpec.objects.all().delete()
