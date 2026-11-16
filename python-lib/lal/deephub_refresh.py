"""Run the object-labeling app's explicitly configured DeepHub refresh."""

import hashlib
import json

import pandas as pd


def _local(project_key, ref):
    if not ref:
        raise ValueError("Configure the image folder, labels and queries in the labeling webapp settings.")
    if "." in ref:
        prefix, ref = ref.split(".", 1)
        if prefix != project_key:
            raise ValueError("Refresh only supports Flow objects in this project.")
    return ref


def _role(project_key, recipe, direction, name):
    items = recipe.get(direction, {}).get(name, {}).get("items", [])
    if len(items) != 1:
        raise ValueError("Recipe %s needs exactly one %s %s." % (recipe.get("name"), direction, name))
    return _local(project_key, items[0].get("ref"))


def _producer(project_key, recipes, ref, recipe_type, output_role):
    matches = []
    for recipe in recipes:
        for role_name, outputs in recipe.get("outputs", {}).items():
            for output in outputs.get("items", []):
                if output.get("ref") in (ref, project_key + "." + ref):
                    matches.append((recipe, role_name))
    if len(matches) != 1 or matches[0][0].get("type") != recipe_type or matches[0][1] != output_role:
        raise ValueError("Expected exactly one %s recipe producing %s." % (recipe_type, ref))
    recipe = matches[0][0]
    output = recipe["outputs"][output_role]["items"]
    if (len(output) != 1 or output[0].get("appendMode", False) or
            sum(len(role.get("items", [])) for role in recipe["outputs"].values()) != 1):
        raise ValueError("Recipe output %s must overwrite a single dataset." % ref)
    return recipe


def _require(actual, expected, description):
    if actual != expected:
        raise ValueError("%s must use %s; found %s." % (description, expected, actual))


def _manifest_builds(project_key, recipes, manifest, folder):
    # Only these one-input recipes are safe to rebuild without following arbitrary Flow branches.
    builds = []
    current = manifest
    while True:
        if current in builds:
            raise ValueError("The image manifest recipe chain contains a cycle.")
        builds.append(current)
        candidates = [r for r in recipes if any(i.get("ref") in (current, project_key + "." + current)
                      for i in r.get("outputs", {}).get("main", {}).get("items", []))]
        if len(candidates) != 1:
            raise ValueError("The image manifest must have a unique recipe for %s." % current)
        kind = candidates[0].get("type")
        if kind not in ("list_folder_contents", "shaker", "sampling"):
            raise ValueError("Build the image manifest from List folder contents, optionally followed by Prepare or Sample/Filter.")
        recipe = _producer(project_key, recipes, current, kind, "main")
        if set(recipe.get("inputs", {})) != {"main"}:
            raise ValueError("Image manifest recipes must have exactly one input.")
        source = _role(project_key, recipe, "inputs", "main")
        if kind == "list_folder_contents":
            _require(source, folder, "Image manifest folder")
            break
        current = source
    return builds


def _model_categories(project, project_key, model_id, label_column):
    model = project.get_saved_model(model_id)
    model_settings = model.get_settings().get_raw()
    if (model_settings.get("contentType") != "prediction/deep_hub" or
            model_settings.get("miniTask", {}).get("predictionType") != "DEEP_HUB_IMAGE_OBJECT_DETECTION"):
        raise ValueError("The scoring model must be a native DeepHub object detection model.")
    _require(model_settings["miniTask"].get("targetVariable"), label_column, "Model target column")
    active = model.get_active_version()
    if not active or not active.get("id"):
        raise ValueError("Deploy and activate the DeepHub model before refreshing queries.")
    version_id = active["id"]
    # The DeepHub model details endpoint works, but the SDK's extra snippet request does not.
    details = model.client._perform_json(
        "GET", "/projects/%s/savedmodels/%s/versions/%s/details" % (project_key, model_id, version_id))
    preprocessing = details.get("preprocessing")
    remapping = preprocessing.get("target_remapping") if preprocessing else None
    categories = {entry.get("sourceValue") for entry in (remapping or []) if entry.get("sourceValue")}
    if not categories:
        raise ValueError("The active model has no target category mapping; check the deployed DeepHub model.")
    return model, version_id, categories


def _validate_annotations(label_frame, label_column, categories):
    if label_column not in label_frame:
        raise ValueError("The labeling dataset does not contain column %s." % label_column)
    for value in label_frame[label_column].dropna():
        try:
            annotations = json.loads(value)
            if not isinstance(annotations, list) or any(not isinstance(item, dict) for item in annotations):
                raise ValueError("Expected a list of annotation objects")
            missing = {annotation["label"] for annotation in annotations} - categories
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("Invalid annotations in the labeling dataset: %s" % exc)
        if missing:
            raise ValueError("The model does not recognize these annotation categories: %s. Update and redeploy the model." % ", ".join(sorted(missing)))


def _signature(dataset, labels, metadata, initial_labels=None):
    digest = hashlib.sha256()
    for name in (labels, metadata):
        frame = initial_labels if name == labels and initial_labels is not None else dataset(name).get_dataframe()
        digest.update(pd.util.hash_pandas_object(frame, index=True).values.tobytes())
    return digest.digest()


def refresh_queries(project, scenario, dataset, webapp_id):
    config = project.get_webapp(webapp_id).get_settings().get_raw()["config"]
    project_key = project.project_key
    folder = _local(project_key, config.get("unlabeled"))
    labels = _local(project_key, config.get("labels_ds"))
    metadata = _local(project_key, config.get("metadata_ds"))
    queries = _local(project_key, config.get("queries_ds"))
    label_column = config.get("label_col_name", "label")
    recipes = [recipe.get_settings().get_recipe_raw_definition()
               for recipe in project.list_recipes(as_type="objects")]

    sampler = _producer(project_key, recipes, queries, "CustomCode_deephub-object-detection-query-sampler", "queries")
    _require(_role(project_key, sampler, "inputs", "images"), folder, "Sampler image folder")
    manifest = _role(project_key, sampler, "inputs", "input_images")
    scored = _role(project_key, sampler, "inputs", "predictions")
    scoring = _producer(project_key, recipes, scored, "prediction_scoring", "main")
    _require(_role(project_key, scoring, "inputs", "main"), manifest, "Scoring input")
    _require(_role(project_key, scoring, "inputs", "data"), folder, "Scoring image folder")
    model_id = _role(project_key, scoring, "inputs", "model")
    training = _producer(project_key, recipes, model_id, "prediction_training", "main")
    _require(_role(project_key, training, "inputs", "data"), folder, "Training image folder")
    converted = _role(project_key, training, "inputs", "main")
    conversion = _producer(project_key, recipes, converted, "CustomCode_ml-assisted-labeling-deephub-export", "output_dataset")
    _require(_role(project_key, conversion, "inputs", "input_dataset"), labels, "Annotation conversion input")
    _require(conversion.get("params", {}).get("customConfig", {}).get("target_column", "label"),
             label_column, "Annotation conversion target column")

    manifest_builds = _manifest_builds(project_key, recipes, manifest, folder)
    objects = [labels, metadata, converted, scored, queries] + manifest_builds
    if len(set(objects)) != len(objects):
        raise ValueError("Labels, metadata and refresh datasets must be distinct.")

    model, version_id, categories = _model_categories(project, project_key, model_id, label_column)
    label_frame = dataset(labels).get_dataframe()
    _validate_annotations(label_frame, label_column, categories)

    initial_signature = _signature(dataset, labels, metadata, label_frame)
    build_options = {"build_mode": "NON_RECURSIVE_FORCED_BUILD"}
    scenario.build_dataset(converted, **build_options)
    scenario.train_model(model_id, **build_options)
    new_active = model.get_active_version()
    if not new_active or not new_active.get("id") or new_active["id"] == version_id:
        raise ValueError("Training did not activate a new model version; queries were not refreshed.")
    for name in reversed(manifest_builds):
        scenario.build_dataset(name, **build_options)
    scenario.build_dataset(scored, **build_options)
    if _signature(dataset, labels, metadata) != initial_signature:
        raise ValueError("Labels changed during refresh. Pause labeling and run the refresh again.")
    scenario.build_dataset(queries, **build_options)
