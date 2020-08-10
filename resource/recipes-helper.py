import os

import dataiku
import numpy as np
from PIL import Image

from lal.utils import prettify_error

try:
    dataiku.use_plugin_libs('object-detection-cpu')
except:
    try:
        dataiku.use_plugin_libs('object-detection-gpu')
    except:
        raise ImportError(prettify_error(
            'ML assisted labeling object detection relies on the DSS object detection '
            'plugin. The plugin could not be found on this instance. Please install it '
            'to use this recipe. More information: https://www.dataiku.com/product/plugins/object-detection/'
        ))


import dataiku

def can_use_gpu(inputs):
    """Check that system supports gpu."""
    # Check that 'tensorflow-gpu' is installed on the current code-env
    import pkg_resources
    has_tf_gpu = "tensorflow-gpu" in [d.key for d in pkg_resources.working_set]
    if not has_tf_gpu:
        return False

    # In the case of classification query sampler, check if the model is keras
    is_keras_model = True
    saved_models = [inp for inp in inputs if inp["type"] == 'SAVED_MODEL' and inp["role"] == 'saved_model']
    if len(saved_models) > 0:
        # We found a saved model, we are in the query sampling case
        model = dataiku.Model(saved_models[0]['fullName'])
        is_keras_model = (model.get_definition().get('contentType') == 'prediction/keras')
        return is_keras_model
    else:
        return any([(inp["type"] == 'MANAGED_FOLDER' and inp["role"] == 'saved_model') for inp in inputs])



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

    if payload['method'] == 'get-dataset-info':
        response = get_dataset_info(inputs)
        response.update(get_avg_side(inputs))
        return response
    if payload['method'] == 'get-gpu-info':
        return {'can_use_gpu': can_use_gpu(inputs)}
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
