"""Run the object-labeling app's explicitly configured DeepHub refresh."""

import hashlib
import json

import pandas as pd


def refresh_queries(project, scenario, dataset, webapp_id):
    config = project.get_webapp(webapp_id).get_settings().get_raw()["config"]
    project_key = project.project_key

    def local(ref):
        if not ref:
            raise ValueError("Configure the image folder, labels and queries in the labeling webapp settings.")
        if "." in ref:
            prefix, ref = ref.split(".", 1)
            if prefix != project_key:
                raise ValueError("Refresh only supports Flow objects in this project.")
        return ref

    folder = local(config.get("unlabeled"))
    labels = local(config.get("labels_ds"))
    metadata = local(config.get("metadata_ds"))
    queries = local(config.get("queries_ds"))
    label_column = config.get("label_col_name", "label")
    recipes = [recipe.get_settings().get_recipe_raw_definition()
               for recipe in project.list_recipes(as_type="objects")]

    def role(recipe, direction, name):
        items = recipe.get(direction, {}).get(name, {}).get("items", [])
        if len(items) != 1:
            raise ValueError("Recipe %s needs exactly one %s %s." % (recipe.get("name"), direction, name))
        return local(items[0].get("ref"))

    def producer(ref, recipe_type, output_role):
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

    def require(actual, expected, description):
        if actual != expected:
            raise ValueError("%s must use %s; found %s." % (description, expected, actual))

    sampler = producer(queries, "CustomCode_deephub-object-detection-query-sampler", "queries")
    require(role(sampler, "inputs", "images"), folder, "Sampler image folder")
    manifest = role(sampler, "inputs", "input_images")
    scored = role(sampler, "inputs", "predictions")
    scoring = producer(scored, "prediction_scoring", "main")
    require(role(scoring, "inputs", "main"), manifest, "Scoring input")
    require(role(scoring, "inputs", "data"), folder, "Scoring image folder")
    model_id = role(scoring, "inputs", "model")
    training = producer(model_id, "prediction_training", "main")
    require(role(training, "inputs", "data"), folder, "Training image folder")
    converted = role(training, "inputs", "main")
    conversion = producer(converted, "CustomCode_ml-assisted-labeling-deephub-export", "output_dataset")
    require(role(conversion, "inputs", "input_dataset"), labels, "Annotation conversion input")
    require(conversion.get("params", {}).get("customConfig", {}).get("target_column", "label"),
            label_column, "Annotation conversion target column")

    # Only these one-input recipes are safe to rebuild without following arbitrary Flow branches.
    manifest_builds = []
    current = manifest
    while True:
        if current in manifest_builds:
            raise ValueError("The image manifest recipe chain contains a cycle.")
        manifest_builds.append(current)
        candidates = [r for r in recipes if any(i.get("ref") in (current, project_key + "." + current)
                      for i in r.get("outputs", {}).get("main", {}).get("items", []))]
        if len(candidates) != 1:
            raise ValueError("The image manifest must have a unique recipe for %s." % current)
        kind = candidates[0].get("type")
        if kind not in ("list_folder_contents", "shaker", "sampling"):
            raise ValueError("Build the image manifest from List folder contents, optionally followed by Prepare or Sample/Filter.")
        recipe = producer(current, kind, "main")
        if set(recipe.get("inputs", {})) != {"main"}:
            raise ValueError("Image manifest recipes must have exactly one input.")
        source = role(recipe, "inputs", "main")
        if kind == "list_folder_contents":
            require(source, folder, "Image manifest folder")
            break
        current = source

    objects = [labels, metadata, converted, scored, queries] + manifest_builds
    if len(set(objects)) != len(objects):
        raise ValueError("Labels, metadata and refresh datasets must be distinct.")

    model = project.get_saved_model(model_id)
    model_settings = model.get_settings().get_raw()
    if (model_settings.get("contentType") != "prediction/deep_hub" or
            model_settings.get("miniTask", {}).get("predictionType") != "DEEP_HUB_IMAGE_OBJECT_DETECTION"):
        raise ValueError("The scoring model must be a native DeepHub object detection model.")
    require(model_settings["miniTask"].get("targetVariable"), label_column, "Model target column")
    active = model.get_active_version()
    if not active or not active.get("id"):
        raise ValueError("Deploy and activate the DeepHub model before refreshing queries.")
    version_id = active["id"]
    preprocessing = model.get_version_details(version_id).get_preprocessing_settings()
    remapping = preprocessing.get("target_remapping") if preprocessing else None
    categories = {entry.get("sourceValue") for entry in (remapping or []) if entry.get("sourceValue")}
    if not categories:
        raise ValueError("The active model has no target category mapping; check the deployed DeepHub model.")
    label_frame = dataset(labels).get_dataframe()
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

    def signature(initial_labels=None):
        digest = hashlib.sha256()
        for name in (labels, metadata):
            frame = initial_labels if name == labels and initial_labels is not None else dataset(name).get_dataframe()
            digest.update(pd.util.hash_pandas_object(frame, index=True).values.tobytes())
        return digest.digest()

    initial_signature = signature(label_frame)
    build_options = {"build_mode": "NON_RECURSIVE_FORCED_BUILD"}
    scenario.build_dataset(converted, **build_options)
    scenario.train_model(model_id, **build_options)
    new_active = model.get_active_version()
    if not new_active or not new_active.get("id") or new_active["id"] == version_id:
        raise ValueError("Training did not activate a new model version; queries were not refreshed.")
    for name in reversed(manifest_builds):
        scenario.build_dataset(name, **build_options)
    scenario.build_dataset(scored, **build_options)
    if signature() != initial_signature:
        raise ValueError("Labels changed during refresh. Pause labeling and run the refresh again.")
    scenario.build_dataset(queries, **build_options)
