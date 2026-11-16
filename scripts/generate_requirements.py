"""Print plugin requirements, or verify the checked-in DSS requirements."""

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.group and args.check:
        parser.error("--check cannot be used with --group")

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = ([dependency for group in args.group for dependency in data["dependency-groups"][group]]
                    if args.group else data["project"]["dependencies"])
    if not all(isinstance(dependency, str) for dependency in dependencies):
        raise ValueError("Dependency group includes must be expanded before exporting requirements")
    header = "" if args.group else "# Generated from pyproject.toml; do not edit directly.\n"
    generated = header + "\n".join(dependencies) + "\n"
    if args.check:
        path = ROOT / "code-env/python/spec/requirements.txt"
        if not path.exists() or path.read_text(encoding="utf-8") != generated:
            print("Generated requirements are out of date; run make requirements", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(generated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
