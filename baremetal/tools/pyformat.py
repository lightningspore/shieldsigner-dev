# SPDX-License-Identifier: MIT
"""Format generated Python with ruff as it is written.

Importing this module (every tools/prepare_*.py does) wraps Path.write_text so
that any `.py` file inside baremetal/ is passed through `ruff format` with the
repository's ruff.toml before it reaches disk. Excluded paths (vendored
upstream code) are written unchanged. Provenance hashes computed from the file
on disk therefore describe the formatted output, and regenerating is
reproducible.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUFF = ["uvx", "--quiet", "ruff@0.17.5"]


def format_source(text, path):
    """Return `text` formatted as the file at `path` (unchanged if excluded)."""
    path = Path(path).resolve()
    result = subprocess.run(
        RUFF
        + [
            "format",
            "--config",
            str(ROOT / "ruff.toml"),
            "--force-exclude",
            "--stdin-filename",
            str(path),
            "-",
        ],
        input=text,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise RuntimeError("ruff format failed for %s:\n%s" % (path, result.stderr))
    return result.stdout


_write_text = Path.write_text


def _formatting_write_text(self, data, *args, **kwargs):
    target = self.resolve()
    if target.suffix == ".py" and ROOT in target.parents:
        data = format_source(data, target)
    return _write_text(self, data, *args, **kwargs)


Path.write_text = _formatting_write_text


class _Whole:
    """Minimal re.Match stand-in: group() returns the replaced source."""

    def __init__(self, text):
        self._text = text

    def group(self, index=0):
        if index:
            raise IndexError(index)
        return self._text


def subn_assignment(name, repl, text, flags=0):
    """Layout-independent `re.subn(r'^NAME = .+$', repl, text, flags=re.M)`.

    Replaces the whole top-level `NAME = ...` statement (however many lines the
    formatter spread it over, plus its trailing comment) with repl(match).
    """
    import ast

    lines = text.split('\n')
    for node in ast.parse(text).body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
        ):
            start, end = node.lineno - 1, node.end_lineno
            old = '\n'.join(lines[start:end])
            new = repl(_Whole(old)) if callable(repl) else repl
            return '\n'.join(lines[:start] + [new] + lines[end:]), 1
    return text, 0


def sub_assignment(name, repl, text, flags=0):
    return subn_assignment(name, repl, text, flags)[0]
