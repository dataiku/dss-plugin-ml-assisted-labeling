import json
import logging
from base64 import b64encode

import pandas as pd

from cardinal.criteria import get_halting_values
from lal.classifiers.base_classifier import FolderBasedDataClassifier


class ImageObjectClassifier(FolderBasedDataClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self, folder, queries_df, config):
        """

        :type folder: dataiku.core.managed_folder.Folder
        """
        self.folder = folder
        super(ImageObjectClassifier, self).__init__(queries_df, config)
        if self.queries_df is not None and not queries_df.empty:
            hv, self.halting_thr_low, self.halting_thr_high = get_halting_values(self.queries_df.uncertainty)
            self.halting_values_by_path = {k: v for k, v in zip(self.queries_df.path, hv)}
            self.custom_config = {"halting_thr": sorted([self.halting_thr_low, self.halting_thr_high])}
        else:
            self.halting_values_by_path = None
            self.custom_config = {}

    def validate_config(self, config):
        config = super().validate_config(config)
        if "unlabeled" not in config:
            raise ValueError("Image folder not specified. Go to settings tab.")
        return config

    def get_config(self):
        return self.custom_config

    def get_enriched_item_by_id(self, sid):
        self.logger.info('Reading image from: ' + str(sid))
        with self.folder.get_download_stream(sid) as s:
            data = b64encode(s.read())
        self.logger.info("Read: {0}, {1}".format(len(data), type(data)))
        return {"img": data.decode('utf-8'),
                "halting": self.halting_values_by_path and self.halting_values_by_path[sid]
                }

    def get_initial_df(self):
        return pd.DataFrame(self.folder.list_paths_in_partition(), columns=["path"])

    def serialize_label(self, label):
        return json.dumps(label)

    def deserialize_label(self, label):
        return json.loads(label)

    @property
    def type(self):
        return "image-object"

    @staticmethod
    def format_labels_for_stats(raw_labels_series):
        labels = []
        for v in raw_labels_series.values:
            if pd.notnull(v):
                labels += [a['label'] for a in json.loads(v) if a['label']]
        return pd.Series(labels)

