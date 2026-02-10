"""AST-first construct checks for exercise code."""

from __future__ import annotations

import ast
import io
import re
import token
import tokenize
from typing import Final

_OPERATOR_NODES: Final[dict[str, type[ast.operator]]] = {
    "*": ast.Mult,
    "/": ast.Div,
    "-": ast.Sub,
}


def _parse_code(code: str) -> ast.AST | None:
    """Return an AST for code, or None when parsing fails."""
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def _has_print_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            return True
    return False


def _has_operator(tree: ast.AST, operator_type: type[ast.operator]) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, operator_type):
            return True
        if isinstance(node, ast.AugAssign) and isinstance(node.op, operator_type):
            return True
    return False


def check_has_print_statement(code: str) -> bool:
    """Return True when the code contains a print call, using AST-first checks."""
    tree = _parse_code(code)
    if tree is None:
        return re.search(r"\bprint\s*\(", code) is not None
    return _has_print_call(tree)


def check_uses_operator(code: str, operator: str) -> bool:
    """Return True when the code uses the required operator, using AST-first checks."""
    operator_type = _OPERATOR_NODES.get(operator)
    if operator_type is None:
        raise ValueError(f"Unsupported operator: {operator}")

    tree = _parse_code(code)
    if tree is None:
        allowed_tokens = {operator, f"{operator}="}
        try:
            for tok in tokenize.generate_tokens(io.StringIO(code).readline):
                if tok.type in {token.STRING, tokenize.COMMENT}:
                    continue
                if tok.type == token.OP and tok.string in allowed_tokens:
                    return True
        except (tokenize.TokenError, IndentationError):
            return False
        return False
    return _has_operator(tree, operator_type)
