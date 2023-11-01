# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

from typing import Any
from jsonpath_ng.ext import parse

from app.utils import Process
from app.utils.exceptions import (
    BranchError,
    JSONExtractionError,
    ForEachError,
    SequenceError,
)


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


def extract_json(self, action_id: str, json_obj: dict, expression: str):
    try:
        if not isinstance(json_obj, dict):
            raise ValueError("json_object must be a dictionary")

        values = [res.value for res in parse(expression).find(json_obj)]
        if len(values) == 1:
            return values[0]
        return values
    except Exception as e:
        raise JSONExtractionError(f"Unable to extract JSON: {e}")


async def for_each(
    self,
    action_id: str,
    array: list,
    next_function: str,
):
    try:
        if not isinstance(array, list):
            raise ValueError("array must be a list")

        for index, item in enumerate(array):
            global_variable_keys = [k for k in self._variables.keys() if "__" not in k]
            flow = self._flow.model_copy()
            flow.variables = {k: v for k, v in self._variables.items() if "__" not in k}
            flow.variables[action_id] = item
            flow.start_id = next_function
            process = Process(flow, debug=self._debug, update=self._update)
            await process._run_function(next_function)
            local_variables = process._variables
            for k in global_variable_keys:
                self._variables[k] = local_variables.pop(k)
            self._variables[f"{action_id}__{index}"] = local_variables
        return "Completed"
    except Exception as e:
        raise ForEachError(e)


async def sequence(self, action_id: str, array: list[str]):
    try:
        if not isinstance(array, list):
            raise ValueError("array must be a list")

        for item in array:
            flow = self._flow.model_copy()
            flow.variables = {k: v for k, v in self._variables.items() if "__" not in k}
            flow.start_id = item
            process = Process(flow, debug=self._debug, update=self._update)
            await process._run_function(item)
            self._variables.update(process._variables)
        return "Completed"
    except Exception as e:
        raise SequenceError(e)


def set_variable(self, action_id: str, variable_name: str, value: Any):
    self._variables[variable_name] = value
    return self._variables[variable_name]
