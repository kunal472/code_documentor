import ast
from pathlib import Path
from typing import List, Tuple

from app.models import CodeElement


# ... (Helper functions _get_docstring, _get_function_details, _get_class_details remain the same) ...
def _get_docstring(node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef) -> str | None:
    return ast.get_docstring(node)


def _get_function_details(
        node: ast.AsyncFunctionDef | ast.FunctionDef
) -> Tuple[List[str], str | None]:
    params = [arg.arg for arg in node.args.args]
    return_type = None
    if node.returns:
        if isinstance(node.returns, ast.Name):
            return_type = node.returns.id
        elif isinstance(node.returns, ast.Constant):
            return_type = str(node.returns.value)
        else:
            return_type = ast.unparse(node.returns)
    return params, return_type


def _get_class_details(node: ast.ClassDef) -> Tuple[List[str], List[CodeElement]]:
    base_classes = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            base_classes.append(base.id)
        else:
            base_classes.append(ast.unparse(base))

    methods = []
    for body_item in node.body:
        if isinstance(body_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_params, method_return = _get_function_details(body_item)
            methods.append(
                CodeElement(
                    type="method",
                    name=body_item.name,
                    start_line=body_item.lineno,
                    end_line=body_item.end_lineno or body_item.lineno,
                    docstring=_get_docstring(body_item),
                    parameters=method_params,
                    return_type=method_return,
                )
            )
    return base_classes, methods


# ... (End of unchanged helper functions) ...


class PythonASTVisitor(ast.NodeVisitor):
    """
    Visits an AST tree and extracts function/class definitions and imports.
    """

    def __init__(self):
        self.elements: List[CodeElement] = []
        # --- NEW: Store imports ---
        self.imports: List[str] = []
        # --- END NEW ---

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_function(node)
        # We don't call generic_visit to avoid parsing nested functions
        # self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_function(node)
        # self.generic_visit(node)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        # This simple check assumes top-level functions are not nested.
        # A more robust way tracks parent nodes, but this is fine for now.
        params, return_type = _get_function_details(node)
        self.elements.append(
            CodeElement(
                type="function",
                name=node.name,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                docstring=_get_docstring(node),
                parameters=params,
                return_type=return_type,
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef):
        base_classes, methods = _get_class_details(node)

        class_element = CodeElement(
            type="class",
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=_get_docstring(node),
            base_classes=base_classes,
        )
        self.elements.append(class_element)
        self.elements.extend(methods)
        # Don't call generic_visit, methods are handled in _get_class_details

    # --- NEW: Added import visitors ---
    def visit_Import(self, node: ast.Import):
        """
        Handles `import os, sys`
        """
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """
        Handles `from pathlib import Path` or `from . import utils`
        """
        if node.module:
            # Reconstruct the full import path
            # level 0: from my_pkg import foo
            # level 1: from . import foo
            # level 2: from .. import foo
            prefix = "." * node.level
            self.imports.append(f"{prefix}{node.module}")
        elif node.level > 0:
            # Handle `from . import foo` (where module is None)
            prefix = "." * node.level
            # We can't know the full path here, but the dependency analyzer
            # will use the prefix. For simplicity, we just add the prefix
            # and the first imported name as a hint.
            if node.names:
                self.imports.append(f"{prefix}{node.names[0].name}")
            else:
                self.imports.append(f"{prefix}")

        self.generic_visit(node)
    # --- END NEW ---


def parse_python_file(file_path: Path) -> Tuple[List[CodeElement], List[str]]:
    """
    Reads a Python file and uses AST to parse its structure and imports.

    Returns a tuple of (code_elements, import_statements).
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        visitor = PythonASTVisitor()
        visitor.visit(tree)
        # --- MODIFIED: Return imports as well ---
        return visitor.elements, visitor.imports
        # --- END MODIFICATION ---

    except SyntaxError as e:
        print(f"Syntax error in {file_path} at line {e.lineno}: {e.msg}")
        return [], []
    except Exception as e:
        print(f"Error parsing Python file {file_path}: {e}")
        return [], []