# SPDX-License-Identifier: MIT
"""Lazy imports and MicroPython-compatible formatting for actual source Views."""

import ast
from source_port import Port


class LazyPort(Port):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.imports = []

    def visit_FunctionDef(self, n):
        imports = {}

        class Imports(ast.NodeVisitor):
            def visit_FunctionDef(self, n):
                pass

            def visit_ClassDef(self, n):
                pass

            def visit_ImportFrom(inner, n):
                if n.module not in ('typing', '__future__'):
                    for a in n.names:
                        imports[a.asname or a.name] = (self.absolute(n), a.name)

            def visit_Import(inner, n):
                for a in n.names:
                    imports[a.asname or a.name.split('.')[0]] = (
                        a.name if a.asname else a.name.split('.')[0],
                        None,
                    )

        for b in n.body:
            Imports().visit(b)
        self.imports.append(imports)
        out = super().visit_FunctionDef(n)
        self.imports.pop()
        return out

    def visit_Name(self, n):
        if isinstance(n.ctx, ast.Load):
            for names, imports in reversed(list(zip(self.locals, self.imports))):
                if n.id in names:
                    return ast.copy_location(self.call(*imports[n.id]), n) if n.id in imports else n
        return super().visit_Name(n)

    def visit_JoinedStr(self, n):
        args = []

        def template(parts):
            out = ''
            for part in parts:
                if isinstance(part, ast.Constant):
                    out += part.value.replace('{', '{{').replace('}', '}}')
                else:
                    index = len(args)
                    args.append(self.visit(part.value))
                    out += (
                        '{'
                        + str(index)
                        + (('!' + chr(part.conversion)) if part.conversion != -1 else '')
                    )
                    if part.format_spec is not None:
                        out += ':' + template(part.format_spec.values)
                    out += '}'
            return out

        text = template(n.values)
        return ast.copy_location(
            ast.Call(
                func=ast.Attribute(value=ast.Constant(text), attr='format', ctx=ast.Load()),
                args=args,
                keywords=[],
            ),
            n,
        )

    def visit_ImportFrom(self, n):
        return None if self.locals else super().visit_ImportFrom(n)

    def visit_Import(self, n):
        return None if self.locals else super().visit_Import(n)
