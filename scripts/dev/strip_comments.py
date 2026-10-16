import argparse
import ast
import io
import re
import tokenize
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def clean_python_source(source: str) -> str:
    """
    Strips comments and collapses multiline docstrings into concise one-line public docstrings.
    """
    try:
        ast.parse(source)
    except SyntaxError:
        return source

    lines = source.splitlines(keepends=True)

    # 1. Strip comments using tokenize
    readline = io.BytesIO(source.encode("utf-8")).readline
    try:
        tok_gen = tokenize.tokenize(readline)
        comment_spans = []
        for tok in tok_gen:
            if tok.type == tokenize.COMMENT:
                # Keep shebang on line 1
                if tok.start[0] == 1 and tok.string.startswith("#!"):
                    continue
                comment_spans.append((tok.start, tok.end))
    except Exception:
        return source

    for (s_row, s_col), (e_row, e_col) in reversed(comment_spans):
        line = lines[s_row - 1]
        prefix = line[:s_col]
        nl = "\n" if line.endswith("\n") else ""
        if prefix.strip() == "":
            lines[s_row - 1] = ""
        else:
            lines[s_row - 1] = prefix.rstrip() + nl

    intermediate = "".join(lines)
    try:
        tree = ast.parse(intermediate)
    except SyntaxError:
        return source

    # 2. Find multiline docstrings and collapse them to concise single lines
    docstring_spans = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                val = node.body[0].value.value
                if isinstance(val, str) and "\n" in val.strip():
                    expr = node.body[0]
                    # Get first non-empty line
                    first_line = ""
                    for sub in val.strip().splitlines():
                        if sub.strip():
                            first_line = sub.strip()
                            break
                    if first_line:
                        docstring_spans.append((expr.lineno, expr.end_lineno, expr.col_offset, first_line))

    if docstring_spans:
        int_lines = intermediate.splitlines(keepends=True)
        # Sort back to front
        docstring_spans.sort(key=lambda x: (x[0], x[1]), reverse=True)
        for start_line, end_line, col_offset, first_line in docstring_spans:
            indent = " " * col_offset
            # Clean single line docstring
            clean_doc = f'{indent}"""{first_line}"""\n'
            # Replace lines [start_line - 1 : end_line]
            int_lines[start_line - 1 : end_line] = [clean_doc]
        intermediate = "".join(int_lines)

    # 3. Clean consecutive empty lines (max 2)
    output_lines = []
    blank_count = 0
    for line in intermediate.splitlines():
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                output_lines.append("")
        else:
            blank_count = 0
            output_lines.append(line)

    result = "\n".join(output_lines)
    if source.endswith("\n") and not result.endswith("\n"):
        result += "\n"

    try:
        ast.parse(result)
    except SyntaxError:
        return source

    return result


def clean_js_ts_source(source: str) -> str:
    """
    Strips single-line and multi-line comments from JS/TS/JSX/TSX while
    preserving strings, template literals, regexes, and triple-slash directives.
    """
    result = []
    i = 0
    n = len(source)
    state = "code"

    while i < n:
        c = source[i]
        next_c = source[i + 1] if i + 1 < n else ""

        if state == "code":
            # Check for TypeScript triple-slash reference directive: /// <reference
            if c == "/" and next_c == "/" and i + 2 < n and source[i + 2] == "/":
                rest_of_line = source[i : source.find("\n", i) if source.find("\n", i) != -1 else n]
                if "<reference" in rest_of_line:
                    result.append(rest_of_line)
                    i += len(rest_of_line)
                    continue

            # JSX comment: {/* ... */}
            if c == "{" and next_c == "/" and i + 2 < n and source[i + 2] == "*":
                state = "jsx_comment"
                i += 3
                continue
            # Multi-line comment: /* ... */
            elif c == "/" and next_c == "*":
                state = "multi_comment"
                i += 2
                continue
            # Single-line comment: // ...
            elif c == "/" and next_c == "/":
                state = "single_comment"
                i += 2
                continue
            elif c == "'":
                state = "single_quote"
                result.append(c)
                i += 1
                continue
            elif c == '"':
                state = "double_quote"
                result.append(c)
                i += 1
                continue
            elif c == "`":
                state = "template_literal"
                result.append(c)
                i += 1
                continue
            else:
                result.append(c)
                i += 1
                continue

        elif state == "single_quote":
            result.append(c)
            if c == "\\" and i + 1 < n:
                i += 1
                result.append(source[i])
            elif c == "'":
                state = "code"
            i += 1
            continue

        elif state == "double_quote":
            result.append(c)
            if c == "\\" and i + 1 < n:
                i += 1
                result.append(source[i])
            elif c == '"':
                state = "code"
            i += 1
            continue

        elif state == "template_literal":
            result.append(c)
            if c == "\\" and i + 1 < n:
                i += 1
                result.append(source[i])
            elif c == "`":
                state = "code"
            i += 1
            continue

        elif state == "single_comment":
            if c == "\n":
                state = "code"
                result.append("\n")
            i += 1
            continue

        elif state == "multi_comment":
            if c == "*" and next_c == "/":
                state = "code"
                i += 2
                continue
            i += 1
            continue

        elif state == "jsx_comment":
            if c == "*" and next_c == "/" and i + 2 < n and source[i + 2] == "}":
                state = "code"
                i += 3
                continue
            i += 1
            continue

    cleaned_lines = []
    blank_count = 0
    for line in "".join(result).splitlines():
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(line)

    res_str = "\n".join(cleaned_lines)
    if source.endswith("\n") and not res_str.endswith("\n"):
        res_str += "\n"
    return res_str


def clean_css_source(source: str) -> str:
    """Strips /* ... */ comments from CSS."""
    pattern = r"/\*[\s\S]*?\*/"
    res = re.sub(pattern, "", source)
    cleaned_lines = []
    blank_count = 0
    for line in res.splitlines():
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(line)
    res_str = "\n".join(cleaned_lines)
    if source.endswith("\n") and not res_str.endswith("\n"):
        res_str += "\n"
    return res_str


def process_repository(apply: bool = False) -> None:
    python_files = (
        list((ROOT_DIR / "backend").rglob("*.py"))
        + list((ROOT_DIR / "tests").rglob("*.py"))
        + list((ROOT_DIR / "scripts").glob("*.py"))
    )

    frontend_files = (
        list((ROOT_DIR / "frontend" / "src").rglob("*.ts"))
        + list((ROOT_DIR / "frontend" / "src").rglob("*.tsx"))
        + list((ROOT_DIR / "frontend" / "src").rglob("*.js"))
        + list((ROOT_DIR / "frontend" / "src").rglob("*.jsx"))
        + list((ROOT_DIR / "frontend").glob("*.cjs"))
    )

    css_files = list((ROOT_DIR / "frontend" / "src").rglob("*.css"))

    modified_py = 0
    for p in python_files:
        try:
            content = p.read_text(encoding="utf-8-sig")
            cleaned = clean_python_source(content)
            if cleaned != content:
                modified_py += 1
                if apply:
                    p.write_text(cleaned, encoding="utf-8")
        except Exception as e:
            print(f"Error processing {p}: {e}")

    modified_fe = 0
    for p in frontend_files:
        try:
            content = p.read_text(encoding="utf-8-sig")
            cleaned = clean_js_ts_source(content)
            if cleaned != content:
                modified_fe += 1
                if apply:
                    p.write_text(cleaned, encoding="utf-8")
        except Exception as e:
            print(f"Error processing {p}: {e}")

    modified_css = 0
    for p in css_files:
        try:
            content = p.read_text(encoding="utf-8-sig")
            cleaned = clean_css_source(content)
            if cleaned != content:
                modified_css += 1
                if apply:
                    p.write_text(cleaned, encoding="utf-8")
        except Exception as e:
            print(f"Error processing {p}: {e}")

    print(
        f"Processing summary ({'APPLIED' if apply else 'DRY RUN'}):\n"
        f"  Python files modified: {modified_py} / {len(python_files)}\n"
        f"  Frontend files modified: {modified_fe} / {len(frontend_files)}\n"
        f"  CSS files modified: {modified_css} / {len(css_files)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply changes in place")
    args = parser.parse_args()
    process_repository(apply=args.apply)
