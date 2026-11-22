"""Check every docstring against the python-docstrings SKILL.md rules."""

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted(
    list((ROOT / "northwind_analysis").glob("*.py"))
    + [ROOT / "run_all.py", ROOT / "verify_with_sql.py"]
)
MAX_LINE = 72
THIRD_PERSON_OK = {"Process"}


def _functions():
    """Yield every function definition in the project.

    Args:
        None.

    Yields:
        tuple[pathlib.Path, ast.FunctionDef]: Source file and the
        function node.
    """
    for path in FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                yield path, node


def _signature_names(node):
    """List documented parameter names in signature order.

    Args:
        node (ast.FunctionDef): Function definition.

    Returns:
        list[str]: Names, with ``*`` and ``**`` prefixes for
        variadic parameters; ``self`` and ``cls`` are excluded.
    """
    args = node.args
    names = [
        a.arg
        for a in args.posonlyargs + args.args
        if a.arg not in ("self", "cls")
    ]
    if args.vararg:
        names.append("*" + args.vararg.arg)
    names += [a.arg for a in args.kwonlyargs]
    if args.kwarg:
        names.append("**" + args.kwarg.arg)
    return names


def _documented_names(doc):
    """List parameter names documented under ``Args:``.

    Args:
        doc (str): Cleaned docstring text.

    Returns:
        list[str]: Names in the order written.
    """
    names, inside = [], False
    for line in doc.splitlines():
        if line.strip() == "Args:":
            inside = True
            continue
        if inside:
            if line and not line.startswith(" "):
                break
            if line.startswith("    ") and not line.startswith("     "):
                names.append(line.strip().split(" (")[0])
    return names


class TestDocstringRules(unittest.TestCase):
    """Rules from SKILL.md applied to every function."""

    def test_modules_have_docstrings(self):
        for path in FILES:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            self.assertTrue(ast.get_docstring(tree), path.name)

    def test_every_function_has_docstring(self):
        for path, node in _functions():
            self.assertTrue(
                ast.get_docstring(node), f"{path.name}:{node.name}"
            )

    def test_args_match_signature_in_order(self):
        for path, node in _functions():
            doc = ast.get_docstring(node)
            params = _signature_names(node)
            label = f"{path.name}:{node.name}"
            if params:
                self.assertEqual(
                    _documented_names(doc), params, label
                )
            else:
                self.assertIn("Args:\n    None.", doc, label)

    def test_output_section_present(self):
        for path, node in _functions():
            doc = ast.get_docstring(node)
            self.assertTrue(
                "Returns:" in doc or "Yields:" in doc,
                f"{path.name}:{node.name}",
            )

    def test_generators_use_yields(self):
        for path, node in _functions():
            is_gen = any(
                isinstance(n, (ast.Yield, ast.YieldFrom))
                for n in ast.walk(node)
            )
            doc = ast.get_docstring(node)
            label = f"{path.name}:{node.name}"
            if is_gen:
                self.assertIn("Yields:", doc, label)
            else:
                self.assertNotIn("Yields:", doc, label)

    def test_raises_documented_when_raised(self):
        for path, node in _functions():
            doc = ast.get_docstring(node)
            raised = {
                n.exc.func.id
                for n in ast.walk(node)
                if isinstance(n, ast.Raise)
                and isinstance(n.exc, ast.Call)
                and isinstance(n.exc.func, ast.Name)
            }
            label = f"{path.name}:{node.name}"
            if raised:
                self.assertIn("Raises:", doc, label)
                for name in raised:
                    self.assertIn(name, doc, label)
            else:
                self.assertNotIn("Raises:", doc, label)

    def test_summary_line_format(self):
        for path, node in _functions():
            doc = ast.get_docstring(node)
            lines = doc.splitlines()
            label = f"{path.name}:{node.name}"
            self.assertTrue(lines[0].endswith("."), label)
            if len(lines) > 1:
                self.assertEqual(lines[1], "", label)
            first = lines[0].split()[0]
            self.assertFalse(
                first.endswith("s") and first not in THIRD_PERSON_OK,
                f"{label}: summary should be imperative",
            )
            for filler in ("This function", "Helper to", "Used to"):
                self.assertFalse(lines[0].startswith(filler), label)

    def test_line_length_and_whitespace(self):
        for path, node in _functions():
            raw = ast.get_docstring(node, clean=False)
            label = f"{path.name}:{node.name}"
            for line in raw.splitlines()[:-1]:
                self.assertLessEqual(len(line), MAX_LINE, f"{label}: {line}")
                self.assertEqual(line, line.rstrip(), label)

    def test_quote_style_and_layout(self):
        for path, node in _functions():
            lines = path.read_text(encoding="utf-8").splitlines()
            first = node.body[0]
            label = f"{path.name}:{node.name}"
            self.assertTrue(
                lines[first.lineno - 1].strip().startswith('"""'), label
            )
            self.assertEqual(lines[first.end_lineno - 1].strip(), '"""', label)
            self.assertNotEqual(lines[first.lineno - 2].strip(), "", label)
            if len(node.body) > 1:
                self.assertNotEqual(
                    lines[first.end_lineno].strip(), "", label
                )


if __name__ == "__main__":
    unittest.main()
