from django.core.exceptions import ValidationError
from arcanelab.ouroboros.executors import Workflow
from arcanelab.ouroboros.models import NodeSpec, WorkflowSpec, CourseSpec
from arcanelab.ouroboros import exceptions
from .support import ValidationErrorWrappingTestCase


# TODO transition-spec

# TODO check on instances

# TODO check on runs

##########################################
# NodeSpec tests
##########################################

class NodeSpecTestCase(ValidationErrorWrappingTestCase):

    # testing enter node
    # TODO actually make them! right now they are only empty stubs

    def test_enter_node_with_inbounds_is_bad(self):
        pass

    def test_enter_node_without_outbounds_is_bad(self):
        pass

    def test_enter_node_wit_many_outbounds_is_bad(self):
        pass

    def test_enter_node_with_exit_value_is_bad(self):
        pass

    def test_enter_node_with_joiner_is_bad(self):
        pass

    def test_enter_node_with_branches_is_bad(self):
        pass

    def test_enter_node_with_execute_permission_is_bad(self):
        pass

    # testing exit node

    def test_exit_node_with_outbounds_is_bad(self):
        pass

    def test_exit_node_without_inbounds_is_bad(self):
        pass

    def test_exit_node_with_branches_is_bad(self):
        pass

    def test_exit_node_with_execute_permission_is_bad(self):
        pass

    def test_exit_node_with_joiner_is_bad(self):
        pass

    def test_exit_node_without_exit_value_is_bad(self):
        pass

    # testing cancel node

    def test_cancel_node_with_inbounds_is_bad(self):
        pass

    def test_cancel_node_with_outbounds_is_bad(self):
        pass

    def test_cancel_node_with_branches_is_bad(self):
        pass

    def test_cancel_node_with_exit_value_is_bad(self):
        pass

    def test_cancel_node_with_joiner_is_bad(self):
        pass

    def test_cancel_node_with_execute_permission_is_bad(self):
        pass

    # testing joined node

    def test_joined_node_with_inbounds_is_bad(self):
        pass

    def test_joined_node_with_outbounds_is_bad(self):
        pass

    def test_joined_node_with_branches_is_bad(self):
        pass

    def test_joined_node_with_exit_value_is_bad(self):
        pass

    def test_joined_node_with_joiner_is_bad(self):
        pass

    def test_joined_node_with_execute_permission_is_bad(self):
        pass

    # testing split node

    def test_split_node_without_inbounds_is_bad(self):
        pass

    def test_split_node_without_outbounds_is_bad(self):
        pass

    def test_split_node_without_branches_is_bad(self):
        pass

    def test_split_node_with_one_branch_is_bad(self):
        pass

    def test_split_node_with_branches_in_other_workflow_is_bad(self):
        pass

    def test_split_node_with_one_outbound_and_joiner_is_bad(self):
        pass

    def test_split_node_with_many_outbounds_and_no_joiner_is_bad(self):
        pass

    def test_split_node_with_exit_value_is_bad(self):
        pass

    def test_split_node_with_execute_permission_is_bad(self):
        pass

    # testing step node

    def test_step_node_without_inbounds_is_bad(self):
        pass

    def test_step_node_with_no_outbounds_is_bad(self):
        pass

    def test_step_node_with_many_outbounds_is_bad(self):
        pass

    def test_step_node_with_branches_is_bad(self):
        pass

    def test_step_node_with_exit_value_is_bad(self):
        pass

    def test_step_node_with_joiner_is_bad(self):
        pass

    def test_step_node_with_execute_permission_is_bad(self):
        pass

    # testing multiplexer node

    def test_multiplexer_node_with_no_inbounds_is_bad(self):
        pass

    def test_multiplexer_node_with_no_outbounds_is_bad(self):
        pass

    def test_multiplexer_node_with_one_outbound_is_bad(self):
        pass

    def test_multiplexer_node_with_branches_is_bad(self):
        pass

    def test_multiplexer_node_with_execute_permission_is_bad(self):
        pass

    def test_multiplexer_node_with_joiner_is_bad(self):
        pass

    def test_multiplexer_node_with_exit_value_is_bad(self):
        pass

    # testing input node

    def test_input_node_with_no_inbounds_is_bad(self):
        pass

    def test_input_node_with_no_outbounds_is_bad(self):
        pass

    def test_input_node_with_branches_is_bad(self):
        pass

    def test_input_node_with_execute_permission_is_bad(self):
        pass

    def test_input_node_with_joiner_is_bad(self):
        pass

    def test_input_node_with_exit_value_is_bad(self):
        pass

##########################################
# TransitionSpec tests
##########################################

class TransitionSpecTestCase(ValidationErrorWrappingTestCase):

    pass
