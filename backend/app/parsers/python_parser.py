import ast
from pathlib import Path
from typing import List, Tuple

from app.models import CodeElement


def _get_docstring(node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef) -> str | None:
    """
    Safely extracts the docstring from a node.
    """
    return ast.get_docstring(node)


def _get_function_details(
        node: ast.AsyncFunctionDef | ast.FunctionDef
) -> Tuple[List[str], str | None]:
    """
    Extracts parameter names and return type annotation.
    """
    params = [arg.arg for arg in node.args.args]
    return_type = None
    if node.returns:
        if isinstance(node.returns, ast.Name):
            return_type = node.returns.id
        elif isinstance(node.returns, ast.Constant):  # Python 3.10+ for simple types
            return_type = str(node.returns.value)
        else:
            # Handle complex types like list[str]
            return_type = ast.unparse(node.returns)

    return params, return_type


def _get_class_details(node: ast.ClassDef) -> Tuple[List[str], List[CodeElement]]:
    """
    Extracts base class names and parses internal methods.
    """
    base_classes = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            base_classes.append(base.id)
        else:
            # Handle complex base definitions
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


class PythonASTVisitor(ast.NodeVisitor):
    """
    Visits an AST tree and extracts function and class definitions.
    """

    def __init__(self):
        self.elements: List[CodeElement] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_function(node)
        self.generic_visit(node)  # Continue traversal inside function? (No, for top-level)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_function(node)
        self.generic_visit(node)  # Continue traversal inside function? (No, for top-level)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        # Check if function is defined at the top level (not a method)
        # This is a simple check; a more robust way involves tracking parent nodes.
        # For now, we'll assume visit_ClassDef handles methods separately.

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

        # Don't call generic_visit on the class body,
        # as we've already processed its methods.
        # self.generic_visit(node)


def parse_python_file(file_path: Path) -> List[CodeElement]:
    """
    Reads a Python file and uses AST to parse its structure.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        visitor = PythonASTVisitor()
        visitor.visit(tree)
        return visitor.elements

    except SyntaxError as e:
        print(f"Syntax error in {file_path} at line {e.lineno}: {e.msg}")
        return []
    except Exception as e:
        print(f"Error parsing Python file {file_path}: {e}")
        return []