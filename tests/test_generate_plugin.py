"""Check generated DSS plugin metadata and archive safeguards."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]


def generate(project, *args):
    return subprocess.run(
        [os.environ.get("UV", "uv"), "run", "--no-project", "--python", "3.11",
         "python", "scripts/generate_plugin.py", *args],
        cwd=project, text=True, capture_output=True,
    )


@pytest.fixture
def project(tmp_path):
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts/generate_plugin.py", tmp_path / "scripts/generate_plugin.py")
    shutil.copyfile(ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "pyproject.toml").write_text(
        '''[project]
name = "different-project-name"
version = "5.0.0"
[tool.dataiku-plugin]
id = "plugin-id"
extra = "supported"
[tool.dataiku-plugin.meta]
label = 'A "label" with café'
tags = ["One", "Two"]
''', encoding="utf-8")
    return tmp_path


def test_manifest_preserves_metadata_and_uses_project_version(project):
    result = generate(project)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "id": "plugin-id", "version": "5.0.0", "extra": "supported",
        "meta": {"label": 'A "label" with café', "tags": ["One", "Two"]},
    }
    (project / "plugin.json").write_text(result.stdout, encoding="utf-8")
    assert generate(project, "--check").returncode == 0

    pyproject = project / "pyproject.toml"
    pyproject.write_text(pyproject.read_text().replace('version = "5.0.0"', 'version = "5.1.0"'))
    assert generate(project, "--check").returncode != 0
    assert (project / "plugin.json").read_text(encoding="utf-8") == result.stdout


def test_duplicate_version_is_rejected(project):
    pyproject = project / "pyproject.toml"
    pyproject.write_text(pyproject.read_text().replace('id = "plugin-id"',
                                                       'id = "plugin-id"\nversion = "other"'))
    assert generate(project).returncode != 0


def test_packaging_rejects_dirty_or_stale_committed_manifest(project):
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    generated = generate(project)
    assert generated.returncode == 0, generated.stderr
    (project / "plugin.json").write_text(generated.stdout, encoding="utf-8")
    (project / "tests").mkdir()
    (project / "tests/sample.txt").write_text("excluded from archive")
    subprocess.run(["git", "add", "Makefile", "plugin.json", "pyproject.toml", "scripts/generate_plugin.py", "tests"],
                   cwd=project, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "fixture"], cwd=project, check=True)
    assert subprocess.run(["make", "check-plugin-head"], cwd=project, capture_output=True).returncode == 0

    dist = project / "dist"
    (project / "release_info.json").write_text("keep")
    package = subprocess.run(["make", "plugin"], cwd=project, text=True, capture_output=True)
    assert package.returncode == 0, package.stdout + package.stderr
    with ZipFile(dist / "dss-plugin-plugin-id-5.0.0.zip") as archive:
        assert json.loads(archive.read("plugin.json")) == json.loads(generated.stdout)
        release_info = json.loads(archive.read("release_info.json"))
        assert release_info["last_commit_id"] == subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project, text=True).strip()
        assert "tests/sample.txt" not in archive.namelist()
    assert (project / "release_info.json").read_text() == "keep"
    (dist / "sentinel").write_text("keep")
    pyproject = project / "pyproject.toml"
    original = pyproject.read_text()
    pyproject.write_text(original.replace('version = "5.0.0"', 'version = "5.1.0"'))
    (project / "plugin.json").write_text(generate(project).stdout, encoding="utf-8")
    assert subprocess.run(["make", "plugin"], cwd=project, capture_output=True).returncode != 0
    assert (dist / "sentinel").read_text() == "keep"
    assert (project / "release_info.json").read_text() == "keep"

    pyproject.write_text(original)
    manifest = json.loads(generated.stdout)
    manifest["version"] = "4.0.0"
    (project / "plugin.json").write_text(json.dumps(manifest, indent=4, ensure_ascii=False) + "\n")
    subprocess.run(["git", "add", "plugin.json"], cwd=project, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "stale manifest"], cwd=project, check=True)
    (project / "plugin.json").write_text(generated.stdout, encoding="utf-8")
    assert subprocess.run(["make", "plugin"], cwd=project, capture_output=True).returncode != 0
    assert (dist / "sentinel").read_text() == "keep"
    assert (project / "release_info.json").read_text() == "keep"
