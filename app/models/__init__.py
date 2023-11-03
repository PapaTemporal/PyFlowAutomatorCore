# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

from typing import Any
from pydantic import BaseModel


class Edge(BaseModel, extra="allow"):
    id: str
    source: str
    sourceHandle: int | str | None = None
    target: str
    targetHandle: int | str


class NodeData(BaseModel, extra="allow"):
    function: str | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None
    next_function: int | str | None = None


class Node(BaseModel, extra="allow"):
    id: str
    type: str
    data: NodeData

    @property
    def func(self):
        return self.data.function

    @property
    def next(self):
        return self.data.next_function

    @property
    def args(self):
        return self.data.args

    @property
    def kwargs(self):
        return self.data.kwargs


class Flow(BaseModel):
    id: str | None = None
    name: str | None = None
    variables: dict[str, Any]
    edges: list[Edge]
    nodes: list[Node]
    start_id: str | None = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        if data.get("start_id"):
            self.start_id = data["start_id"]
        else:
            for edge in data["edges"]:
                if edge["sourceHandle"] == "start":
                    self.start_id = edge["target"]
                    break
        if not self.start_id:
            raise ValueError("No start node found.")

    @property
    def exec_edges(self) -> list[Edge]:
        return [
            edge
            for edge in self.edges
            if edge.sourceHandle == "e-out" and edge.targetHandle == "e-in"
        ]

    @property
    def except_edges(self) -> list[Edge]:
        return [
            edge
            for edge in self.edges
            if edge.sourceHandle != "e-out" and edge.targetHandle == "e-in"
        ]

    @property
    def arg_edges(self) -> list[Edge]:
        return [
            edge
            for edge in self.edges
            if isinstance(edge.targetHandle, int) or edge.targetHandle.isdigit()
        ]

    @property
    def kwarg_edges(self) -> list[Edge]:
        return [
            edge
            for edge in self.edges
            if not isinstance(edge.targetHandle, int)
            and edge.targetHandle != "e-in"
            and not edge.targetHandle.isdigit()
        ]

    def get_node(self, node_id: str) -> Node:
        for node in self.nodes:
            if node.id == node_id:
                node.data.next_function = next(
                    (edge.target for edge in self.exec_edges if edge.source == node_id),
                    None,
                )
                return node

    def get_except_edges_by_source(self, edge_id: str) -> list[Edge]:
        edges = []
        for edge in self.except_edges:
            if edge.source == edge_id:
                edges.append(edge)
        return edges

    def get_arg_edges_by_target(self, edge_id: str) -> list[Edge]:
        edges = []
        for edge in self.arg_edges:
            if edge.target == edge_id:
                edge.targetHandle = int(edge.targetHandle)
                edges.append(edge)
        return edges

    def get_kwarg_edges_by_target(self, edge_id: str) -> list[Edge]:
        edges = []
        for edge in self.kwarg_edges:
            if edge.target == edge_id:
                edges.append(edge)
        return edges
