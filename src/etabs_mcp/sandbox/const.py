"""Sandbox constants: allowed builtins, blocked attributes, module whitelists."""

ALLOWED_BUILTIN_EXCEPTIONS: frozenset[str] = frozenset(
    {
        "Exception",
        "ArithmeticError", "FloatingPointError", "OverflowError", "ZeroDivisionError",
        "LookupError", "IndexError", "KeyError",
        "NameError", "UnboundLocalError",
        "OSError", "BlockingIOError", "BrokenPipeError", "ChildProcessError",
        "ConnectionError", "ConnectionAbortedError", "ConnectionRefusedError",
        "ConnectionResetError", "FileExistsError", "FileNotFoundError",
        "InterruptedError", "IsADirectoryError", "NotADirectoryError",
        "PermissionError", "ProcessLookupError", "TimeoutError",
        "RuntimeError", "NotImplementedError", "RecursionError",
        "AssertionError", "AttributeError", "BufferError", "EOFError",
        "ImportError", "ModuleNotFoundError", "MemoryError", "ReferenceError",
        "StopAsyncIteration", "StopIteration", "SystemError",
        "TypeError", "ValueError",
        "UnicodeError", "UnicodeDecodeError", "UnicodeEncodeError", "UnicodeTranslateError",
        "Warning", "BytesWarning", "DeprecationWarning", "FutureWarning",
        "ImportWarning", "PendingDeprecationWarning", "ResourceWarning",
        "RuntimeWarning", "SyntaxWarning", "UnicodeWarning", "UserWarning",
    }
)

ALLOWED_BUILTINS: frozenset[str] = frozenset(
    {
        "abs", "all", "any", "bin", "bool", "bytes", "chr", "dict", "divmod",
        "enumerate", "filter", "float", "frozenset", "hash", "hex", "int",
        "isinstance", "issubclass", "iter", "len", "list", "map", "max",
        "min", "next", "oct", "ord", "pow", "print", "range", "repr",
        "reversed", "round", "set", "slice", "sorted", "str", "sum",
        "tuple", "zip",
        "True", "False", "None",
        *ALLOWED_BUILTIN_EXCEPTIONS,
    }
)

BLOCKED_BUILTINS: frozenset[str] = frozenset(
    {
        "eval", "exec", "compile", "__import__", "globals", "locals", "vars",
        "dir", "getattr", "setattr", "delattr", "hasattr", "open", "input",
        "breakpoint", "exit", "quit", "memoryview", "classmethod",
        "staticmethod", "property", "super", "type", "__build_class__", "format",
    }
)

BLOCKED_ATTRS: frozenset[str] = frozenset(
    {
        "gi_frame", "gi_code", "gi_yieldfrom",
        "cr_frame", "cr_code", "cr_origin",
        "ag_frame", "ag_code",
        "f_globals", "f_locals", "f_builtins", "f_code", "f_back", "f_trace", "f_lineno",
        "co_consts", "co_names", "co_varnames", "co_freevars", "co_cellvars",
        "co_filename", "co_code",
        "tb_frame", "tb_next", "tb_lineno",
        "mro",
        # pywin32 COM dispatch internals
        "_oleobj_", "_ApplyTypes_", "_FlagAsMethod", "_olerepr_",
        "_mapCachedItems_", "_builtMethods_", "_enum_", "_lazydata_",
    }
)

ALLOWED_MODULE_ATTRS: dict[str, frozenset[str]] = {
    "json": frozenset({"dumps", "loads"}),
    "math": frozenset(
        {
            "pi", "e", "tau", "inf", "nan",
            "ceil", "floor", "trunc", "factorial", "gcd", "lcm",
            "comb", "perm", "fabs", "fmod", "remainder", "copysign",
            "fsum", "prod", "isqrt", "frexp", "ldexp", "modf",
            "nextafter", "ulp",
            "exp", "expm1", "log", "log2", "log10", "log1p", "pow", "sqrt",
            "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
            "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
            "degrees", "radians", "hypot", "dist",
            "erf", "erfc", "gamma", "lgamma",
            "isfinite", "isinf", "isnan", "isclose",
        }
    ),
}

MAX_EXECUTION_STDOUT = 256_000
MAX_RESULT_LENGTH = 100_000
