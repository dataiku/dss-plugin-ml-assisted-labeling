# -*- coding: utf-8 -*-

import json
import logging
import dataiku
from dataiku.customrecipe import get_recipe_config, get_input_names_for_role, get_output_names_for_role


def format_labeling_plugin_annotations(image_annotations):
    """ Format labeling annotations to be compatible with dss object detection (deephub)"""

    deephub_image_annotations = []
    # if images were skipped during labelling plugin, their annotations is nan:
    image_annotations = json.loads(image_annotations) if isinstance(image_annotations, str) else []
    for annotation in image_annotations:
        deephub_image_annotations.append(
            {"bbox": [annotation.get("left"), annotation.get("top"), annotation.get("width"), annotation.get("height")],
             "area": annotation.get("height") * annotation.get("width"),
             "iscrowd": False,
             "category": annotation.get("label")
             })
    image_annotations = json.dumps(deephub_image_annotations)
    return image_annotations


if __name__ == '__main__':
    input_dataset = dataiku.Dataset(get_input_names_for_role("input_dataset")[0])

    # copy all the columns from input dataset (only target one will be changed)
    output_df = input_dataset.get_dataframe()

    target_column = get_recipe_config()["target_column"]
    if target_column not in output_df.columns:
        raise Exception("Column {} not in input_df with columns [{}]".format(target_column, list(output_df.columns)))

    logging.info("Annotations target column chosen: {}".format(target_column))

    output_df[target_column] = output_df[target_column].map(format_labeling_plugin_annotations)

    output_dataset = dataiku.Dataset(get_output_names_for_role("output_dataset")[0])
    output_dataset.write_with_schema(output_df)
