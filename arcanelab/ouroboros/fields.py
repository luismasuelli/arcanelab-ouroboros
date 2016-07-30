from django.db.models.fields import CharField
from .support import CallableReference


class CallableReferenceField(CharField):
    """
    It is like a charfield EXCEPT it handles references to CallableReference.
    """

    def __init__(self, *args, **kwargs):
        if len(args) >= 4:
            args = args[:3] + (255,) + args[4:]
        else:
            kwargs['max_length'] = 255
        super(CallableReferenceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        return value if isinstance(value, CallableReference) else CallableReference(path=value)

    def from_db_value(self, value, expression, connection, context):
        return value and CallableReference(path=value)

    def get_prep_value(self, value):
        return value and value.path