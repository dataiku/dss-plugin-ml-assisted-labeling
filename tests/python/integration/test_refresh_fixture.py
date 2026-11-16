"""Run the DeepHub refresh on a disposable copy of a prepared test fixture."""

import json
import os
import re
import uuid
import zipfile
from pathlib import Path

import pytest

from test_deephub_workflow import dataset_rows, session


def _project_scoped_filesystem(raw, name, connection, clone_key=None):
    path = raw.get("params", {}).get("path", "")
    suffix = r"(?:[A-Za-z0-9_-]+|\$\{odbId\})" if connection == "filesystem_folders" else r"[A-Za-z0-9_-]+"
    if clone_key is not None:
        safe_path = (connection == "filesystem_managed" and
                     re.fullmatch(r"MLLABELINGTEST_[A-F0-9]{12}", clone_key) and
                     re.fullmatch(r"[A-Za-z0-9_-]+", name) and
                     (path == "/{}.{}".format(clone_key, name) or
                      bool(re.fullmatch(r"\$\{projectKey\}/" + suffix, path))))
    else:
        safe_path = re.fullmatch(r"\$\{projectKey\}/" + suffix, path)
    assert raw.get("type") == "Filesystem"
    assert raw.get("params", {}).get("connection") == connection
    assert safe_path, "Fixture object {} must use a project-scoped filesystem path".format(name)
    assert not raw.get("partitioning", {}).get("dimensions"), "Partitioned fixture objects are not supported"


def _validate_fixture(project, duplicated=False):
    """Reject shared or fixed paths before a duplicate is created or refreshed."""
    for dataset in project.list_datasets(as_type="objects", include_shared=True):
        raw = dataset.get_settings().get_raw()
        assert raw.get("projectKey") == project.project_key
        assert raw.get("managed"), "Fixture dataset {} must be managed locally".format(dataset.name)
        _project_scoped_filesystem(raw, dataset.name, "filesystem_managed",
                                   clone_key=project.project_key if duplicated else None)
    config = project.get_webapp("xFUUnCL").get_settings().get_raw()["config"]
    for key in ("unlabeled", "labels_ds", "metadata_ds", "queries_ds"):
        assert config.get(key), "Fixture must have a local {}".format(key)
        assert "." not in config[key], "Fixture must have a local {}".format(key)
    folder = project.get_managed_folder(config["unlabeled"])
    folders = project.list_managed_folders()
    assert any(item["id"] == folder.id for item in folders), "Source image folder is not local"
    for item in folders:
        assert item.get("projectKey") == project.project_key, "Fixture folders must be local"
        current_folder = project.get_managed_folder(item["id"])
        _project_scoped_filesystem(current_folder.get_settings().get_raw(), current_folder.id, "filesystem_folders")

    # Only run the scenario shipped by this version of the plugin.
    archive = Path(__file__).resolve().parents[3] / "apps/object-detection/project.zip"
    with zipfile.ZipFile(archive) as z:
        expected = json.loads(z.read("project_config/scenarios/Refresh_deephub.json"))["params"]["steps"]
    actual = project.get_scenario("Refresh_deephub").get_settings().get_raw()["params"]["steps"]
    assert [(s["type"], s["params"]) for s in actual] == [(s["type"], s["params"]) for s in expected], \
        "Fixture refresh scenario differs from the plugin template"
    return config


def _producer(recipes, ref, kind, role):
    matches = [r for r in recipes if any(item.get("ref") == ref for item in
               r.get("outputs", {}).get(role, {}).get("items", []))]
    assert len(matches) == 1
    assert matches[0]["type"] == kind, "Expected {} recipe for {}".format(kind, ref)
    return matches[0]


def _input(recipe, role):
    items = recipe["inputs"][role]["items"]
    assert len(items) == 1
    assert "." not in items[0]["ref"], "Fixture inputs must be local"
    return items[0]["ref"]


@pytest.mark.parametrize("path", ["/shared/data", "${projectKey}/../shared", "${projectKey}/${other}"])
def test_project_scoped_path_guard_rejects_shared_or_indirect_paths(path):
    """Disallow fixed, traversal and project-variable paths before copying a fixture."""
    with pytest.raises(AssertionError, match="project-scoped filesystem"):
        _project_scoped_filesystem({"type": "Filesystem", "params": {
            "connection": "filesystem_managed", "path": path}}, "fixture", "filesystem_managed")


def test_clone_guard_accepts_only_its_own_exact_dataset_path():
    """Duplicated datasets must use DSS's exact target-project path."""
    clone = "MLLABELINGTEST_123456ABCDEF"
    def raw(path):
        return {"type": "Filesystem", "params": {"connection": "filesystem_managed", "path": path}}
    _project_scoped_filesystem(raw("/" + clone + ".labels"), "labels", "filesystem_managed", clone)
    _project_scoped_filesystem(raw("${projectKey}/labels"), "labels", "filesystem_managed", clone)
    for path, name, key in [
        ("/OTHER.labels", "labels", clone),
        ("/" + clone + ".other", "labels", clone),
        ("/" + clone + ".../shared", "../shared", clone),
        ("/OTHER.labels", "labels", "OTHER"),
        ("${projectKey}/../labels", "labels", clone),
    ]:
        dataset = raw(path)
        with pytest.raises(AssertionError, match="project-scoped filesystem"):
            _project_scoped_filesystem(dataset, name, "filesystem_managed", key)


def test_preflight_rejects_unconfigured_app(app_project):
    """An app without its DeepHub Flow is rejected before duplication or training."""
    with pytest.raises(AssertionError, match="local queries_ds"):
        _validate_fixture(app_project)


def test_refresh_retrains_and_restarts_webapp(dss_client):
    """Retrain and check scoring, query contents, session, and webapp restart."""
    source_key = os.environ.get("DSS_ML_LABELING_FIXTURE_PROJECT")
    if not source_key:
        pytest.fail("Set DSS_ML_LABELING_FIXTURE_PROJECT to a dedicated prepared test fixture project")
    source = dss_client.get_project(source_key)
    _validate_fixture(source)
    target_key = "MLLABELINGTEST_" + uuid.uuid4().hex[:12].upper()
    try:
        source.duplicate(target_key, target_key, duplication_mode="FULL", export_saved_models=True,
                         export_analysis_models=True, export_git_repository=False)
    except Exception as exc:
        raise RuntimeError("Fixture duplication failed; check for a partially created project {}".format(target_key)) from exc
    project = dss_client.get_project(target_key)
    safe_to_clear = False
    try:
        config = _validate_fixture(project, duplicated=True)
        safe_to_clear = True
        folder = project.get_managed_folder(config["unlabeled"])
        recipes = [r.get_settings().get_recipe_raw_definition() for r in project.list_recipes(as_type="objects")]
        queries = config["queries_ds"]
        sampler = _producer(recipes, queries, "CustomCode_deephub-object-detection-query-sampler", "queries")
        assert _input(sampler, "images") == folder.id
        scored = _input(sampler, "predictions")
        manifest = _input(sampler, "input_images")
        scoring = _producer(recipes, scored, "prediction_scoring", "main")
        assert _input(scoring, "main") == manifest
        assert _input(scoring, "data") == folder.id
        model_id = _input(scoring, "model")
        training = _producer(recipes, model_id, "prediction_training", "main")
        assert _input(training, "data") == folder.id
        converted = _input(training, "main")
        export = _producer(recipes, converted, "CustomCode_ml-assisted-labeling-deephub-export", "output_dataset")
        assert _input(export, "input_dataset") == config["labels_ds"]
        labels_before = dataset_rows(project.get_dataset(config["labels_ds"]))
        metadata_before = dataset_rows(project.get_dataset(config["metadata_ds"]))
        assert labels_before, "Fixture must contain labeled images"
        model = project.get_saved_model(model_id)
        old_version = model.get_active_version()["id"]
        old_session = session(project, queries)
        webapp = project.get_webapp("xFUUnCL")
        webapp.start_or_restart_backend().wait_for_result()
        old_backend = webapp.get_state().state["runId"]
        project.get_scenario("Refresh_deephub").run_and_wait()
        assert model.get_active_version()["id"] != old_version
        assert session(project, queries) == old_session + 1
        assert dataset_rows(project.get_dataset(config["labels_ds"])) == labels_before
        assert dataset_rows(project.get_dataset(config["metadata_ds"])) == metadata_before
        assert webapp.get_state().running
        assert webapp.get_state().state["runId"] != old_backend

        sampler_config = sampler["params"]["customConfig"]
        paths = [r[sampler_config["input_path_column"]] for r in dataset_rows(project.get_dataset(manifest))]
        predictions = [(r[sampler_config["path_column"]], r[sampler_config["prediction_column"]])
                       for r in dataset_rows(project.get_dataset(scored))]
        normalize = lambda path: "/" + path.lstrip("/")
        expected_paths = {normalize(path) for path in paths}
        assert len(expected_paths) == len(paths)
        assert {normalize(path) for path, _ in predictions} == expected_paths
        assert len(predictions) == len(paths)
        folder_paths = {normalize(item["path"]) for item in folder.list_contents()["items"]}
        assert expected_paths <= folder_paths
        expected = {}
        for path, prediction in predictions:
            detections = json.loads(prediction)
            assert isinstance(detections, list)
            confidences = [detection["confidence"] for detection in detections]
            assert all(0 <= confidence <= 1 for confidence in confidences)
            expected[normalize(path)] = 1 - max(confidences) if confidences else 1.0
        actual = {r["path"]: r["uncertainty"] for r in dataset_rows(project.get_dataset(queries))}
        assert expected
        assert actual == pytest.approx(expected)
    finally:
        try:
            if safe_to_clear:
                for item in project.list_managed_folders():
                    project.get_managed_folder(item["id"]).delete(drop_data=True)
        finally:
            project.delete(clear_managed_datasets=safe_to_clear, clear_output_managed_folders=False)
