# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.


class BranchError(Exception):
    """Raised when an exception is encountered while executing a branch action"""


class ForEachError(Exception):
    """Raised when an exception is encountered while executing a for-each action"""


class FunctionCallError(Exception):
    """Raised when an exception is encountered while calling a function"""


class FunctionRunError(Exception):
    """Raised when an exception is encountered while calling a function"""


class FunctionLoadError(Exception):
    """Raised when an unhandled exception is encountered while loading a function to functions cache"""


class GetSubProcessError(Exception):
    """Raised when an exception is encountered while getting a sub-process"""


class InvalidActionId(Exception):
    """Raised when an exception is encountered while executing an invalid action ID"""


class InvalidFunction(Exception):
    """Raised when an exception is encountered while executing an invalid function"""


class InvalidFunctionSyntax(Exception):
    """Raised when an exception is encountered while executing an invalid function syntax"""


class InvalidModule(Exception):
    """Raised when an exception is encountered while executing an invalid module"""


class InvalidSubProcessActionId(Exception):
    """Raised when an exception is encountered while executing an invalid sub-process action ID"""


class JSONExtractionError(Exception):
    """Raised when an exception is encountered while extracting JSON"""


class ModifySubProcessError(Exception):
    """Raised when an exception is encountered while modifying a sub-process"""


class PatternReplacementError(Exception):
    """Raised when an exception is encountered while replacing patterns"""


class ProcessInitializationError(Exception):
    """Raised when an exception is encountered while initializing a process"""


class ProcessRunError(Exception):
    """Raised when an exception is encountered while running a process"""


class REGEXExtractionError(Exception):
    """Raised when an exception is encountered while extracting using regular expressions"""


class SequenceError(Exception):
    """Raised when an exception is encountered while executing a sequence action"""


class ParallelError(Exception):
    """Raised when an exception is encountered while executing a parallel action"""


class ArgumentError(Exception):
    """Raised when an exception is encountered while executing a sequence action"""


class KeywordArgumentError(Exception):
    """Raised when an exception is encountered while executing a sequence action"""


class SetExceptionsError(Exception):
    """Raised when an exception is encountered while executing a sequence action"""
