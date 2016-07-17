###################################################################################
#                                                                                 #
# Workflow logic will be coded here, just to get rid of dirty code in the models. #
#                                                                                 #
###################################################################################

from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from cantrips.iteration import iterable
from . import exceptions, models

class WorkflowExecutor(object):

    class CourseHelpers(object):

        @classmethod
        def _check_status(cls, course_instance, types, invert=False):
            try:
                return (course_instance.node.type in iterable(types)) ^ bool(invert)
            except models.NodeInstance.DoesNotExist:
                return bool(invert)

        @classmethod
        def is_pending(cls, course_instance):
            return cls._check_status(course_instance, (), True)

        @classmethod
        def is_waiting(cls, course_instance):
            return cls._check_status(course_instance, models.Node.INPUT)

        @classmethod
        def is_cancelled(cls, course_instance):
            return cls._check_status(course_instance, models.Node.CANCEL)

        @classmethod
        def is_ended(cls, course_instance):
            return cls._check_status(course_instance, models.Node.EXIT)

        @classmethod
        def is_splitting(cls, course_instance):
            return cls._check_status(course_instance, models.Node.SPLIT)

        @classmethod
        def is_joined(cls, course_instance):
            return cls._check_status(course_instance, models.Node.JOINED)

        @classmethod
        def is_terminated(cls, course_instance):
            return cls._check_status(course_instance, (models.Node.JOINED, models.Node.EXIT, models.Node.CANCEL))

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
