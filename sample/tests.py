from django.core.exceptions import ValidationError
from django.test import TestCase
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec
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

############################################
# WorkflowSpec tests
############################################

class WorkflowSpecTestCase(TestCase):

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
        ed_items = ar.exception.error_dict
        self.assertEqual(len(ed_items), 1, 'The raised ValidationError produces an invalid count of errors (expected 1)')
        self.assertIn('__all__', ed_items, 'The raised ValidationError produces errors for other fields than __all__')
        self.assertIsInstance(ed_items['__all__'], list, 'The raised ValidationError has a non-list object in __all__')
        self.assertEqual(len(ed_items['__all__']), 1, 'The raised ValidationError has more than one error in __all__')
        self.assertIsInstance(ed_items['__all__'][0], ValidationError, 'The raised ValidationError has a non-list '
                                                                       'object in __all__')
        self.assertEqual(ed_items['__all__'][0].code, exceptions.WorkflowSpecHasNoMainCourse.CODE,
                         'Invalid subclass of ValidationError raised')

    def test_single_main_course_is_good(self):
        try:
            Workflow.Spec.install({'model': 'sample.Task',
                                   'code': 'empty-wfspec',
                                   'name': 'Empty Workflow Spec',
                                   'description': 'This empty workflow spec shall not pass',
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

    def test_multiple_main_courses_is_bad(self):
        self.assertTrue(True, 'not yet implemented')

    def test_cyclical_course_dependencies_is_bad(self):
        self.assertTrue(True, 'not yet implemented')
