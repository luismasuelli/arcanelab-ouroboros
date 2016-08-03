from django.core.exceptions import ValidationError
from django.test import TestCase
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec, WorkflowSpec
from arcanelab.ouroboros import exceptions

"""
Involved tests here:

    - Empty workflow (no courses) -> Must Explode: No Main.
    - Workflow with single main course (enter, cancel, exit, enter->exit) -> Must Pass.
    - Workflow with two main courses (enter, cancel, exit, enter->exit) -> Must Explode: Multiple Main.
    - Workflow with a main course with two branches. Main course is
      (enter, split, cancel, exit, enter->split, split->exit), while a branch
      references a course like (enter, cancel, exit, enter->exit) and the other
      references the main branch -> Must Explode: cyclical.

    ... add more cases.
"""

class ValidationErrorWrappingTestCase(TestCase):

    def unwrapValidationError(self, exception, field='__all__'):
        ed_items = exception.error_dict
        self.assertEqual(len(ed_items), 1, 'The raised ValidationError produces an invalid count of errors (expected 1)')
        self.assertIn(field, ed_items, 'The raised ValidationError produces errors for other fields than %s' % field)
        self.assertIsInstance(ed_items[field], list, 'The raised ValidationError has a non-list object in %s' % field)
        self.assertEqual(len(ed_items[field]), 1, 'The raised ValidationError has more than one error in %s' % field)
        self.assertIsInstance(ed_items[field][0], ValidationError, 'The raised ValidationError has a non-list object in'
                                                                   ' %s' % field)
        return ed_items[field][0]

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
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'empty-wfspec',
                                   'name': 'Empty Workflow Spec',
                                   'description': 'This empty workflow spec shall not pass'})
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowSpecHasNoMainCourse.CODE, 'Invalid subclass of ValidationError '
                                                                                'raised')

    def test_single_main_course_is_good(self):
        try:
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wfspec',
                                   'name': 'Workflow Spec',
                                   'description': 'This workflow spec shall pass',
                                   'create_permission': '',
                                   'cancel_permission': '',
                                   'courses': [{
                                       'code': '',
                                       'name': 'Single',
                                       'description': 'The only defined course',
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
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'exit',
                                           'name': 'Initial transition',
                                           'description': 'The initial and only transition',
                                           'permission': 'sample.start_task',
                                       }]
                                   }]})
            self.assertTrue(True)
        except Exception as e:
            self.assertFalse(True, 'An exception was raised (%s): %s' % (type(e).__name__, e))

    def test_cyclical_course_dependencies_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wfspec',
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
                                           'description': 'Parallel brancher',
                                           'branches': ['foo', 'bar']
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
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'parallel-1',
                                           'name': 'Initial transition',
                                           'description': 'The initial transition',
                                           'permission': 'sample.start_task',
                                       }, {
                                           'origin': 'parallel-1',
                                           'action_name': 'escape',
                                           'destination': 'exit',
                                           'name': 'Final transition',
                                           'description': 'The final transition',
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
                                           'type': NodeSpec.SPLIT,
                                           'code': 'bad-parallel',
                                           'name': 'Bad-Parallel',
                                           'description': 'Bad parallel brancher',
                                           'branches': ['foo', 'bar']
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
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'bad-parallel',
                                           'name': 'Initial transition',
                                           'description': 'The initial transition',
                                           'permission': 'sample.start_task',
                                       }, {
                                           'origin': 'bad-parallel',
                                           'action_name': 'escape',
                                           'destination': 'exit',
                                           'name': 'Final transition',
                                           'description': 'The final transition',
                                       }]
                                   }]})
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
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wfspec',
                                   'name': 'Workflow Spec',
                                   'description': 'This workflow spec shall not pass',
                                   'create_permission': '',
                                   'cancel_permission': '',
                                   'courses': [{
                                       'code': '',
                                       'name': 'Single',
                                       'description': 'The only defined course',
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
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'exit',
                                           'name': 'Initial transition',
                                           'description': 'The initial and only transition',
                                           'permission': 'sample.start_task',
                                       }]
                                   }]})
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasNoRequiredNode.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_multi_cancel_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wfspec',
                                   'name': 'Workflow Spec',
                                   'description': 'This workflow spec shall not pass',
                                   'create_permission': '',
                                   'cancel_permission': '',
                                   'courses': [{
                                       'code': '',
                                       'name': 'Single',
                                       'description': 'The only defined course',
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
                                           'type': NodeSpec.CANCEL,
                                           'code': 'cancel-2',
                                           'name': 'Cancel 2',
                                           'description': 'Another cancel node',
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'exit',
                                           'name': 'Initial transition',
                                           'description': 'The initial and only transition',
                                           'permission': 'sample.start_task',
                                       }]
                                   }]})
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecMultipleRequiredNodes.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_no_enter_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wfspec',
                                   'name': 'Workflow Spec',
                                   'description': 'This workflow spec shall not pass',
                                   'create_permission': '',
                                   'cancel_permission': '',
                                   'courses': [{
                                       'code': '',
                                       'name': 'Single',
                                       'description': 'The only defined course',
                                       'nodes': [{
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
                                       }],
                                       'transitions': []
                                   }]})
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasNoRequiredNode.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_multi_enter_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wfspec',
                                   'name': 'Workflow Spec',
                                   'description': 'This workflow spec shall not pass',
                                   'create_permission': '',
                                   'cancel_permission': '',
                                   'courses': [{
                                       'code': '',
                                       'name': 'Single',
                                       'description': 'The only defined course',
                                       'nodes': [{
                                           'type': NodeSpec.ENTER,
                                           'code': 'origin',
                                           'name': 'Origin',
                                           'description': 'The origin node'
                                       }, {
                                           'type': NodeSpec.ENTER,
                                           'code': 'origin-2',
                                           'name': 'Origin-2',
                                           'description': 'Another origin node'
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
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'exit',
                                           'name': 'Initial transition',
                                           'description': 'The initial and only transition',
                                           'permission': 'sample.start_task',
                                       }]
                                   }]})
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecMultipleRequiredNodes.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_no_exit_node_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wfspec',
                                   'name': 'Workflow Spec',
                                   'description': 'This workflow spec shall not pass',
                                   'create_permission': '',
                                   'cancel_permission': '',
                                   'courses': [{
                                       'code': '',
                                       'name': 'Single',
                                       'description': 'The only defined course',
                                       'nodes': [{
                                           'type': NodeSpec.ENTER,
                                           'code': 'origin',
                                           'name': 'Origin',
                                           'description': 'The origin node'
                                       }, {
                                           'type': NodeSpec.CANCEL,
                                           'code': 'cancel',
                                           'name': 'Cancel',
                                           'description': 'The cancel node',
                                       }],
                                       'transitions': []
                                   }]})
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasNoRequiredNode.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_no_joined_node_when_caller_uses_joiner_is_bad(self):
        with self.assertRaises(exceptions.WorkflowInvalidState) as ar:
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'wfspec',
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
                                       }],
                                       'transitions': [{
                                           'origin': 'origin',
                                           'destination': 'exit',
                                           'name': 'Initial transition',
                                           'description': 'The initial transition',
                                           'permission': 'sample.start_task',
                                       }]
                                   }]})
        exc = self.unwrapValidationError(ar.exception)
        self.assertEqual(exc.code, exceptions.WorkflowCourseSpecHasNoRequiredNode.CODE,
                         'Invalid subclass of ValidationError raised')
