"""Check the generated DSS requirements and development groups."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "code-env/python/spec").mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/generate_requirements.py", tmp_path / "scripts/generate_requirements.py")
    shutil.copyfile(ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "pyproject.toml").write_text(
        """[project]
dependencies = ["numpy>=1; python_version < '3.12'", "spacy[lookups,th]>=3.8"]
[dependency-groups]
dev = ["pytest>=8"]
integration = ["dataiku-api-client>=14"]
""", encoding="utf-8")
    return tmp_path


def run_generator(project, *args):
    return subprocess.run(
        [os.environ.get("UV", "uv"), "run", "--no-project", "--python", "3.11",
         "python", "scripts/generate_requirements.py", *args],
        cwd=project, text=True, capture_output=True,
    )


def test_runtime_and_group_dependencies_are_exported_without_changing_markers(project):
    result = run_generator(project)
    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "# Generated from pyproject.toml; do not edit directly.\n"
        "numpy>=1; python_version < '3.12'\n"
        "spacy[lookups,th]>=3.8\n"
    )
    groups = run_generator(project, "--group", "dev", "--group", "integration")
    assert groups.returncode == 0, groups.stderr
    assert groups.stdout == "pytest>=8\ndataiku-api-client>=14\n"
    assert not (project / "uv.lock").exists()


def test_check_and_failed_generation_do_not_change_the_requirements(project):
    requirements = project / "code-env/python/spec/requirements.txt"
    requirements.write_text("existing contents\n", encoding="utf-8")
    result = run_generator(project, "--check")
    assert result.returncode != 0
    assert requirements.read_text(encoding="utf-8") == "existing contents\n"

    generated = run_generator(project)
    assert generated.returncode == 0, generated.stderr
    requirements.write_text(generated.stdout, encoding="utf-8")
    assert run_generator(project, "--check").returncode == 0
    assert requirements.read_text(encoding="utf-8") == generated.stdout

    (project / "pyproject.toml").write_text("not valid TOML", encoding="utf-8")
    result = subprocess.run(["make", "requirements"], cwd=project, text=True, capture_output=True)
    assert result.returncode != 0
    assert requirements.read_text(encoding="utf-8") == generated.stdout
