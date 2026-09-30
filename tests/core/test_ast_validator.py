"""Unit tests for AST Security Validator in COPPER Sandbox."""

from app.core.ast_validator import (
    ASTSecurityValidator,
    ASTValidationResult,
    ASTViolation,
    ast_security_validator,
)


def test_validator_instance_and_types():
    """Verify ASTSecurityValidator class instantiation and dataclass contracts."""
    validator = ASTSecurityValidator()
    res = validator.validate("x = 42")
    assert isinstance(res, ASTValidationResult)
    assert res.is_safe

    blocked_res = validator.validate("import os")
    assert isinstance(blocked_res, ASTValidationResult)
    assert not blocked_res.is_safe
    assert len(blocked_res.violations) > 0
    assert isinstance(blocked_res.violations[0], ASTViolation)
    assert blocked_res.violations[0].node_type == "Import"


def test_import_os_system_blocked():
    """Verify that importing os and executing system() is blocked."""
    code = "import os\nos.system('rm -rf /')"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("os" in v.description for v in res.violations)
    assert any(v.severity == "critical" for v in res.violations)


def test_eval_call_blocked():
    """Verify that calling eval() is blocked."""
    code = "eval(input())"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("eval()" in v.description for v in res.violations)


def test_exec_call_blocked():
    """Verify that calling exec() is blocked."""
    code = "exec(\"print('injected')\")"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("exec()" in v.description for v in res.violations)


def test_compile_call_blocked():
    """Verify that calling compile() is blocked."""
    code = "c = compile('1 + 1', '<string>', 'eval')"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("compile()" in v.description for v in res.violations)


def test_dunder_import_subprocess_blocked():
    """Verify that using __import__('subprocess').call(...) is blocked."""
    code = "__import__('subprocess').call(['ls'])"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("__import__()" in v.description for v in res.violations)


def test_print_hello_world_allowed():
    """Verify that benign print statements pass validation."""
    code = "print('hello world')"
    res = ast_security_validator.validate(code)
    assert res.is_safe
    assert res.risk_level == "safe"
    assert len(res.violations) == 0


def test_math_and_sum_allowed():
    """Verify that list operations and math sum pass validation."""
    code = "x = [1, 2, 3]\nprint(sum(x))"
    res = ast_security_validator.validate(code)
    assert res.is_safe
    assert res.risk_level == "safe"
    assert len(res.violations) == 0


def test_list_comprehension_and_string_ops_allowed():
    """Verify that list comprehensions, dicts, and string operations pass."""
    code = """
names = ['alice', 'bob', 'charlie']
upper_names = [n.upper() for n in names if len(n) > 3]
counts = {n: len(n) for n in names}
print(upper_names, counts)
"""
    res = ast_security_validator.validate(code)
    assert res.is_safe
    assert res.risk_level == "safe"
    assert len(res.violations) == 0


def test_dunder_globals_access_blocked():
    """Verify that accessing __globals__ is blocked."""
    code = "def f(): pass\ng = f.__globals__"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("__globals__" in v.description for v in res.violations)


def test_dunder_subclasses_chain_blocked():
    """Verify that sandbox escape chains accessing __subclasses__ or __bases__ are blocked."""
    code = "subclasses = ().__class__.__bases__[0].__subclasses__()"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    dunder_viols = [v.description for v in res.violations]
    assert any("__bases__" in d or "__subclasses__" in d for d in dunder_viols)


def test_dunder_builtins_and_code_blocked():
    """Verify that accessing __builtins__ and __code__ is blocked."""
    code = "b = ().__class__.__builtins__\nc = (lambda: 1).__code__"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    descriptions = " ".join(v.description for v in res.violations)
    assert "__builtins__" in descriptions
    assert "__code__" in descriptions


def test_getattr_sensitive_attribute_blocked():
    """Verify that using getattr to access sensitive dunder attributes is blocked."""
    code = "g = getattr(dict, '__globals__')"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("getattr()" in v.description for v in res.violations)


def test_open_write_mode_blocked():
    """Verify that open() with write mode ('w') is blocked as dangerous."""
    code = "f = open('output.txt', 'w')\nf.write('compromised')"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level in ("dangerous", "blocked")
    assert any("open() with write" in v.description for v in res.violations)


def test_open_append_and_modify_modes_blocked():
    """Verify that open() with append or update modes ('a', 'wb+', etc.) is blocked."""
    for mode in ("a", "a+", "wb+", "x", "w+"):
        code = f"open('file.txt', '{mode}')"
        res = ast_security_validator.validate(code)
        assert not res.is_safe
        assert any("open() with write" in v.description for v in res.violations)


def test_open_read_mode_allowed():
    """Verify that open() in default read-only or explicit 'r' mode passes."""
    code_implicit = "with open('input.txt') as f:\n    data = f.read()"
    res_implicit = ast_security_validator.validate(code_implicit)
    assert res_implicit.is_safe
    assert res_implicit.risk_level == "safe"

    code_explicit = "with open('input.txt', 'r') as f:\n    data = f.read()"
    res_explicit = ast_security_validator.validate(code_explicit)
    assert res_explicit.is_safe
    assert res_explicit.risk_level == "safe"


def test_open_dynamic_mode_blocked():
    """Verify that open() with a dynamic non-literal mode argument is rejected."""
    code = "mode_var = 'w'\nopen('file.txt', mode_var)"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert any("dynamic or non-literal mode" in v.description for v in res.violations)


def test_pathlib_unlink_destructive_blocked():
    """Verify that Path.unlink() is blocked as a destructive file system operation."""
    code = "from pathlib import Path\np = Path('secrets.txt')\np.unlink()"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert any("unlink()" in v.description for v in res.violations)


def test_pathlib_write_text_blocked():
    """Verify that Path.write_text() and write_bytes() are blocked."""
    code = "from pathlib import Path\nPath('out.txt').write_text('danger')"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert any("write_text()" in v.description for v in res.violations)


def test_forbidden_modules_import_blocked():
    """Verify that importing dangerous standard and third-party modules is blocked."""
    dangerous_modules = [
        "subprocess",
        "shutil",
        "sys",
        "socket",
        "ctypes",
        "importlib",
        "builtins",
        "signal",
        "multiprocessing",
        "requests",
        "urllib",
    ]
    for mod in dangerous_modules:
        code = f"import {mod}"
        res = ast_security_validator.validate(code)
        assert not res.is_safe, f"Module '{mod}' should have been blocked"
        assert res.risk_level == "blocked"
        assert any(mod in v.description for v in res.violations)


def test_aliased_import_blocked():
    """Verify that aliased imports (e.g. import os as o) cannot bypass module filters."""
    code = "import os as operating_system\noperating_system.getcwd()"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("os" in v.description for v in res.violations)


def test_from_import_blocked():
    """Verify that from ... import statements for forbidden modules are blocked."""
    code = "from subprocess import Popen, PIPE"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert any("subprocess" in v.description for v in res.violations)


def test_ast_literal_eval_explicitly_allowed():
    """Verify that ast.literal_eval is explicitly recognized as safe and permitted."""
    code = """
import ast
data = ast.literal_eval('{"status": "ok", "items": [1, 2, 3]}')
print(data["items"])
"""
    res = ast_security_validator.validate(code)
    assert res.is_safe
    assert res.risk_level == "safe"
    assert len(res.violations) == 0


def test_locals_call_suspicious_warning():
    """Verify that locals() triggers a suspicious warning but not a critical block."""
    code = "def get_state():\n    a = 10\n    return locals()"
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "suspicious"
    assert len(res.violations) == 1
    assert res.violations[0].severity == "warning"
    assert "locals()" in res.violations[0].description


def test_vars_call_suspicious_warning():
    """Verify that vars() triggers a suspicious warning."""
    code = "x = 42\nv = vars()"
    res = ast_security_validator.validate(code)
    assert res.risk_level == "suspicious"
    assert any(v.severity == "warning" for v in res.violations)


def test_complex_multiline_script_allowed():
    """Verify that complex multi-line algorithms with functions and classes pass."""
    code = """
import math

class MatrixMath:
    def __init__(self, data: list[list[float]]):
        self.data = data

    def trace(self) -> float:
        return sum(self.data[i][i] for i in range(len(self.data)))

    def apply_sin(self) -> list[list[float]]:
        return [[math.sin(val) for val in row] for row in self.data]

def quicksort(arr: list[int]) -> list[int]:
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

m = MatrixMath([[1.0, 2.0], [3.0, 4.0]])
sorted_items = quicksort([9, 3, 7, 1, 5])
print(m.trace(), sorted_items)
"""
    res = ast_security_validator.validate(code)
    assert res.is_safe
    assert res.risk_level == "safe"
    assert len(res.violations) == 0


def test_syntax_error_handled_gracefully():
    """Verify that malformed Python syntax produces a structured SyntaxError violation."""
    code = "def broken_func("
    res = ast_security_validator.validate(code)
    assert not res.is_safe
    assert res.risk_level == "blocked"
    assert len(res.violations) == 1
    assert res.violations[0].node_type == "SyntaxError"
    assert res.violations[0].severity == "critical"


def test_empty_code_allowed():
    """Verify that empty or whitespace-only code strings are marked safe."""
    assert ast_security_validator.validate("").is_safe
    assert ast_security_validator.validate("   \n\t  ").is_safe


def test_comments_and_docstrings_allowed():
    """Verify that extensive comments and docstrings pass cleanly."""
    code = '''
"""Module docstring explaining algorithm."""

# Helpful comment about computation
def compute():
    """Compute double of 21."""
    return 21 * 2

result = compute()
'''
    res = ast_security_validator.validate(code)
    assert res.is_safe
    assert res.risk_level == "safe"
