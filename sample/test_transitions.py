from django.core.exceptions import ValidationError
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec
from arcanelab.ouroboros import exceptions
from .support import ValidationErrorWrappingTestCase


##########################################
# TransitionSpec tests
##########################################


class TransitionSpecTestCase(ValidationErrorWrappingTestCase):
    pass