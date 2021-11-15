import json
import logging
import math
from json import JSONDecodeError

logger = logging.getLogger(__name__)


def format_labeling_plugin_annotations(image_annotations):
    """ Format labeling annotations to be compatible with dss object detection (deephub)
        :param image_annotations: json serialized with labeling format:
            '[{"top":118, "left":527,"width":174, "height":94, "label":"fish"}]'
        :return: json serialized with deephub format:
            '[{"bbox": [527, 118, 174, 94], "category":"fish"}]'
    """

    deephub_image_annotations = []
    # if images were skipped during labeling plugin, their annotations is nan:
    try:
        if isinstance(image_annotations, str):
            image_annotations = json.loads(image_annotations)
        elif isinstance(image_annotations, float) and math.isnan(image_annotations):
            logger.warning("Image was not labelled, skipping")
            image_annotations = []
        else:
            raise ValueError()

    except (JSONDecodeError, ValueError) as e:
        raise Exception("Image annotations '{}' could not be parsed".format(image_annotations))

    for annotation in image_annotations:
        deephub_image_annotations.append(
            {"bbox": [annotation["left"], annotation["top"], annotation["width"], annotation["height"]],
             "category": annotation["label"]
             })
    return json.dumps(deephub_image_annotations)
