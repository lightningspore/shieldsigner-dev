# SPDX-License-Identifier: MIT
"""import_module through the actual frozen/builtin importer; no host filesystem."""


def import_module(name, package=None):
    if not isinstance(name, str):
        raise TypeError('module name must be str')
    if name.startswith('.'):
        if not package:
            raise TypeError('package required for relative import')
        if not isinstance(package, str):
            raise TypeError('package must be str')
        level = 0
        while level < len(name) and name[level] == '.':
            level += 1
        parts = package.rsplit('.', level - 1)
        if len(parts) < level:
            raise ImportError('relative import beyond top level')
        suffix = name[level:]
        name = parts[0] + ('.' + suffix if suffix else '')
    return __import__(name, None, None, ('*',))
