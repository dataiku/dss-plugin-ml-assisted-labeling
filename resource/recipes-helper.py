import os
import glob

import pandas as pd
import numpy as np
import tensorflow as tf
from PIL import Image
import dataiku


def prettify_error(s):
    """Adds a blank and replaces regular spaces by non-breaking in the first 90 characters
    
    This function adds a big blank space and forces the first words to be a big block of
    unbreakable words. This enforces a newline in the DSS display and makes the error prettier.
    """
    return '\xa0' * 130 + ' \n' + s[:90].replace(' ', '\xa0') + s[90:]


try:
    dataiku.use_plugin_libs('object-detection-cpu')
except:
    try:
        dataiku.use_plugin_libs('object-detection')
    except:
        raise ImportError(prettify_error(
            'ML assisted labeling object detection relies on the DSS object detection '
            'plugin. The plugin could not be found on this instance. Please install it '
            'to use this recipe. More information: https://www.dataiku.com/product/plugins/object-detection/'
        ))


import dataiku
import gpu_utils
import misc_utils
import constants


def can_use_gpu():
    """Check that system supports gpu."""
    # Check that 'tensorflow-gpu' is installed on the current code-env
    import pkg_resources 
    return "tensorflow-gpu" in [d.key for d in pkg_resources.working_set] 


def get_dataset_info(inputs):
    label_dataset_full_name = get_input_name_from_role(inputs, 'bounding_boxes')
    label_dataset = dataiku.Dataset(label_dataset_full_name)
    
    columns = [c['name'] for c in label_dataset.read_schema()]
    return {
        'columns': columns,
        'can_use_gpu': can_use_gpu()
    }


def has_confidence(inputs):
    label_dataset_full_name = get_input_name_from_role(inputs, 'bbox')
    label_dataset = dataiku.Dataset(label_dataset_full_name)
    
    for c in label_dataset.read_schema():
        name = c['name']
        if name == 'confidence': return True
    return False


def get_input_name_from_role(inputs, role):
    return [inp for inp in inputs if inp["role"] == role][0]['fullName']

 
def do(payload, config, plugin_config, inputs):
    if 'method' not in payload:
        return {}

    client = dataiku.api_client()

    if payload['method'] == 'get-dataset-info':
        response = get_dataset_info(inputs)
        response.update(get_avg_side(inputs))
        return response
    if payload['method'] == 'get-gpu-info':
        return {'can_use_gpu': can_use_gpu()}
    if payload['method'] == 'get-confidence':
        return {'has_confidence': has_confidence(inputs)}
    if payload['method'] == 'get-video-info':
        return {
            'can_use_gpu': can_use_gpu(),
            'columns': get_available_videos(inputs)
        }

    return {}


def get_available_videos(inputs):
    name = get_input_name_from_role(inputs, 'video')
    folder = dataiku.Folder(name)
    
    return [f[1:] for f in folder.list_paths_in_partition()]


def get_avg_side(inputs, n_first=3000):
    """Min side is first quartile, max side is third quartile."""
    image_folder_full_name = get_input_name_from_role(inputs, 'images')
    image_folder = dataiku.Folder(image_folder_full_name)
    folder_path = image_folder.get_path()
    
    paths = image_folder.list_paths_in_partition()[:n_first]
    sides = []
    for path in paths:
        path = os.path.join(folder_path, path[1:])
        with Image.open(path) as img: # PIL does not load the raster data at this point, so it's fast.
            w, h = img.size
        sides.append(w)
        sides.append(h)
    sides = np.array(sides)
    
    return {
        'min_side': int(np.percentile(sides, 25)),
        'max_side': int(np.percentile(sides, 75))
    }
