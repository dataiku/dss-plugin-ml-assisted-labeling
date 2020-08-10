import os
import json
import logging
import random

import dataiku
from dataiku.customrecipe import *

import pandas as pd
import numpy as np

from keras_retinanet.models.retinanet import *
from keras_retinanet.utils.image import read_image_bgr, preprocess_image, resize_image
from keras_retinanet import backend
from keras_retinanet.layers import FilterDetections
from lal import utils
from cardinal import uncertainty


try:
    dataiku.use_plugin_libs('object-detection-cpu')
except:
    try:
        dataiku.use_plugin_libs('object-detection-gpu')
    except:
        raise ImportError(utils.prettify_error(
            'ML assisted labeling object detection relies on the DSS object detection '
            'plugin. The plugin could not be found on this instance. Please insteall it '
            'to use this recipe. More information: https://www.dataiku.com/product/plugins/object-detection/'
        ))


from retinanet_model import get_model
from gpu_utils import load_gpu_options


# This is a modification of the original filter_detection to have probabilities of
# all classes
def proba_filter_detections(
    boxes,
    classification,
    other                 = [],
    class_specific_filter = True,
    nms                   = True,
    score_threshold       = 0.05,
    max_detections        = 300,
    nms_threshold         = 0.5
):
    """ Filter detections using the boxes and classification values.
    Args
        boxes                 : Tensor of shape (num_boxes, 4) containing the boxes in (x1, y1, x2, y2) format.
        classification        : Tensor of shape (num_boxes, num_classes) containing the classification scores.
        other                 : List of tensors of shape (num_boxes, ...) to filter along with the boxes and classification scores.
        class_specific_filter : Whether to perform filtering per class, or take the best scoring class and filter those.
        nms                   : Flag to enable/disable non maximum suppression.
        score_threshold       : Threshold used to prefilter the boxes with.
        max_detections        : Maximum number of detections to keep.
        nms_threshold         : Threshold for the IoU value to determine when a box should be suppressed.
    Returns
        A list of [boxes, scores, labels, other[0], other[1], ...].
        boxes is shaped (max_detections, 4) and contains the (x1, y1, x2, y2) of the non-suppressed boxes.
        scores is shaped (max_detections, n_classes) and contains the scores of the predicted class.
        labels is shaped (max_detections,) and contains the predicted label.
        other[i] is shaped (max_detections, ...) and contains the filtered other[i] data.
        In case there are less than max_detections detections, the tensors are padded with -1's.
    """
    def _filter_detections(scores, labels):
        # threshold based on score
        indices = backend.where(keras.backend.greater(scores, score_threshold))

        if nms:
            filtered_boxes  = backend.gather_nd(boxes, indices)
            filtered_scores = keras.backend.gather(scores, indices)[:, 0]

            # perform NMS
            nms_indices = backend.non_max_suppression(filtered_boxes, filtered_scores, max_output_size=max_detections, iou_threshold=nms_threshold)

            # filter indices based on NMS
            indices = keras.backend.gather(indices, nms_indices)

        # add indices to list of all indices
        labels = backend.gather_nd(labels, indices)
        indices = keras.backend.stack([indices[:, 0], labels], axis=1)

        return indices

    if class_specific_filter:
        # XXX THIS PATH HAS NOT BEEN TESTED YET
        all_indices = []
        # perform per class filtering
        for c in range(int(classification.shape[1])):
            scores = classification[:, c]
            labels = c * backend.ones((keras.backend.shape(scores)[0],), dtype='int64')
            all_indices.append(_filter_detections(scores, labels))

        # concatenate indices to single tensor
        indices = keras.backend.concatenate(all_indices, axis=0)
    else:
        scores  = keras.backend.max(classification, axis    = 1)
        labels  = keras.backend.argmax(classification, axis = 1)
        indices = _filter_detections(scores, labels)

    # select top k
    cscores             = keras.backend.gather(classification, indices[:, 0])
    scores              = backend.gather_nd(classification, indices)
    labels              = indices[:, 1]
    scores, top_indices = backend.top_k(scores, k=keras.backend.minimum(max_detections, keras.backend.shape(scores)[0]))

    # filter input using the final set of indices
    indices             = keras.backend.gather(indices[:, 0], top_indices)
    boxes               = keras.backend.gather(boxes, indices)
    labels              = keras.backend.gather(labels, top_indices)
    other_              = [keras.backend.gather(o, indices) for o in other]

    # Take predictions of all classes
    scores = keras.backend.gather(cscores, top_indices)
    
    # zero pad the outputs
    pad_size = keras.backend.maximum(0, max_detections - keras.backend.shape(scores)[0])
    boxes    = backend.pad(boxes, [[0, pad_size], [0, 0]], constant_values=-1)
    scores   = backend.pad(scores, [[0, pad_size], [0, 0]], constant_values=-1)
    labels   = backend.pad(labels, [[0, pad_size]], constant_values=-1)
    labels   = keras.backend.cast(labels, 'int32')
    other_   = [backend.pad(o, [[0, pad_size]] + [[0, 0] for _ in range(1, len(o.shape))], constant_values=-1) for o in other_]

    # set shapes, since we know what they are
    boxes.set_shape([max_detections, 4])
    scores.set_shape([max_detections, int(classification.shape[1])])
    labels.set_shape([max_detections])
    for o, s in zip(other_, [list(keras.backend.int_shape(o)) for o in other]):
        o.set_shape([max_detections] + s[1:])

    return [boxes, scores, labels] + other_


class ProbaFilterDetections(FilterDetections):
    """ Keras layer for filtering detections using score threshold and NMS.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def call(self, inputs, **kwargs):
        """ Constructs the NMS graph.
        Args
            inputs : List of [boxes, classification, other[0], other[1], ...] tensors.
        """
        boxes          = inputs[0]
        classification = inputs[1]
        other          = inputs[2:]

        # wrap nms with our parameters
        def _filter_detections(args):
            boxes          = args[0]
            classification = args[1]
            other          = args[2]

            return proba_filter_detections(
                boxes,
                classification,
                other,
                nms                   = self.nms,
                class_specific_filter = self.class_specific_filter,
                score_threshold       = self.score_threshold,
                max_detections        = self.max_detections,
                nms_threshold         = self.nms_threshold,
            )

        # call filter_detections on each batch
        outputs = backend.map_fn(
            _filter_detections,
            elems=[boxes, classification, other],
            dtype=[keras.backend.floatx(), keras.backend.floatx(), 'int32'] + [o.dtype for o in other],
            parallel_iterations=self.parallel_iterations
        )

        return outputs

    def compute_output_shape(self, input_shape):
        """ Computes the output shapes given the input shapes.
        Args
            input_shape : List of input shapes [boxes, classification, other[0], other[1], ...].
        Returns
            List of tuples representing the output shapes:
            [filtered_boxes.shape, filtered_scores.shape, filtered_labels.shape, filtered_other[0].shape, filtered_other[1].shape, ...]
        """

        return [
            (input_shape[0][0], self.max_detections, 4),
            (input_shape[1][0], self.max_detections, input_shape[1][1]),
            (input_shape[1][0], self.max_detections),
        ] + [
            tuple([input_shape[i][0], self.max_detections] + list(input_shape[i][2:])) for i in range(2, len(input_shape))
        ]


def __build_anchors(anchor_parameters, features):
    """ Builds anchors for the shape of the features from FPN.
    Args
        anchor_parameters : Parameteres that determine how anchors are generated.
        features          : The FPN features.
    Returns
        A tensor containing the anchors for the FPN features.
        The shape is:
        ```
        (batch_size, num_anchors, 4)
        ```
    """
    anchors = [
        layers.Anchors(
            size=anchor_parameters.sizes[i],
            stride=anchor_parameters.strides[i],
            ratios=anchor_parameters.ratios,
            scales=anchor_parameters.scales,
            name='anchors_{}'.format(i)
        )(f) for i, f in enumerate(features)
    ]

    return keras.layers.Concatenate(axis=1, name='anchors')(anchors)

    
def proba_retinanet_bbox(
    model                 = None,
    nms                   = True,
    class_specific_filter = False, # XXX DEFAULT HAS BEEN MODIFIED
    name                  = 'retinanet-bbox',
    anchor_params         = None,
    nms_threshold         = 0.5,
    score_threshold       = 0.05,
    max_detections        = 300,
    parallel_iterations   = 32,
    **kwargs
):
    """ Construct a RetinaNet model on top of a backbone and adds convenience functions to output boxes directly.
    This model uses the minimum retinanet model and appends a few layers to compute boxes within the graph.
    These layers include applying the regression values to the anchors and performing NMS.
    Args
        model                 : RetinaNet model to append bbox layers to. If None, it will create a RetinaNet model using **kwargs.
        nms                   : Whether to use non-maximum suppression for the filtering step.
        class_specific_filter : Whether to use class specific filtering or filter for the best scoring class only.
        name                  : Name of the model.
        anchor_params         : Struct containing anchor parameters. If None, default values are used.
        nms_threshold         : Threshold for the IoU value to determine when a box should be suppressed.
        score_threshold       : Threshold used to prefilter the boxes with.
        max_detections        : Maximum number of detections to keep.
        parallel_iterations   : Number of batch items to process in parallel.
        **kwargs              : Additional kwargs to pass to the minimal retinanet model.
    Returns
        A keras.models.Model which takes an image as input and outputs the detections on the image.
        The order is defined as follows:
        ```
        [
            boxes, scores, labels, other[0], other[1], ...
        ]
        ```
    """

    # if no anchor parameters are passed, use default values
    if anchor_params is None:
        anchor_params = AnchorParameters.default

    # create RetinaNet model
    if model is None:
        model = retinanet(num_anchors=anchor_params.num_anchors(), **kwargs)
    else:
        assert_training_model(model)

    # compute the anchors
    features = [model.get_layer(p_name).output for p_name in ['P3', 'P4', 'P5', 'P6', 'P7']]
    anchors  = __build_anchors(anchor_params, features)

    # we expect the anchors, regression and classification values as first output
    regression     = model.outputs[0]
    classification = model.outputs[1]

    # "other" can be any additional output from custom submodels, by default this will be []
    other = model.outputs[2:]

    # apply predicted regression to anchors
    boxes = layers.RegressBoxes(name='boxes')([anchors, regression])
    boxes = layers.ClipBoxes(name='clipped_boxes')([model.inputs[0], boxes])

    # filter detections (apply NMS / score threshold / select top-k)
    detections = ProbaFilterDetections(
        nms                   = nms,
        class_specific_filter = class_specific_filter,
        name                  = 'filtered_detections',
        nms_threshold         = nms_threshold,
        score_threshold       = score_threshold,
        max_detections        = max_detections,
        parallel_iterations   = parallel_iterations
    )([boxes, classification] + other)

    # construct the model
    return keras.models.Model(inputs=model.inputs, outputs=detections, name=name)

    


def get_test_model(weights, num_classes):
    """Returns an inference retinanet model.
    Args:
        weights:     Initial weights.
        num_classes: Number of classes to detect.
        n_gpu:       Number of gpu, if above 1, will set up a multi gpu model.
    Returns:
        The inference model.
    """
    model = get_model(weights, num_classes, freeze=True, n_gpu=1)[0]
    test_model = proba_retinanet_bbox(model=model)
    return test_model


def find_objects(model, paths):
    """Find objects with bach size >= 1.
    To support batch size > 1, this method implements a naive ratio grouping
    where batch of images will be processed together solely if they have a
    identical shape.
    Args:
        model: A retinanet model in inference mode.
        paths: Paths to all images to process. The *maximum* batch size is the
               number of paths.
    Returns:
        Boxes, scores, and labels.
        Their shapes: (b, 300, 4), (b, 300), (b, 300)
        With b the batch size.
    """
    if isinstance(paths, str):
        paths = [paths]

    path_i = 0
    nb_paths = len(paths)
    b_boxes, b_scores, b_labels = [], [], []
    
    while nb_paths != path_i:
        images = []
        scales = []
        previous_shape = None

        for path in paths[path_i:]:
            image = read_image_bgr(path)
            if previous_shape is not None and image.shape != previous_shape:
                break # Cannot make the batch bigger due to ratio difference

            previous_shape = image.shape
            path_i += 1

            image = preprocess_image(image)
            image, scale = resize_image(image)

            images.append(image)
            scales.append(scale)

        images = np.stack(images)
        boxes, scores, labels = model.predict_on_batch(images)
        
        for i, scale in enumerate(scales):
            boxes[i, :, :] /= scale # Taking in account the resizing factor

        b_boxes.append(boxes)
        b_scores.append(scores)
        b_labels.append(labels)

    b_boxes = np.concatenate(b_boxes, axis=0)
    b_scores = np.concatenate(b_scores, axis=0)
    b_labels = np.concatenate(b_labels, axis=0)

    return b_boxes, b_scores, b_labels


logging.basicConfig(level=logging.INFO, format='[ML Assisted labeling] %(levelname)s - %(message)s')


images_folder = dataiku.Folder(get_input_names_for_role('unlabeled_samples')[0])
weights_folder = dataiku.Folder(get_input_names_for_role('saved_model')[0])
queries_ds = dataiku.Dataset(get_output_names_for_role('queries')[0])

weights = os.path.join(weights_folder.get_path(), 'weights.h5')
labels_to_names = json.loads(open(os.path.join(weights_folder.get_path(), 'labels.json')).read())

configs = get_recipe_config()

strategy_mapper = {
    'confidence': uncertainty.confidence_sampling,
    'margin': uncertainty.margin_sampling,
    'entropy': uncertainty.entropy_sampling
}
class NoClassifier():
    def fit(self, X, y=None):
        pass
    def predict(self, X):
        return X
    def predict_proba(self, X):
        return X

scorer = strategy_mapper[configs['strategy']]


gpu_opts = load_gpu_options(configs.get('should_use_gpu', False),
                                        configs.get('list_gpu', ''),
                                        configs.get('gpu_allocation', 0.))

batch_size = int(configs['batch_size'])
confidence = float(configs['confidence'])

model = get_test_model(weights, len(labels_to_names))

df = pd.DataFrame(columns=['path', 'uncertainty'])
df_idx = 0

utils.increment_queries_session(queries_ds.short_name)

paths = images_folder.list_paths_in_partition()
folder_path = images_folder.get_path()
total_paths = len(paths)


def print_percent(i, total):
    logging.info('{}% images computed...'.format(round(100 * i / total, 2)))
    logging.info('\t{}/{}'.format(i, total))


for i in range(0, len(paths), batch_size):
    batch_paths = paths[i:i+batch_size]
    batch_paths = list(map(lambda x: os.path.join(folder_path, x[1:]), batch_paths))

    boxes, scores, labels = find_objects(model, batch_paths)
    for batch_i in range(boxes.shape[0]):
        # For each image of the batch
        cur_path = ["/"+os.path.relpath(os.path.relpath(batch_paths[batch_i], folder_path))]

        if len(boxes[batch_i]) and boxes[batch_i][0][0] >= 0.:
            # We take the box with highest probability
            best_row = scores[batch_i][np.argmax(np.max(scores[batch_i], axis=1))]
            df.loc[df_idx] = cur_path + [scorer(NoClassifier(), [best_row])[1][0]]
        else:
            df.loc[df_idx] = cur_path + [1.]
        df_idx += 1

    if i % 100 == 0:
        print_percent(i, total_paths)

queries_ds.write_with_schema(df)
