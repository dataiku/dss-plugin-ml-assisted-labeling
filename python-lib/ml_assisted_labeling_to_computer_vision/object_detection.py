import json
import logging
from json import JSONDecodeError

logger = logging.getLogger(__name__)


def format_labeling_plugin_annotations(annotations_series):
    """
        Format all images annotations to make them compatible with DSS computer vision.
        (Ignore NAN rows which correspond to images skipped during labeling)
    """
    # Filling missing values (image not annotated) with an empty label
    formatted_annotation_series = annotations_series.fillna(json.dumps([]))
    formatted_annotation_series = formatted_annotation_series.map(format_each_image_annotations)
    return formatted_annotation_series


def format_each_image_annotations(image_annotations):
    """ Format labeling annotations to be compatible with dss object detection (deephub)
        :param image_annotations: json serialized with labeling format:
            '[{"top":118, "left":527,"width":174, "height":94, "label":"fish"}]'
        :return: json serialized with deephub format:
            '[{"bbox": [527, 118, 174, 94], "category":"fish"}]'
    """
    deephub_image_annotations = []
    try:
        image_annotations = json.loads(image_annotations)
    except (JSONDecodeError) as e:
        raise Exception("Image annotations '{}' could not be parsed".format(image_annotations))

    for annotation in image_annotations:
        deephub_image_annotations.append(
            {"bbox": [annotation["left"], annotation["top"], annotation["width"], annotation["height"]],
             "category": annotation["label"]
             })
    return json.dumps(deephub_image_annotations)
