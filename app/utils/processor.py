# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import time
import json
import inspect
import asyncio
from typing import Any, Callable
from requests import Response
from app.utils.exceptions import (
    ArgumentError,
    FunctionCallError,
    FunctionRunError,
    KeywordArgumentError,
    ProcessRunError,
    InvalidFunction,
    SetExceptionsError,
    BranchError,
    ForEachError,
    SequenceError,
    JSONExtractionError,
)

from app.models import Flow, Node

custom_functions = [
    "branch",
    "for_each",
    "sequence",
    "set_variable",
]


class Process:
    def __init__(
        self,
        flow: Flow,
        debug: bool = False,
        update: Callable[[dict[str, Any]], None] = None,
        allow_list: list = None,
    ):
        self._flow = flow
        self._update = update
        self._debug = debug
        self._variables = self._flow.variables.copy()
        self._allow_list = allow_list.extend(custom_functions) if allow_list else None

    def print(self, message: str):
        if self._debug:
            print(message)

    async def run(self):
        try:
            await self._run_function(self._flow.start_id)
            return self._variables
        except Exception as e:
            if self._update:
                await self._update(f"ERROR: {repr(e)}")
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

    async def _run_function(self, function_id: str):
        try:
            # need to sleep so there is time to send the update to the client before the next function is called
            await asyncio.sleep(0.1)
            node = self._flow.get_node(function_id)
            if self._allow_list:
                if node.func not in self._allow_list:
                    raise InvalidFunction(
                        f"Function {node.type} not in allow list {self._allow_list}"
                    )

            self._set_exceptions(function_id, node)
            args = await self._get_args(function_id, node)
            kwargs = await self._get_kwargs(function_id, node)
            response, duration = await self._call_function(
                function_id, node.func, args, kwargs
            )

            if isinstance(response, Response):
                response.raise_for_status()
                response = response.json() or response.text

            self.print(f"Response: {response}")

            self._variables[function_id] = response

            if self._update:
                message = {
                    "function_id": function_id,
                    "function_name": node.func,
                    "duration": f"{duration * 1000000:.2f}μs"
                    if duration < 0.001
                    else (
                        f"{duration * 1000:.2f}ms"
                        if duration < 1
                        else f"{duration:.2f}s"
                    ),
                    "response": response,
                }
                await self._update(message)

            if next_action := node.next:
                await self._run_function(next_action)

        except (
            FunctionCallError,
            ArgumentError,
            KeywordArgumentError,
            SetExceptionsError,
            InvalidFunction,
            ModuleNotFoundError,
            BranchError,
            ForEachError,
            SequenceError,
            JSONExtractionError,
        ):
            raise
        except Exception as e:
            raise FunctionRunError(e)

    async def _get_args(self, function_id: str, node: Node):
        try:
            args = node.args or []
            for edge in self._flow.get_arg_edges_by_target(function_id):
                if (
                    edge.sourceHandle
                    and edge.sourceHandle != "__ignore__"
                    and edge.sourceHandle in self._variables
                ):
                    args[edge.targetHandle] = self._variables[edge.sourceHandle]
                    continue

                if edge.source not in self._variables:
                    await self._run_function(edge.source)

                args[edge.targetHandle] = self._variables[edge.source]
            return args
        except Exception as e:
            raise ArgumentError(e)

    async def _get_kwargs(self, function_id: str, node: Node):
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
                    await self._run_function(edge.source)

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

    async def _call_function(
        self, function_id: str, function: str, args: list[Any], kwargs: dict[str, Any]
    ):
        try:
            if function in custom_functions:
                func_name = function
                func = getattr(self, function)
                args.insert(0, function_id)
            else:
                module_name, func_name = function.rsplit(".", 1)
                if module_name == "custom":
                    module_name = "app.custom"
                module = __import__(module_name, fromlist=[func_name])
                func = getattr(module, func_name)

            self.print(
                f"Calling {function_id}:{func_name} with args: {args} and kwargs: {str(kwargs)[0:100]}"
            )

            if inspect.iscoroutinefunction(func):
                start = time.time()
                r = await func(*args, **kwargs)
                return r, time.time() - start
            else:
                start = time.time()
                r = func(*args, **kwargs)
                return r, time.time() - start
        except (
            ModuleNotFoundError,
            BranchError,
            ForEachError,
            SequenceError,
            JSONExtractionError,
        ):
            raise
        except Exception as e:
            raise FunctionCallError(e)

    # these are custom functions that need to use self because they will modify the class instance
    # the action id is passed to all of these functions whether needed or not to simplify the way
    # they are called

    def branch(
        self, action_id: str, condition: bool, true: str = None, false: str = None
    ) -> str:
        try:
            node = self._flow.get_node(action_id)

            if not isinstance(condition, bool):
                raise ValueError("Condition must be a boolean")

            if condition:
                node.data.next_function = true
                return node.data.next_function

            node.data.next_function = false
            return node.data.next_function
        except Exception as e:
            raise BranchError(f"Unable to process branch: {e}")

    async def for_each(
        self,
        action_id: str,
        array: list,
        next_function: str,
    ):
        try:
            if not isinstance(array, list):
                raise ValueError("array must be a list")

            global_variable_keys = [k for k in self._variables.keys() if "__" not in k]
            original_globals = {k: self._variables[k] for k in global_variable_keys}
            iteration_results = {}

            for index, item in enumerate(array):
                self._variables = original_globals.copy()
                self._variables[action_id] = item
                await self._run_function(next_function)
                local_variables = self._variables.copy()
                iteration_results.update(
                    {
                        f"{action_id}__{index}": {
                            k: v
                            for k, v in local_variables.items()
                            if k not in global_variable_keys
                        }
                    }
                )
                original_globals.update(
                    {
                        k: v
                        for k, v in local_variables.items()
                        if k in global_variable_keys
                    }
                )

            self._variables.update(iteration_results)
            return "Completed"
        except Exception as e:
            raise ForEachError(e)

    async def sequence(self, _: str, array: list[str]):
        try:
            if not isinstance(array, list):
                raise ValueError("array must be a list")

            for item in array:
                await self._run_function(item)
            return "Completed"
        except Exception as e:
            raise SequenceError(e)

    def set_variable(self, _: str, variable_name: str, value: Any):
        self._variables[variable_name] = value
        return self._variables[variable_name]
