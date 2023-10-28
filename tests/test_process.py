import pytest
from app.utils import Process
from app.models import Flow
from app.utils.exceptions import ProcessRunError, FunctionRunError
from tests.test_constants import sample_flow, sample_two_flow, sample_fail_flow


def test_process():
    process = Process(Flow(**sample_flow))

    assert process._flow == Flow(**sample_flow)
    assert process._variables == sample_flow["variables"]
    assert process._allow_list == []
    assert process._debug == False


def test_real_process():
    process = Process(
        Flow(**sample_flow),
        allow_list=[
            "requests.get",
            "custom.extract_json",
            "custom.for_each",
            "custom.branch",
            "custom.set_variable",
            "operator.or_",
            "operator.contains",
            "builtins.print",
        ],
        debug=True,
    )
    process.run()


def test_process_not_allowed():
    with pytest.raises(ProcessRunError):
        Process(
            Flow(**sample_two_flow),
            allow_list=[
                "requests.get",
                "custom.extract_json",
                "custom.for_each",
                "custom.branch",
                "custom.set_variable",
                "operator.or_",
                "operator.contains",
            ],
        ).run()


def test_process_run_success():
    process = Process(Flow(**sample_two_flow))
    result = process.run()
    assert result == {"1": 3, "2": 9}


def test_process_run_fail():
    process = Process(Flow(**sample_fail_flow))
    with pytest.raises(ProcessRunError):
        process.run()


def test_process_run_function():
    process = Process(Flow(**sample_two_flow))
    process._run_function("2")
    assert process._variables == {"1": 3, "2": 9}


def test_process_run_function_fail():
    process = Process(Flow(**sample_two_flow))
    with pytest.raises(FunctionRunError):
        process._run_function("3")


def test_process_get_args():
    process = Process(Flow(**sample_two_flow))
    node = process._flow.get_node("2")
    args = process._get_args("2", node)
    assert args == [3, 3]


def test_process_get_kwargs():
    process = Process(Flow(**sample_two_flow))
    node = process._flow.get_node("2")
    kwargs = process._get_kwargs("2", node)
    assert kwargs == {}


def test_process_set_exceptions():
    process = Process(Flow(**sample_flow))
    node = process._flow.get_node("77775")
    process._set_exceptions("77775", node)
    assert node.kwargs["next_function"] == "72374"


def test_process_call_function():
    process = Process(Flow(**sample_two_flow))
    response = process._call_function("2", "operator.add", [3, 3], {})
    assert response == 6
