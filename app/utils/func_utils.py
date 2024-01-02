import importlib
import inspect
import sys
import ast
import re


def get_signature(func):
    return str(inspect.signature(func))


def has_kwargs(func):
    return any(
        param.kind == param.VAR_KEYWORD
        for param in inspect.signature(func).parameters.values()
    )


def get_source(func):
    return inspect.getsource(func)


class CallVisitor(ast.NodeVisitor):
    def __init__(self, function_name, module_name):
        self.functions = []
        self.with_asnames = {}
        self.imports = {}
        self.current_function = None
        self.function_name = function_name
        module_name, _ = (
            module_name.rsplit(".", 1) if "." in module_name else (module_name, "")
        )
        self.module_name = module_name

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports[alias.name] = (
                f"{self.module_name}.{alias.name}" if node.level == 1 else node.module
            )
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports[alias.name] = alias.name
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.generic_visit(node)

    def visit_With(self, node):
        for item in node.items:
            if isinstance(item.context_expr, ast.Call) and isinstance(
                item.optional_vars, ast.Name
            ):
                self.with_asnames[item.optional_vars.id] = ast.unparse(
                    item.context_expr.func
                )
        self.generic_visit(node)

    def visit_Call(self, node):
        if self.current_function == self.function_name and any(
            [
                keyword.value.id
                for keyword in node.keywords
                if "kwargs" in keyword.value.id
            ]
        ):
            func_name = ast.unparse(node.func)
            for asname, class_name in self.with_asnames.items():
                func_name = func_name.replace(asname, class_name)
            for import_name, module_name in self.imports.items():
                func_name = func_name.replace(import_name, module_name)
            self.functions.append(func_name)
        self.generic_visit(node)


def find_functions_passing_kwargs(source, function_name, module_name):
    tree = ast.parse(source)
    visitor = CallVisitor(function_name, module_name)
    visitor.visit(tree)
    return visitor.functions


def is_attribute_of_module(func_name, module):
    return getattr(module, func_name, False)


def get_all_func_defs_and_kwargs(func_name):
    if "." not in func_name:
        module_name = __name__
        module = sys.modules[__name__]
        func = getattr(module, func_name)
    else:
        module_name, func_name = func_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)

    sig = get_signature(func)
    doc = func.__doc__

    func_defs = {
        0: {
            "func": func.__name__,
            "signature": sig,
            "sig_params": {
                k: {
                    "annotation": str(v.annotation)
                    if v.annotation is not inspect._empty
                    else "No annotation",
                    "default": str(v.default)
                    if v.default is not inspect._empty
                    else "No default value",
                }
                for k, v in inspect.signature(func).parameters.items()
                if k not in ["self", "kwargs"]
            },
            "doc": doc,
        }
    }

    func_count = 0
    kwargs = {}
    funcs = [func]
    while funcs:
        temp = funcs.pop(0)
        if not has_kwargs(temp):
            kwargs.update(inspect.signature(temp).parameters)
        elif (source := get_source(importlib.import_module(temp.__module__))) and (
            func_names := find_functions_passing_kwargs(
                source, temp.__name__, temp.__module__
            )
        ):
            for f in func_names:
                if "." in f:
                    module_name, f_name = f.rsplit(".", 1)
                    try:
                        module = importlib.import_module(module_name)
                        f_attr = getattr(module, f_name, False)
                    except ModuleNotFoundError:
                        module_name, class_name, f_name = f.rsplit(".", 2)
                        module = importlib.import_module(module_name)
                        cls = getattr(module, class_name)
                        f_attr = getattr(cls, f_name, False)
                    if f_attr:
                        f_sig = get_signature(f_attr)
                        f_doc = f_attr.__doc__
                        func_defs[func_count + 1] = {
                            "func": f,
                            "signature": f_sig,
                            "sig_params": {
                                k: {
                                    "annotation": str(v.annotation)
                                    if v.annotation is not inspect._empty
                                    else "No annotation",
                                    "default": str(v.default)
                                    if v.default is not inspect._empty
                                    else "No default value",
                                }
                                for k, v in inspect.signature(f_attr).parameters.items()
                                if k not in ["self", "kwargs"]
                            },
                            "doc": f_doc,
                        }
                        func_count += 1
                        funcs.append(f_attr)
                elif f_attr := is_attribute_of_module(f, module):
                    f_sig = get_signature(f_attr)
                    f_doc = f_attr.__doc__
                    func_defs[func_count + 1] = {
                        "func": f,
                        "signature": f_sig,
                        "sig_params": {
                            k: {
                                "annotation": str(v.annotation)
                                if v.annotation is not inspect._empty
                                else "No annotation",
                                "default": str(v.default)
                                if v.default is not inspect._empty
                                else "No default value",
                            }
                            for k, v in inspect.signature(f_attr).parameters.items()
                            if k not in ["self", "kwargs"]
                        },
                        "doc": f_doc,
                    }
                    func_count += 1
                    funcs.append(f_attr)
        else:
            kwargs.update(inspect.signature(temp).parameters)
    return func_defs, {
        k: {
            "annotation": str(v.annotation)
            if v.annotation is not inspect._empty
            else "No annotation",
            "default": str(v.default)
            if v.default is not inspect._empty
            else "No default value",
        }
        for k, v in kwargs.items()
        if k != "self"
    }


# this merges the signatures of all the functions into one, not needed for now
# def format_signature(func_dict):
#     signatures = [v["signature"].strip("()").split(", ") for v in func_dict.values()]
#     signatures = [[param for param in sig if param != "**kwargs"] for sig in signatures]
#     for param in signatures[-1][:]:
#         if param not in signatures[0] and any(param in sig for sig in signatures[1:-1]):
#             signatures[-1].remove(param)
#     if "self" in signatures[-1]:
#         signatures[-1].remove("self")
#     return "(" + ", ".join(signatures[-1]) + ")"


def get_params_to_remove(func_dict):
    params_to_remove = []
    if len(func_dict) > 1:
        signatures = [
            v["signature"].strip("()").split(", ") for v in func_dict.values()
        ]
        signatures = [
            [re.split("=", param)[0] for param in sig if param != "**kwargs"]
            for sig in signatures
        ]
        for signature in signatures[:-1]:
            for param in signature:
                if param not in params_to_remove:
                    params_to_remove.append(param)
    return params_to_remove


def get_param_doc(docstring, kw):
    pattern = f"(:param {kw}:.*?)((?=:param)|$)"
    match = re.search(pattern, docstring, re.DOTALL)
    return match.group() if match else None


def inject_docs(func_dict, kwargs):
    last_key = max(func_dict.keys())
    last_doc = func_dict[last_key]["doc"]
    kwargs_docs = {kw: get_param_doc(last_doc, kw) for kw in kwargs}
    kwargs_docs = {kw: doc for kw, doc in kwargs_docs.items() if doc is not None}
    kwargs_joined = "\n        " + "\n        ".join(kwargs_docs.values())

    first_doc = func_dict[0]["doc"]
    kwargs_pos = first_doc.find(":param \*\*kwargs:")
    if kwargs_pos != -1:
        kwargs_pos = first_doc[kwargs_pos:].find("\n") + kwargs_pos
        first_half = first_doc[:kwargs_pos]
        last_half = first_doc[kwargs_pos:]

        first_doc = f"{first_half}\n    {kwargs_joined}{last_half}"

    return first_doc


def get_func_def(func_name):
    definitions, kwargs = get_all_func_defs_and_kwargs(func_name)
    params_to_remove = get_params_to_remove(definitions)
    for param in params_to_remove:
        kwargs.pop(param, None)
    formatted = definitions[0]["doc"]
    if params_to_remove:
        formatted = inject_docs(definitions, kwargs)
    return {
        "func": definitions[0]["func"],
        "signature": definitions[0]["signature"],
        "sig_params": definitions[0]["sig_params"],
        "doc": formatted,
    }


print(get_func_def("requests.get"))

# print(get_func_def("requests.get")) returns:
# {
#     "func": "get",
#     "signature": "(url, params=None, **kwargs)",
#     "sig_params": {
#         "url": {"annotation": "No annotation", "default": "No default value"},
#         "params": {"annotation": "No annotation", "default": "None"},
#     },
#     "doc": "Sends a GET request.\n\n    :param url: URL for the new :class:`Request` object.\n    :param params: (optional) Dictionary, list of tuples or bytes to send\n        in the query string for the :class:`Request`.\n    :param \\*\\*kwargs: Optional arguments that ``request`` takes.\n    \n        :param data: (optional) Dictionary, list of tuples, bytes, or file-like\n            object to send in the body of the :class:`Request`.\n        \n        :param headers: (optional) Dictionary of HTTP Headers to send with the\n            :class:`Request`.\n        \n        :param cookies: (optional) Dict or CookieJar object to send with the\n            :class:`Request`.\n        \n        :param files: (optional) Dictionary of ``'filename': file-like-objects``\n            for multipart encoding upload.\n        \n        :param auth: (optional) Auth tuple or callable to enable\n            Basic/Digest/Custom HTTP Auth.\n        \n        :param timeout: (optional) How long to wait for the server to send\n            data before giving up, as a float, or a :ref:`(connect timeout,\n            read timeout) <timeouts>` tuple.\n        :type timeout: float or tuple\n        \n        :param allow_redirects: (optional) Set to True by default.\n        :type allow_redirects: bool\n        \n        :param proxies: (optional) Dictionary mapping protocol or protocol and\n            hostname to the URL of the proxy.\n        \n        :param stream: (optional) whether to immediately download the response\n            content. Defaults to ``False``.\n        \n        :param verify: (optional) Either a boolean, in which case it controls whether we verify\n            the server's TLS certificate, or a string, in which case it must be a path\n            to a CA bundle to use. Defaults to ``True``. When set to\n            ``False``, requests will accept any TLS certificate presented by\n            the server, and will ignore hostname mismatches and/or expired\n            certificates, which will make your application vulnerable to\n            man-in-the-middle (MitM) attacks. Setting verify to ``False``\n            may be useful during local development or testing.\n        \n        :param cert: (optional) if String, path to ssl client cert file (.pem).\n            If Tuple, ('cert', 'key') pair.\n        :rtype: requests.Response\n        \n        :param json: (optional) json to send in the body of the\n            :class:`Request`.\n        \n    :return: :class:`Response <Response>` object\n    :rtype: requests.Response\n    ",
# }
