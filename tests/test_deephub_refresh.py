"""The refresh must validate its Flow and stop before publishing stale queries."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python-lib"))
from lal.deephub_refresh import refresh_queries


def recipe(kind, inputs, output_role, output, config=None):
    return {"type": kind, "name": output, "params": {"customConfig": config or {}},
            "inputs": {k: {"items": [{"ref": v}]} for k, v in inputs.items()},
            "outputs": {output_role: {"items": [{"ref": output}]}}}


def flow():
    recipes = [
        recipe("CustomCode_deephub-object-detection-query-sampler", {"predictions": "scored", "input_images": "manifest", "images": "folder"}, "queries", "queries"),
        recipe("prediction_scoring", {"main": "manifest", "model": "model", "data": "folder"}, "main", "scored"),
        recipe("prediction_training", {"main": "converted", "data": "folder"}, "main", "model"),
        recipe("CustomCode_ml-assisted-labeling-deephub-export", {"input_dataset": "labels"}, "output_dataset", "converted"),
        recipe("list_folder_contents", {"main": "folder"}, "main", "all_files"),
        recipe("shaker", {"main": "all_files"}, "main", "manifest"),
    ]
    config = {"unlabeled": "folder", "labels_ds": "labels", "metadata_ds": "metadata", "queries_ds": "queries"}
    model = Mock()
    model.get_settings.return_value.get_raw.return_value = {"contentType": "prediction/deep_hub", "miniTask": {"predictionType": "DEEP_HUB_IMAGE_OBJECT_DETECTION", "targetVariable": "label"}}
    model.get_active_version.side_effect = [{"id": "old"}, {"id": "new"}]
    model.get_version_details.return_value.get_preprocessing_settings.return_value = {"target_remapping": [{"sourceValue": "cat"}]}
    project = Mock(project_key="PROJECT")
    project.get_webapp.return_value.get_settings.return_value.get_raw.return_value = {"config": config}
    project.list_recipes.return_value = [SimpleNamespace(get_settings=lambda r=r: SimpleNamespace(get_recipe_raw_definition=lambda: r)) for r in recipes]
    project.get_saved_model.return_value = model
    frames = {"labels": pd.DataFrame({"label": [json.dumps([{"label": "cat"}])]}),
              "metadata": pd.DataFrame({"session": [1]})}
    dataset = lambda name: SimpleNamespace(get_dataframe=lambda: frames[name])
    scenario = Mock()
    return SimpleNamespace(project=project, model=model, scenario=scenario, recipes=recipes,
                           frames=frames, dataset=dataset, config=config)


def run(flow):
    refresh_queries(flow.project, flow.scenario, flow.dataset, "webapp")


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.flow = flow()

    def test_refresh_builds_in_order(self):
        f = self.flow
        run(f)
        self.assertEqual([call.args[0] for call in f.scenario.method_calls],
                         ["converted", "model", "all_files", "manifest", "scored", "queries"])
        self.assertTrue(all(call.kwargs["build_mode"] == "NON_RECURSIVE_FORCED_BUILD"
                            for call in f.scenario.method_calls))

    def test_bad_setup_does_not_build(self):
        for change in ("folder", "category", "missing_queries", "duplicate", "malformed", "model_type", "target"):
            f = flow()
            if change == "folder":
                f.recipes[1]["inputs"]["data"]["items"][0]["ref"] = "another_folder"
            elif change == "category":
                f.frames["labels"]["label"] = ['[{"label":"dog"}]']
            elif change == "malformed":
                f.frames["labels"]["label"] = ['[null]']
            elif change == "missing_queries":
                f.config.pop("queries_ds")
            elif change == "model_type":
                f.model.get_settings.return_value.get_raw.return_value["miniTask"]["predictionType"] = "BINARY_CLASSIFICATION"
            elif change == "target":
                f.model.get_settings.return_value.get_raw.return_value["miniTask"]["targetVariable"] = "another_target"
            else:
                f.project.list_recipes.return_value.append(f.project.list_recipes.return_value[0])
            with self.subTest(change=change), self.assertRaises(ValueError):
                run(f)
            self.assertFalse(f.scenario.method_calls)

    def test_no_new_active_model_stops_before_scoring(self):
        f = self.flow
        f.model.get_active_version.side_effect = [{"id": "old"}, {"id": "old"}]
        with self.assertRaisesRegex(ValueError, "did not activate"):
            run(f)
        self.assertEqual([call.args[0] for call in f.scenario.method_calls], ["converted", "model"])

    def test_changed_labels_stop_before_queries(self):
        f = self.flow
        f.scenario.train_model.side_effect = lambda *a, **kw: f.frames["labels"].__setitem__("label", ['[]'])
        with self.assertRaisesRegex(ValueError, "Labels changed"):
            run(f)
        self.assertEqual(f.scenario.method_calls[-1].args[0], "scored")

    def test_failed_scoring_does_not_build_queries(self):
        f = self.flow
        def build(name, **kwargs):
            if name == "scored":
                raise RuntimeError("scoring failed")
        f.scenario.build_dataset.side_effect = build
        with self.assertRaisesRegex(RuntimeError, "scoring failed"):
            run(f)
        self.assertEqual(f.scenario.method_calls[-1].args[0], "scored")


if __name__ == "__main__":
    unittest.main()
