"""Generate or check the DSS plugin manifest from pyproject.toml."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def render(pyproject):
    data = tomllib.loads(pyproject)
    plugin = dict(data["tool"]["dataiku-plugin"])
    if "version" in plugin:
        raise ValueError("Set the plugin version in [project], not [tool.dataiku-plugin]")
    if "meta" not in plugin:
        raise ValueError("Plugin metadata is missing")
    manifest = {"id": plugin.pop("id"), "version": data["project"]["version"], **plugin}
    return json.dumps(manifest, indent=4, ensure_ascii=False) + "\n"


def main():
    parser = argparse.ArgumentParser()
    checks = parser.add_mutually_exclusive_group()
    checks.add_argument("--check", action="store_true")
    checks.add_argument("--check-head", action="store_true")
    args = parser.parse_args()

    if args.check_head:
        try:
            pyproject = subprocess.check_output(["git", "show", "HEAD:pyproject.toml"], cwd=ROOT, text=True)
            manifest = subprocess.check_output(["git", "show", "HEAD:plugin.json"], cwd=ROOT, text=True)
            generated = render(pyproject)
        except (subprocess.CalledProcessError, KeyError, ValueError):
            print("HEAD does not contain valid plugin metadata; commit it before packaging", file=sys.stderr)
            return 1
    else:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        generated = render(pyproject)
        manifest_path = ROOT / "plugin.json"
        manifest = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else None

    if args.check or args.check_head:
        if manifest != generated:
            print("Generated plugin.json is out of date; run make plugin-json and commit it before packaging"
                  if args.check_head else "Generated plugin.json is out of date; run make plugin-json", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(generated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
