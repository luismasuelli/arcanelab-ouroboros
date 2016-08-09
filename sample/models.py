from django.db import models
from permission.logics import PermissionLogic
from permission import add_permission_logic
from arcanelab.ouroboros.models import Document
from django.conf import settings


"""
Our testing will involve the following example:

1. `Area` will be a management area in a company, which will have:
   a. A head which can create, edit, cancel, review, accept completion, and reject completion of tasks.

2. `Task` will be a task created for an area by its head, and will involve:
   a. Who will perform it. It can start it, abort it (because disputing it), and mark it as completed.
   b. Who will review it, abort it (for an additional review), and either accept/reject completion.
   c. Who will audit it. This task is parallel to the performer starting the task and will involve a
      single step telling the effort/cost this task will involve.
   d. Who will invoice it. This step will be effective only if the task is accepted, and will be discarded
      -if done- when the task is rejected or either branch is cancelled.
   e. Who will deliver it, for deliverable task results.
   f. Who will attend its pick, for non-deliverable task results.

                +--------------------------------------------------------------------------------+
                |                           +----------------------------------------------------+
                v                           v                                         +---> rejected
created ---> reviewed ---> assigned ---> started ---> completed +--> pending approval +--> approved +--+---> ...
                                                             |  +--> pending audit ------> audited  +  |
                                                             +-----> pending invoice ----> invoiced ---+

... +--> was service? -----------------------------------+--> notify --> delivered
    +--> was deliverable? ---> pending delivery ---------+
    +--> otherwise ----------> pending customer pick ----+
"""


class Area(models.Model):
    """
    A management area.
    """

    head = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=False, blank=False)


class Task(Document):
    """
    A task in a management area.
    """

    TYPES = (
        ('service', 'Service'),
        ('deliverable', 'Deliverable'),
        ('non-deliverable', 'Non-Deliverable')
    )

    area = models.ForeignKey(Area, null=False, blank=False, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=20, choices=TYPES, null=False, blank=False)
    performer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=False, blank=False, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=False, blank=False, on_delete=models.CASCADE)
    accountant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=False, blank=False, on_delete=models.CASCADE)
    auditor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=False, blank=False, on_delete=models.CASCADE)
    dispatcher = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=False, blank=False, on_delete=models.CASCADE)
    attendant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', null=False, blank=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=False, blank=False)
    content = models.TextField(max_length=2000, null=False, blank=False)
    invoice = models.CharField(max_length=20, null=True, blank=True)
    auditory = models.TextField(max_length=3000, null=True, blank=True)

    class Meta:
        permissions = (
            ('cancel_task', 'Cancel Task'),
            ('create_task', 'Create Task'),
            ('review_task', 'Review Task'),
            ('accept_task', 'Accept Task'),
            ('reject_task', 'Reject Task'),
            ('start_task', 'Start Task'),
            ('abort_task', 'Abort Task'),
            ('complete_task', 'Complete Task'),
            ('invoice_task', 'Invoice Task'),
            ('audit_task', 'Audit Task'),
            ('deliver_task', 'Deliver Task'),
            ('pick_attend_task', 'Pick-Attend Task'),
        )


class TaskPermissionLogic(PermissionLogic):

    def has_perm(self, user_obj, perm, obj=None):
        cancel = self.get_full_permission_string('cancel')
        create = self.get_full_permission_string('create')
        review = self.get_full_permission_string('review')
        accept = self.get_full_permission_string('accept')
        reject = self.get_full_permission_string('reject')
        start = self.get_full_permission_string('start')
        abort = self.get_full_permission_string('abort')
        complete = self.get_full_permission_string('complete')
        audit = self.get_full_permission_string('audit')
        invoice = self.get_full_permission_string('invoice')
        deliver = self.get_full_permission_string('deliver')
        pick_attend = self.get_full_permission_string('pick_attend')

        if obj is None:
            return False

        if user_obj.is_superuser:
            return True

        if perm in (create, cancel):
            return user_obj == obj.area.head
        elif perm in (review, accept, reject):
            return user_obj in (obj.reviewer, obj.area.head)
        elif perm == abort:
            return user_obj in (obj.reviewer, obj.area.head, obj.performer)
        if perm in (start, complete):
            return user_obj == obj.performer
        elif perm == invoice:
            return user_obj == obj.accountant
        elif perm == audit:
            return user_obj == obj.auditor
        elif perm == pick_attend:
            return user_obj == obj.attendant
        elif perm == deliver:
            return user_obj == obj.dispatcher
        return False


add_permission_logic(Task, TaskPermissionLogic())
