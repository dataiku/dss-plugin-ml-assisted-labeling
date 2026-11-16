"""Exercise the installed plugin's annotation and sampler recipes on DSS."""

import csv
import io
import json

import pytest
from dataikuapi.utils import DataikuException


def upload_csv(project, name, rows):
    buffer = io.StringIO(newline="")
    csv.writer(buffer).writerows(rows)
    dataset = project.create_upload_dataset(name)
    dataset.uploaded_add_file(io.BytesIO(buffer.getvalue().encode("utf-8")), "input.csv")
    dataset.autodetect_settings().save()
    return dataset


def managed_dataset(project, name):
    connection = project.get_dataset("object-labels").get_settings().get_raw()["params"]["connection"]
    return project.new_managed_dataset(name).with_store_into(connection).create()


def custom_recipe(project, name, recipe_type, inputs, output_role, output, config):
    recipe = project.create_recipe({
        "name": name,
        "type": recipe_type,
        "inputs": {role: {"items": [{"ref": ref}]} for role, ref in inputs.items()},
        "outputs": {output_role: {"items": [{"ref": output, "appendMode": False}]}},
    }, {})
    settings = recipe.get_settings()
    settings.get_recipe_raw_definition()["params"]["customConfig"] = config
    settings.save()
    return recipe


def dataset_rows(dataset):
    columns = [column["name"] for column in dataset.get_schema()["columns"]]
    return [dict(zip(columns, row)) for row in dataset.iter_rows()]


def session(project, queries):
    return project.get_variables()["standard"].get(
        "ML-ASSISTED-LABELING__{}__session".format(queries), 0)


def test_sampler_scores_images_and_failed_run_does_not_advance_session(app_project):
    """Run the installed sampler recipe, including a missing-prediction failure."""
    project = app_project
    folder = project.get_managed_folder("Sz5YxlDP")
    for name in ("a.jpg", "b.jpg"):
        folder.put_file(name, io.BytesIO(b"image contents are not read by the sampler"))
    upload_csv(project, "test_paths", [("path", "kind"), ("a.jpg", "image"), ("b.jpg", "image")])
    upload_csv(project, "test_scored", [("path", "prediction"),
               ("a.jpg", '[{"confidence": 0.8}]'), ("b.jpg", "[]")])
    upload_csv(project, "test_incomplete", [("path", "prediction"),
               ("a.jpg", '[{"confidence": 0.8}]')])
    output = managed_dataset(project, "test_queries")
    sampler = custom_recipe(project, "test_sampler", "CustomCode_deephub-object-detection-query-sampler",
                            {"input_images": "test_paths", "predictions": "test_scored", "images": folder.id},
                            "queries", output.name,
                            {"input_path_column": "path", "path_column": "path", "prediction_column": "prediction"})

    before = session(project, output.name)
    sampler.run()
    result = {row["path"]: row["uncertainty"] for row in dataset_rows(output)}
    assert result == {"/a.jpg": pytest.approx(0.2), "/b.jpg": pytest.approx(1.0)}
    assert session(project, output.name) == before + 1

    settings = sampler.get_settings()
    settings.get_recipe_raw_definition()["inputs"]["predictions"]["items"][0]["ref"] = "test_incomplete"
    settings.save()
    with pytest.raises(DataikuException):
        sampler.run()
    assert session(project, output.name) == before + 1
    assert {row["path"]: row["uncertainty"] for row in dataset_rows(output)} == result


def test_annotation_export_converts_labeling_boxes(app_project):
    """Run the installed annotation conversion recipe on labeling-format boxes."""
    boxes = [{"top": 2, "left": 3, "width": 10, "height": 12, "label": "cat"}]
    upload_csv(app_project, "test_labels", [("path", "label"), ("a.jpg", json.dumps(boxes))])
    output = managed_dataset(app_project, "test_annotations")
    recipe = custom_recipe(app_project, "test_export", "CustomCode_ml-assisted-labeling-deephub-export",
                           {"input_dataset": "test_labels"}, "output_dataset", output.name,
                           {"target_column": "label"})
    recipe.run()
    rows = dataset_rows(output)
    assert len(rows) == 1
    assert rows[0]["path"] == "a.jpg"
    assert json.loads(rows[0]["label"]) == [{"bbox": [3, 2, 10, 12], "category": "cat"}]


