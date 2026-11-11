#!/usr/bin/env python3
"""Check mise task wiring without running builds, board actions or network operations."""
import re
import shlex
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
count = 0
for config in [ROOT / 'mise.toml', ROOT / 'website/mise.toml']:
    tasks = tomllib.loads(config.read_text())['tasks']
    graph = {name: [] for name in tasks}
    for name, task in tasks.items():
        count += 1
        label = f'{config.relative_to(ROOT)}:{name}'
        if not task.get('description'):
            errors.append(f'{label}: missing description')
        commands = task.get('run', [])
        if isinstance(commands, str):
            commands = [commands]
        for command in commands:
            words = shlex.split(command)
            # Root convenience tasks delegate to the website's own task namespace.
            if len(words) >= 5 and words[:2] == ['mise', '-C'] and words[3] == 'run':
                other = config.parent / words[2] / 'mise.toml'
                if not other.is_file() or words[4] not in tomllib.loads(other.read_text())['tasks']:
                    errors.append(f'{label}: unknown delegated task {words[2]}:{words[4]}')
            for index, word in enumerate(words):
                if words[index:index + 2] == ['mise', 'run']:
                    target = words[index + 2] if len(words) > index + 2 else ''
                    if target not in tasks:
                        errors.append(f'{label}: unknown task {target}')
                    else:
                        graph[name].append(target)
                # Only executable source paths, not output filenames or glob patterns.
                if re.fullmatch(r'(?:scripts|firmware|enclosure|reverse-engineering|tools|website)/[\w/.-]+\.(?:py|sh|tsx?|mjs|js)', word):
                    if not (config.parent / word).is_file():
                        errors.append(f'{label}: missing script {word}')
        for target in task.get('depends', []):
            if target not in tasks:
                errors.append(f'{label}: unknown dependency {target}')
            else:
                graph[name].append(target)
    visited = set()
    def visit(name, active):
        if name in active:
            errors.append(f'{config.relative_to(ROOT)}: task cycle {" -> ".join([*active, name])}')
            return
        if name in visited:
            return
        for target in graph[name]:
            visit(target, [*active, name])
        visited.add(name)
    for name in graph:
        visit(name, [])
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print(f'Checked {count} tasks in root and website configs: descriptions, local script paths, task references and cycles.')
print('External tools, private deployment helpers, hardware and build artifacts require their own workflow checks.')
