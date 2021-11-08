# -*- coding: utf-8 -*-

import json
import logging
import dataiku
from dataiku.customrecipe import get_recipe_config, get_input_names_for_role, get_output_names_for_role


def format_labeling_plugin_annotations(image_annotations):
    """ Format labeling annotations to be compatible with dss object detection (deephub)"""

    deephub_image_annotations = []
    # if images were skipped during labeling plugin, their annotations is nan:
    image_annotations = json.loads(image_annotations) if isinstance(image_annotations, str) else []
    for annotation in image_annotations:
        deephub_image_annotations.append(
            {"bbox": [annotation["left"], annotation["top"], annotation["width"], annotation["height"]],
             "category": annotation[target_column]
             })
    image_annotations = json.dumps(deephub_image_annotations)
    return image_annotations


dataset_df = dataiku.Dataset(get_input_names_for_role("input_dataset")[0]).get_dataframe()

target_column = get_recipe_config()["target_column"]
if target_column not in dataset_df.columns:
    raise Exception("Column {} not in dataset with columns [{}]".format(target_column, dataset_df.columns.tolist()))

logging.info("Annotations target column chosen: {}".format(target_column))

dataset_df[target_column] = dataset_df[target_column].map(format_labeling_plugin_annotations)

output_dataset = dataiku.Dataset(get_output_names_for_role("output_dataset")[0])
output_dataset.write_with_schema(dataset_df)
