# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import json
from typing import Any
from requests import Response
from app.utils.exceptions import (
    ArgumentError,
    FunctionCallError,
    FunctionRunError,
    KeywordArgumentError,
    ProcessRunError,
    InvalidFunction,
    SetExceptionsError,
)

from app.models import Flow, Node


class Process:
    def __init__(self, flow: Flow, allow_list: list = [], debug: bool = False):
        self._flow = flow
        self._variables = self._flow.variables.copy()
        self._allow_list = allow_list
        self._debug = debug

    def run(self):
        try:
            self._run_function(self._flow.start_id)
            return self._variables
        except Exception as e:
            raise ProcessRunError(
                json.loads(
                    json.dumps(
                        {
                            "error": repr(e),
                            "dump": {
                                "flow": self._flow.model_dump(),
                                "variables": self._variables,
                            },
                        },
                        default=lambda o: repr(o),
                        indent=4,
                    )
                )
            )

    def _run_function(self, function_id: str):
        try:
            node = self._flow.get_node(function_id)
            if self._allow_list:
                if node.func not in self._allow_list:
                    raise InvalidFunction(
                        f"Function {node.type} not in allow list {self._allow_list}"
                    )

            self._set_exceptions(function_id, node)
            args = self._get_args(function_id, node)
            kwargs = self._get_kwargs(function_id, node)
            response = self._call_function(function_id, node.func, args, kwargs)
            if isinstance(response, Response):
                response.raise_for_status()
                self._variables[function_id] = response.json() or response.text
            else:
                self._variables[function_id] = response
            if next_action := node.next:
                self._run_function(next_action)
        except Exception as e:
            raise FunctionRunError(e)

    def _get_args(self, function_id: str, node: Node):
        try:
            args = (
                [self, function_id]
                if node.func and node.func.startswith("custom.")
                else []
            )
            args.extend(node.args or [])
            for edge in self._flow.get_arg_edges_by_target(function_id):
                if (
                    edge.sourceHandle
                    and edge.sourceHandle != "__ignore__"
                    and edge.sourceHandle in self._variables
                ):
                    args[edge.targetHandle] = self._variables[edge.sourceHandle]
                    continue

                if edge.source not in self._variables:
                    self._run_function(edge.source)

                args[edge.targetHandle] = self._variables[edge.source]
            return args
        except Exception as e:
            raise ArgumentError(e)

    def _get_kwargs(self, function_id: str, node: Node):
        try:
            kwargs = node.kwargs or {}
            for edge in self._flow.get_kwarg_edges_by_target(function_id):
                if (
                    edge.sourceHandle
                    and edge.sourceHandle != "__ignore__"
                    and edge.sourceHandle in self._variables
                ):
                    kwargs[edge.targetHandle] = self._variables[edge.sourceHandle]
                    continue

                if edge.source not in self._variables:
                    self._run_function(edge.source)

                kwargs[edge.targetHandle] = self._variables[edge.source]
            return kwargs
        except Exception as e:
            raise KeywordArgumentError(e)

    def _set_exceptions(self, function_id: str, node: Node):
        try:
            for edge in self._flow.get_except_edges_by_source(function_id):
                if not node.kwargs:
                    node.data.kwargs = {}
                node.kwargs[edge.sourceHandle] = edge.target
        except Exception as e:
            raise SetExceptionsError(e)

    def _call_function(
        self, function_id: str, function: str, args: list[Any], kwargs: dict[str, Any]
    ):
        try:
            module_name, func_name = function.rsplit(".", 1)
            if module_name == "custom":
                module_name = "app.utils.custom"
            if self._debug:
                print(
                    f"Calling {function_id}:{func_name} with args: {args} and kwargs: {str(kwargs)[0:100]}"
                )
            module = __import__(module_name, fromlist=[func_name])
            func = getattr(module, func_name)
            return func(*args, **kwargs)
        except Exception as e:
            raise FunctionCallError(e)
