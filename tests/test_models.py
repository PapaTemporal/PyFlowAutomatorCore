import pytest
from app.models import Flow
from tests.test_constants import (
    sample_flow,
    exec_edges,
    except_edges,
    arg_edges,
    kwarg_edges,
)


def test_flow():
    flow = Flow(**sample_flow)

    assert flow.start_id == "93043"
    assert [e.model_dump() for e in flow.exec_edges] == exec_edges
    assert [e.model_dump() for e in flow.except_edges] == except_edges
    assert [e.model_dump() for e in flow.arg_edges] == arg_edges
    assert [e.model_dump() for e in flow.kwarg_edges] == kwarg_edges


def test_get_start_node_error():
    with pytest.raises(ValueError):
        Flow(
            **{
                "nodes": [
                    {
                        "id": "1",
                        "type": "whateva",
                        "data": {"function": "operator.add", "args": [1, 1]},
                    }
                ],
                "edges": [],
                "variables": {},
            }
        )


def test_get_node():
    flow = Flow(**sample_flow)
    node = flow.get_node("72374")
    assert node.id == "72374"
    assert node.data.function == "custom.extract_json"
    assert node.data.kwargs == {"expression": "$.name"}
    assert node.data.next_function == "51034"


def test_get_node_not_found():
    flow = Flow(**sample_flow)
    assert not flow.get_node("not_found")  # returns None


def test_get_next_node():
    flow = Flow(**sample_flow)
    node = flow.get_node("72374")
    assert node.next == "51034"


def test_get_next_node_not_found():
    tmp_sample_flow = sample_flow.copy()
    tmp_sample_flow["edges"] = [
        edge for edge in tmp_sample_flow["edges"] if edge["target"] != "51034"
    ]
    flow = Flow(**tmp_sample_flow)
    node = flow.get_node("72374")
    assert not node.next  # returns None


def test_get_except_edges_by_source():
    flow = Flow(**sample_flow)
    except_edge = flow.get_except_edges_by_source("77775")[0]
    assert except_edge.id == "xyflow__edge-77775next_function-72374e-in"


def test_get_except_edges_by_source_not_found():
    flow = Flow(**sample_flow)
    assert not flow.get_except_edges_by_source("not_found")  # returns None


def test_get_arg_edges_by_target():
    flow = Flow(**sample_flow)
    arg_edge = flow.get_arg_edges_by_target("77638")[0]
    assert arg_edge.id == "xyflow__edge-85893name-776381"


def test_get_kwarg_edges_by_target():
    flow = Flow(**sample_flow)
    kwarg_edge = flow.get_kwarg_edges_by_target("59697")[0]
    assert kwarg_edge.id == "xyflow__edge-88179__ignore__-59697condition"
