import json
import logging
from base64 import b64encode

import pandas as pd

from lal.classifiers.base_classifier import FolderBasedDataClassifier


class ImageObjectClassifier(FolderBasedDataClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self, folder, queries_df, config):
        """

        :type folder: dataiku.core.managed_folder.Folder
        """
        self.folder = folder
        super(ImageObjectClassifier, self).__init__(queries_df, config)

    def validate_config(self, config):
        config = super().validate_config(config)
        if "unlabeled" not in config:
            raise ValueError("Image folder not specified. Go to settings tab.")
        return config

    def get_enriched_item_by_id(self, sid):
        self.logger.info('Reading image from: ' + str(sid))
        with self.folder.get_download_stream(sid) as s:
            data = b64encode(s.read())
        self.logger.info("Read: {0}, {1}".format(len(data), type(data)))
        return {"img": data.decode('utf-8')}

    def get_initial_df(self):
        return pd.DataFrame(self.folder.list_paths_in_partition(), columns=["path"])

    def clean_data_to_save(self, lab):
        return {
            'top': lab['top'],
            'left': lab['left'],
            'label': lab['label'],
            'width': lab['width'],
            'height': lab['height']
        }

    def serialize_label(self, label):
        cleaned_labels = [self.clean_data_to_save(lab) for lab in label]
        return json.dumps(cleaned_labels)

    def deserialize_label(self, label):
        return json.loads(label)

    @property
    def type(self):
        return "image-object"

    @property
    def is_dynamic(self):
        return True

    @staticmethod
    def format_labels_for_stats(raw_labels_series):
        labels = []
        for v in raw_labels_series.values:
            if pd.notnull(v):
                labels += [a['label'] for a in json.loads(v) if a['label']]
        return pd.Series(labels)

