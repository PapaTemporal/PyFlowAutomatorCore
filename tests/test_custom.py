import pytest
from app.models import Flow
from app.utils import Process
from app.utils.exceptions import (
    BranchError,
    JSONExtractionError,
    ForEachError,
    SequenceError,
)
from tests.test_constants import (
    sample_branch_flow,
    sample_foreach_flow,
    sample_sequence_flow,
)
from app.utils.custom import branch, extract_json, for_each, sequence, set_variable


def test_branch_true():
    process = Process(Flow(**sample_branch_flow))
    result = branch(process, "1", True, "2", "3")
    assert result == "2"
    assert process._flow.nodes[0].data.next_function == "2"


def test_branch_false():
    process = Process(Flow(**sample_branch_flow))
    result = branch(process, "1", False, "2", "3")
    assert result == "3"
    assert process._flow.nodes[0].data.next_function == "3"


def test_branch_error():
    process = Process(Flow(**sample_branch_flow))
    with pytest.raises(BranchError):
        branch(process, "12", "True", "2", "3")

    with pytest.raises(BranchError):
        branch(process, "1", [1], "2", "3")

    with pytest.raises(BranchError):
        branch(process, "1", {"a": "b"}, "2", "3")


def test_extract_json_success():
    result = extract_json(None, "1", {"a": {"b": {"c": 1}}}, "$.a.b.c")
    assert result == 1


def test_extract_json_multiple_values():
    result = extract_json(None, "1", {"a": {"b": {"c": 1}}, "d": {"e": 2}}, "$..*")
    assert result == [{"b": {"c": 1}}, {"e": 2}, {"c": 1}, 1, 2]


def test_extract_json_error():
    with pytest.raises(JSONExtractionError):
        extract_json(None, "1", "mello yellow", "$..f")


def test_for_each_success():
    process = Process(Flow(**sample_foreach_flow))
    result = for_each(process, "1", [1, 2, 3], "2")
    assert result == "Completed"
    assert process._variables == {
        "test": "success",
        "1__0": {"1": 1, "2": 3, "3": "success"},
        "1__1": {"1": 2, "2": 6, "3": "success"},
        "1__2": {"1": 3, "2": 9, "3": "success"},
    }


def test_for_each_error():
    process = Process(Flow(**sample_foreach_flow))
    with pytest.raises(ForEachError):
        for_each(process, "1", "1", "2")


def test_sequence_success():
    process = Process(Flow(**sample_sequence_flow))
    result = sequence(process, "1", ["2", "3"])
    assert result == "Completed"
    assert process._variables == {"1": None, "2": 3, "3": 9}


def test_sequence_error():
    process = Process(Flow(**sample_foreach_flow))
    with pytest.raises(SequenceError):
        sequence(process, "1", "1")


def test_set_variable_success():
    process = Process(Flow(**sample_foreach_flow))
    set_variable(process, None, "my_var", "my_value")
    assert process._variables == {"my_var": "my_value", "test": "test"}
