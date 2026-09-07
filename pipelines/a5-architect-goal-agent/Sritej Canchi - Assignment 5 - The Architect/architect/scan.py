"""Codebase perception.

Class 7 slide 8: the agent reads the project the way a new developer would.
Directory structure first, then what is actually wired up.

We use the ast module rather than regex so that "charge" appearing inside a
comment is not mistaken for a charge system that exists. Comments are recorded
separately and deliberately scored lower, because a comment describing a system
is evidence the system was considered and NOT built.
"""
import ast
import os


class Symbol:
    def __init__(self, name, kind, module, lineno):
        self.name, self.kind = name, kind
        self.module, self.lineno = module, lineno

    def as_dict(self):
        return {"name": self.name, "kind": self.kind,
                "module": self.module, "line": self.lineno}


class Codebase:
    def __init__(self, root):
        self.root = root
        self.modules = {}     # relpath -> source
        self.symbols = []     # Symbol
        self.imports = {}     # relpath -> [module names]
        self.comments = []    # (relpath, lineno, text)
        self.stubs = []       # functions whose body is a single literal return
        self._walk()

    def _walk(self):
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames
                           if d not in ("__pycache__", ".git", "state")]
            for fn in sorted(filenames):
                if not fn.endswith(".py"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, self.root).replace("\\", "/")
                src = open(full, encoding="utf-8").read()
                self.modules[rel] = src
                self._parse(rel, src)

    def _parse(self, rel, src):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and _is_constant_stub(node):
                self.stubs.append(Symbol(node.name, "stub", rel, node.lineno))
            if isinstance(node, ast.ClassDef):
                self.symbols.append(Symbol(node.name, "class", rel, node.lineno))
            elif isinstance(node, ast.FunctionDef):
                self.symbols.append(Symbol(node.name, "def", rel, node.lineno))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                self.symbols.append(Symbol(node.id, "name", rel, node.lineno))
            elif isinstance(node, ast.Attribute):
                self.symbols.append(Symbol(node.attr, "attr", rel, node.lineno))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", None) or ""
                imports.append(mod or ",".join(a.name for a in node.names))
        self.imports[rel] = imports
        for i, line in enumerate(src.splitlines(), 1):
            s = line.strip()
            if s.startswith("#"):
                self.comments.append((rel, i, s.lstrip("# ")))

    # ---- queries -----------------------------------------------------
    def names(self):
        return {s.name.lower() for s in self.symbols}

    def find(self, token):
        token = token.lower()
        return [s for s in self.symbols if token in s.name.lower()]

    def find_stub(self, token):
        token = token.lower()
        return [s for s in self.stubs if token in s.name.lower()]

    def in_comments(self, token):
        token = token.lower()
        return [(m, ln, t) for (m, ln, t) in self.comments if token in t.lower()]

    def summary(self):
        return {"modules": len(self.modules), "symbols": len(self.symbols),
                "comment_lines": len(self.comments), "stubs": len(self.stubs)}


def _is_constant_stub(node):
    """True if the function body is docstring-plus-comments and one literal return.

    This is the difference between a system that exists and a placeholder that
    satisfies a call site. Nemesis.charge_band is the motivating case: the name
    is there, the behaviour is not.
    """
    body = [n for n in node.body if not (isinstance(n, ast.Expr)
                                         and isinstance(n.value, ast.Constant)
                                         and isinstance(n.value.value, str))]
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return False
    return isinstance(body[0].value, ast.Constant)
