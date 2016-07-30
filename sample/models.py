from django.db import models
from permission.logics import PermissionLogic
from permission import add_permission_logic
from arcanelab.ouroboros.models import Document
from django.conf import settings


class SampleDocument(Document):
    """
    A document which expects interaction with three users.
    The document has name, description, and content to edit.
    """

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    collaborator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=255)
    content = models.TextField(max_length=2 ** 20 - 1)
    rating = models.PositiveSmallIntegerField(choices=tuple((str(x), x) for x in range(1, 6)), null=True, blank=True)

    class Meta:
        permissions = (
            ('modify_sampledocument', 'Modify SampleDocument'),
            ('review_sampledocument', 'Review SampleDocument'),
            ('cancel_sampledocument', 'Cancel SampleDocument'),
        )


class SamplePermissionLogic(PermissionLogic):

    def has_perm(self, user_obj, perm, obj=None):
        modify = self.get_full_permission_string('modify')
        review = self.get_full_permission_string('review')
        cancel = self.get_full_permission_string('cancel')

        if obj is None:
            return False

        if user_obj.is_superuser:
            return True

        if perm == modify:
            return user_obj in (obj.creator, obj.collaborator)
        elif perm == cancel:
            return user_obj == obj.creator
        elif perm == review:
            return user_obj == obj.reviewer
        return False


add_permission_logic(SampleDocument, SamplePermissionLogic())
