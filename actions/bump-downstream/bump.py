#!/usr/bin/env python3
"""Moves a downstream manifest to a new release of a crate.

    bump.py <Cargo.toml> <crate> <version> [<crate's dependencies JSON>]

Sets every requirement on <crate> to <version>, keeping its `=` if it had
one. When the crates.io dependency list of the release is given, each
dependency the downstream also names (by package name, so renames such as
`gpui_platform = { package = "gpui-pre-platform", ... }` count) moves to the
version the release requires, when that is newer than the downstream's.
Without that, a crate that pins its runtime exactly (gpuicn pins GPUI Kit)
could never resolve next to the downstream's old pin of the same runtime.

Prints each moved package name, one per line, for `cargo update -p`.
"""

import json
import re
import sys

VERSION = re.compile(r'(\bversion\s*=\s*")([=^~]?)([^"]*)(")')
PACKAGE = re.compile(r'\bpackage\s*=\s*"([^"]+)"')
TABLE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
ENTRY = re.compile(r'^(\s*)([A-Za-z0-9_-]+|"[^"]+")(\s*=\s*)(.*)$')


def parse(version):
    """The numeric part of a version, for comparison; None if it has none."""
    parts = re.match(r"\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?", version)
    if not parts:
        return None
    return tuple(int(p or 0) for p in parts.groups())


def is_dependency_table(name):
    last = name.split(".")[-1].strip()
    return last.endswith("dependencies")


def wanted_versions(crate, version, deps):
    """Package name -> (operator, version) the downstream should require."""
    wanted = {crate: version}
    for dep in deps:
        if dep.get("kind") == "dev":
            continue
        req = dep["req"].strip()
        match = re.fullmatch(r"([=^~]?)\s*(\d+(?:\.\d+){0,2}(?:[-+][^\s,]*)?)", req)
        if match:  # a single bound such as =0.9.1 or ^0.7.0
            wanted.setdefault(dep["crate_id"], match.group(2))
    return wanted


def bump(text, crate, wanted):
    moved, seen = [], set()
    lines = text.split("\n")
    # Inline entries: `name = "1.0"` and `name = { version = "1.0", ... }`
    # in any [*dependencies] table.
    table = None
    for i, line in enumerate(lines):
        header = TABLE.match(line)
        if header:
            table = header.group(1).strip()
            continue
        if table is None or not is_dependency_table(table):
            continue
        entry = ENTRY.match(line)
        if not entry:
            continue
        key = entry.group(2).strip('"')
        value = entry.group(4)
        package = key
        if value.lstrip().startswith("{"):
            renamed = PACKAGE.search(value)
            if renamed:
                package = renamed.group(1)
        if package not in wanted:
            continue
        seen.add(package)
        new = rewrite(value, package == crate, wanted[package])
        if new != value:
            lines[i] = entry.group(1) + entry.group(2) + entry.group(3) + new
            moved.append(package)
    # [dependencies.name] tables, whose `package` line may come before or
    # after their `version` line.
    i = 0
    while i < len(lines):
        header = TABLE.match(lines[i])
        if not header:
            i += 1
            continue
        parts = [p.strip().strip('"') for p in header.group(1).split(".")]
        start = i + 1
        end = start
        while end < len(lines) and not TABLE.match(lines[end]):
            end += 1
        if len(parts) >= 2 and is_dependency_table(".".join(parts[:-1])):
            package = parts[-1]
            for line in lines[start:end]:
                renamed = PACKAGE.search(line)
                if renamed and line.lstrip().startswith("package"):
                    package = renamed.group(1)
            if package in wanted:
                seen.add(package)
                for j in range(start, end):
                    if lines[j].lstrip().startswith("version"):
                        new = rewrite(lines[j], package == crate, wanted[package])
                        if new != lines[j]:
                            lines[j] = new
                            moved.append(package)
        i = end
    return "\n".join(lines), moved, seen


def rewrite(value, is_crate, version):
    """Sets the version in a requirement string or inline table."""
    if value.lstrip().startswith('"'):
        match = re.match(r'(\s*")([=^~]?)([^"]*)(")', value)
        if not match:
            return value
        op, current = match.group(2), match.group(3)
        if not is_crate and not newer(version, current):
            return value
        return match.group(1) + op + version + match.group(4) + value[match.end():]
    match = VERSION.search(value)
    if not match:
        return value
    op, current = match.group(2), match.group(3)
    if not is_crate and not newer(version, current):
        return value
    return value[: match.start()] + match.group(1) + op + version + match.group(4) + value[match.end():]


def newer(version, current):
    a, b = parse(version), parse(current)
    return a is not None and b is not None and a > b


def main():
    manifest, crate, version = sys.argv[1:4]
    deps = json.load(open(sys.argv[4]))["dependencies"] if len(sys.argv) > 4 else []
    text = open(manifest).read()
    text, moved, seen = bump(text, crate, wanted_versions(crate, version, deps))
    if crate not in seen:
        sys.exit(f"No requirement on {crate} in {manifest}")
    open(manifest, "w").write(text)
    for package in dict.fromkeys(moved):
        print(package)


if __name__ == "__main__":
    main()
